"""Shared base classes for waipu.tv entities."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Station
from .const import DOMAIN
from .coordinator import WaipuCoordinator


class WaipuEntity(CoordinatorEntity[WaipuCoordinator]):
    """Common base — every entity shares one device per config entry."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        # Subscription plan now lives on the config entry title instead
        # (set once known, in __init__.py) — showing it here too was
        # redundant.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            translation_key="channels",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )


class WaipuProgramEntity(WaipuEntity):
    """An entity showing one station's running program.

    Besides refreshing on the normal coordinator poll (every
    DEFAULT_SCAN_INTERVAL), this schedules a one-shot state write for the
    exact moment the *currently known* program ends (or, if none is airing,
    when the next one starts) — so the shown program flips over right on
    time instead of up to 5 minutes late. Purely a display-timing
    improvement: it fetches nothing, it re-evaluates current_program()/
    next_program() against the data already in hand. A schedule
    *correction* still only arrives with the next coordinator poll (or
    cached EPG refetch, see CONF_EPG_CACHE_TTL).

    Subclasses say which station they show via `_boundary_station`.
    """

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        self._boundary_unsub: Callable[[], None] | None = None

    def _boundary_station(self) -> Station | None:
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._schedule_boundary_update()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_boundary_update()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        # Also runs on coordinator.async_update_listeners(), i.e. whenever
        # the tuned channel changes — the timer follows the new station.
        self._schedule_boundary_update()
        super()._handle_coordinator_update()

    def _cancel_boundary_update(self) -> None:
        if self._boundary_unsub:
            self._boundary_unsub()
            self._boundary_unsub = None

    def _schedule_boundary_update(self) -> None:
        """(Re-)arm a timer for the next known now/next transition."""
        self._cancel_boundary_update()
        st = self._boundary_station()
        if not st:
            return
        now = datetime.now(timezone.utc)
        current = st.current_program(now)
        boundary = current.stop_time if current else None
        if boundary is None:
            nxt = st.next_program(now)
            boundary = nxt.start_time if nxt else None
        if boundary is None or boundary <= now:
            return
        self._boundary_unsub = async_track_point_in_utc_time(
            self.hass, self._handle_boundary_reached, boundary
        )

    @callback
    def _handle_boundary_reached(self, _now: datetime) -> None:
        self._boundary_unsub = None
        self._schedule_boundary_update()
        self.async_write_ha_state()
