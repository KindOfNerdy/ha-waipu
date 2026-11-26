"""Follow what waipu plays on the TV itself, via Android's media session.

androidtv_remote only reports which app is in front, never the channel, so
a switch on the TV's own remote or in the waipu app would leave the
media_player on the last channel HA tuned. Android's media session does
say what waipu plays — the title plus state and position, no channel or
id. It is read over ADB through HA's "Android Debug Bridge" integration
(``androidtv.adb_command`` on its media_player), every TV_POLL_INTERVAL
while waipu is in front. ``api.classify_tv_playback`` turns the answer
into a live channel (title matched against the EPG the coordinator already
holds), a recording (matched against the recordings) or a waiputhek video.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .api import (
    TIMESHIFT_MIN,
    LivePlayback,
    TvPlayback,
    classify_tv_playback,
    media_session_command,
    parse_media_session,
)
from .const import (
    ANDROID_WAIPU_PACKAGE_ID,
    CONF_ADB_ENTITY,
    CONF_ANDROID_TV_REMOTE,
    TV_POLL_INTERVAL,
)
from .coordinator import WaipuCoordinator

_LOGGER = logging.getLogger(__name__)

ADB_DOMAIN = "androidtv"
ADB_SERVICE = "adb_command"
ADB_RESPONSE_ATTR = "adb_response"
# After HA itself changed the playback (key press, deep link): how long the
# TV gets before it is asked again.
REFRESH_DELAY = timedelta(seconds=2)
# On demand, a position this far off steady playback is a seek.
SEEK_JUMP = timedelta(seconds=5)


def playback_changed(old: TvPlayback | None, new: TvPlayback | None) -> bool:
    """Whether the player has to re-render: anything but steady playback."""
    if old is None or new is None:
        return old is not new
    if (old.title, old.playing, old.is_live) != (new.title, new.playing, new.is_live):
        return True
    if new.is_live is not False or old.position is None or new.position is None:
        return False
    expected = old.position
    if old.playing and old.position_updated_at and new.position_updated_at:
        expected += (new.position_updated_at - old.position_updated_at).total_seconds()
    return abs(new.position - expected) > SEEK_JUMP.total_seconds()


@callback
def async_setup_tv_follow(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WaipuCoordinator,
    is_waipu_shown: Callable[[], bool],
) -> Callable[[], None] | None:
    """Start asking the configured ADB entity; returns the unsubscribe."""
    adb_entity: str | None = entry.options.get(CONF_ADB_ENTITY) or None
    if not adb_entity:
        return None

    # Set when the last title couldn't be placed for sure (EPG may not have
    # the program yet, a new recording may not be listed yet): retried on
    # the next coordinator update — but only if nothing else changed the
    # playback since (playback_generation), or tuning a channel / playing a
    # recording from HA (which fire coordinator updates themselves) would
    # be reverted to what the TV showed a second earlier.
    retry_generation: list[int | None] = [None]
    polling = [False]
    cancel_refresh: list[Callable[[], None] | None] = [None]

    @callback
    def _apply(tv: TvPlayback) -> bool:
        """Place the reported title; True if the shown playback changed."""
        retry_generation[0] = None
        if not coordinator.data:
            return False
        result = classify_tv_playback(
            coordinator.data.stations,
            coordinator.data.recordings,
            tv,
            preferred=(coordinator.selected_station_id, *coordinator.recent_station_ids),
        )
        changed = False
        if isinstance(result, LivePlayback):
            if (
                result.station_id != coordinator.selected_station_id
                or coordinator.on_demand is not None
                or result.timeshift != coordinator.timeshift
            ):
                # Also None: the title airs on several channels and none
                # of them was watched before — better no channel than the
                # one tuned earlier, which it certainly isn't.
                _LOGGER.debug("TV reports %r live on %s", tv.title, result.station_id)
                coordinator.selected_station_id = result.station_id
                coordinator.timeshift = result.timeshift
                changed = True
        elif result is not None and result != coordinator.on_demand:
            _LOGGER.debug("TV reports %r as %s", tv.title, result.kind)
            coordinator.set_on_demand(result)
            changed = True
        if (
            result is None
            or getattr(result, "tentative", False)
            or (isinstance(result, LivePlayback) and result.station_id is None)
        ):
            retry_generation[0] = coordinator.playback_generation
        return changed

    def _timeshift_changed(tv: TvPlayback) -> bool:
        if not tv.is_live:
            return False
        now = dt_util.utcnow()
        watched = tv.watched_time(now)
        if watched is None:
            return False
        lag = now - watched
        if lag < TIMESHIFT_MIN:
            return coordinator.timeshift != timedelta(0)
        return abs(lag - coordinator.timeshift) >= TIMESHIFT_MIN

    async def _ask_tv() -> TvPlayback | None:
        try:
            await hass.services.async_call(
                ADB_DOMAIN,
                ADB_SERVICE,
                {
                    "entity_id": adb_entity,
                    "command": media_session_command(ANDROID_WAIPU_PACKAGE_ID),
                },
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.debug("Asking %s what waipu plays failed: %s", adb_entity, err)
            return None
        state = hass.states.get(adb_entity)
        response = state.attributes.get(ADB_RESPONSE_ATTR) if state else None
        return parse_media_session(
            response if isinstance(response, str) else None,
            ANDROID_WAIPU_PACKAGE_ID,
            dt_util.utcnow(),
        )

    async def _poll(_now: datetime | None = None) -> None:
        if polling[0]:
            return
        polling[0] = True
        try:
            new = await _ask_tv() if is_waipu_shown() else None
        finally:
            polling[0] = False
        old = coordinator.tv_playback
        coordinator.tv_playback = new
        changed = playback_changed(old, new)
        # Only a new title, a jump between live and on demand, or — live —
        # a changed lag behind live (restart/seek/pause within the same
        # program) is placed again: an unchanged title must not revert a
        # channel HA tuned a moment ago, before the TV followed.
        if new is not None and (
            old is None
            or new.title != old.title
            or new.is_live != old.is_live
            or _timeshift_changed(new)
        ):
            changed = _apply(new) or changed
        if changed:
            coordinator.async_update_listeners()

    @callback
    def _refresh_soon() -> None:
        if cancel_refresh[0]:
            cancel_refresh[0]()

        async def _later(_now: datetime) -> None:
            cancel_refresh[0] = None
            await _poll()

        cancel_refresh[0] = async_call_later(hass, REFRESH_DELAY, _later)

    @callback
    def _handle_remote_change(event: Event[EventStateChangedData]) -> None:
        # The app in front changed, or the TV went on/off: don't wait for
        # the next tick.
        hass.async_create_task(_poll())

    @callback
    def _handle_coordinator_update() -> None:
        tv = coordinator.tv_playback
        if (
            tv is not None
            and retry_generation[0] is not None
            and retry_generation[0] == coordinator.playback_generation
            and _apply(tv)
        ):
            coordinator.async_update_listeners()

    unsubs: list[Callable[[], None]] = [
        async_track_time_interval(hass, _poll, TV_POLL_INTERVAL),
        coordinator.async_add_listener(_handle_coordinator_update),
    ]
    remote: str | None = entry.options.get(CONF_ANDROID_TV_REMOTE) or None
    if remote:
        unsubs.append(async_track_state_change_event(hass, [remote], _handle_remote_change))
    coordinator.tv_refresh = _refresh_soon
    hass.async_create_task(_poll())

    @callback
    def _unsubscribe() -> None:
        coordinator.tv_refresh = None
        coordinator.tv_playback = None
        if cancel_refresh[0]:
            cancel_refresh[0]()
        for unsub in unsubs:
            unsub()

    return _unsubscribe
