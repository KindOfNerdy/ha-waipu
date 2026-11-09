"""Follow what waipu plays on the TV itself, via its Google Cast entity.

androidtv_remote only reports which app is in front, never the channel, so
a switch on the TV's own remote or in the waipu app used to leave the
media_player/select on the last channel HA tuned. The TV's Cast entity
(HA's ``cast`` integration) does report what waipu plays — but only the
title plus position/duration, no channel or id. ``api.classify_cast_playback``
turns that into a live channel (title matched against the EPG the
coordinator already holds), a recording (matched against the recordings)
or a waiputhek video.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .api import CastPlayback, LivePlayback, classify_cast_playback
from .const import CAST_WAIPU_APP_IDS, CAST_WAIPU_APP_NAME_MARKER, CONF_CAST_ENTITY
from .coordinator import WaipuCoordinator

_LOGGER = logging.getLogger(__name__)


def waipu_cast_playback(state: State | None) -> CastPlayback | None:
    """What waipu plays per `state`, or None if it isn't waipu (or nothing)."""
    if state is None:
        return None
    attrs = state.attributes
    app_name = str(attrs.get("app_name") or "")
    is_waipu = (
        CAST_WAIPU_APP_NAME_MARKER in app_name.casefold()
        or attrs.get("app_id") in CAST_WAIPU_APP_IDS
    )
    title = attrs.get("media_title")
    if not is_waipu or not title:
        return None
    updated_at = attrs.get("media_position_updated_at")
    if isinstance(updated_at, str):
        updated_at = dt_util.parse_datetime(updated_at)
    return CastPlayback(
        title=str(title),
        position=_as_float(attrs.get("media_position")),
        duration=_as_float(attrs.get("media_duration")),
        position_updated_at=updated_at if isinstance(updated_at, datetime) else None,
        playing=state.state == "playing",
        image=attrs.get("entity_picture"),
    )


def _as_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


@callback
def async_setup_cast_follow(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: WaipuCoordinator
) -> Callable[[], None] | None:
    """Start following the configured Cast entity; returns the unsubscribe."""
    cast_entity: str | None = entry.options.get(CONF_CAST_ENTITY) or None
    if not cast_entity:
        return None

    # Set when the last title couldn't be placed for sure (EPG may not have
    # the program yet, a new recording may not be listed yet): retried on
    # the next coordinator update — but only if nothing else changed the
    # playback since (playback_generation), or tuning a channel / playing a
    # recording from HA (which fire coordinator updates themselves) would
    # be reverted to what the TV showed a second earlier.
    retry_generation: list[int | None] = [None]

    @callback
    def _apply() -> None:
        retry_generation[0] = None
        cast = waipu_cast_playback(hass.states.get(cast_entity))
        if cast is None or not coordinator.data:
            return
        result = classify_cast_playback(
            coordinator.data.stations,
            coordinator.data.recordings,
            cast,
            preferred=coordinator.selected_station_id,
        )
        if isinstance(result, LivePlayback):
            if (
                result.station_id != coordinator.selected_station_id
                or coordinator.on_demand is not None
                or result.timeshift != coordinator.timeshift
            ):
                _LOGGER.debug("Cast reports %r live on %s", cast.title, result.station_id)
                coordinator.selected_station_id = result.station_id
                coordinator.timeshift = result.timeshift
                coordinator.async_update_listeners()
        elif result is not None:
            if result != coordinator.on_demand:
                _LOGGER.debug("Cast reports %r as %s", cast.title, result.kind)
                coordinator.set_on_demand(result)
                coordinator.async_update_listeners()
        if result is None or getattr(result, "tentative", False):
            retry_generation[0] = coordinator.playback_generation

    @callback
    def _handle_cast_change(event: Event[EventStateChangedData]) -> None:
        new = waipu_cast_playback(event.data["new_state"])
        old = waipu_cast_playback(event.data["old_state"])
        # Only a new title or a jump between live and on demand matters —
        # position updates (pause, seek) would otherwise re-evaluate often.
        if new is None or (
            old is not None and new.title == old.title and new.is_live == old.is_live
        ):
            return
        _apply()

    @callback
    def _handle_coordinator_update() -> None:
        if (
            retry_generation[0] is not None
            and retry_generation[0] == coordinator.playback_generation
        ):
            _apply()

    unsub_state = async_track_state_change_event(hass, [cast_entity], _handle_cast_change)
    unsub_coordinator = coordinator.async_add_listener(_handle_coordinator_update)
    _apply()

    @callback
    def _unsubscribe() -> None:
        unsub_state()
        unsub_coordinator()

    return _unsubscribe
