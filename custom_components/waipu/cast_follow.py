"""Follow channel switches made on the TV itself, via its Google Cast entity.

androidtv_remote only reports which app is in front, never the channel, so
a switch on the TV's own remote or in the waipu app used to leave the
media_player/select on the last channel HA tuned. The TV's Cast entity
(HA's ``cast`` integration) does report what waipu plays — but only the
program title, no channel. The channel is found by matching that title
against the EPG the coordinator already holds (see
``api.match_station_by_title``).
"""
from __future__ import annotations

import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event

from .api import match_station_by_title
from .const import CAST_WAIPU_APP_IDS, CAST_WAIPU_APP_NAME_MARKER, CONF_CAST_ENTITY
from .coordinator import WaipuCoordinator

_LOGGER = logging.getLogger(__name__)


def waipu_cast_title(state: State | None) -> str | None:
    """The program title if `state` is the Cast entity playing waipu, else None."""
    if state is None:
        return None
    attrs = state.attributes
    app_name = str(attrs.get("app_name") or "")
    is_waipu = (
        CAST_WAIPU_APP_NAME_MARKER in app_name.casefold()
        or attrs.get("app_id") in CAST_WAIPU_APP_IDS
    )
    if not is_waipu:
        return None
    title = attrs.get("media_title")
    return str(title) if title else None


@callback
def async_setup_cast_follow(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: WaipuCoordinator
) -> Callable[[], None] | None:
    """Start following the configured Cast entity; returns the unsubscribe."""
    cast_entity: str | None = entry.options.get(CONF_CAST_ENTITY) or None
    if not cast_entity:
        return None

    # A title no channel matched yet: the EPG may not have that program
    # until the next poll. Retried on coordinator updates — only this one,
    # never a title that already matched, or tuning a channel from HA
    # (which itself fires a coordinator update) would be reverted to the
    # channel the TV showed a second earlier.
    pending: list[str | None] = [None]

    @callback
    def _apply(title: str | None) -> None:
        pending[0] = None
        if not title or not coordinator.data:
            return
        station_id = match_station_by_title(
            coordinator.data.stations,
            title,
            preferred=coordinator.selected_station_id,
        )
        if station_id is None:
            pending[0] = title
            return
        if station_id != coordinator.selected_station_id:
            _LOGGER.debug("Cast reports %r, following to %s", title, station_id)
            coordinator.selected_station_id = station_id
            coordinator.async_update_listeners()

    @callback
    def _handle_cast_change(event: Event[EventStateChangedData]) -> None:
        new_title = waipu_cast_title(event.data["new_state"])
        if new_title == waipu_cast_title(event.data["old_state"]):
            return
        _apply(new_title)

    @callback
    def _handle_coordinator_update() -> None:
        if pending[0]:
            _apply(pending[0])

    unsub_state = async_track_state_change_event(hass, [cast_entity], _handle_cast_change)
    unsub_coordinator = coordinator.async_add_listener(_handle_coordinator_update)
    _apply(waipu_cast_title(hass.states.get(cast_entity)))

    @callback
    def _unsubscribe() -> None:
        unsub_state()
        unsub_coordinator()

    return _unsubscribe
