"""Sensor platform: 'now' and 'next' program per configured station."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Program, Station
from .const import CONF_SELECTED_CHANNELS, DOMAIN
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = hass.data[DOMAIN][entry.entry_id]
    selected: list[str] | None = entry.options.get(CONF_SELECTED_CHANNELS)
    known: set[str] = set()

    @callback
    def _include(station: Station) -> bool:
        if not station.usable:
            return False
        if selected:
            return station.id in selected
        return station.favorite

    @callback
    def _refresh() -> None:
        if not coordinator.data:
            return
        new_entities: list[SensorEntity] = []
        for station in coordinator.data.stations:
            if station.id in known or not _include(station):
                continue
            known.add(station.id)
            new_entities.append(WaipuNowSensor(coordinator, station.id))
            new_entities.append(WaipuNextSensor(coordinator, station.id))
        if new_entities:
            async_add_entities(new_entities)

    _refresh()
    entry.async_on_unload(coordinator.async_add_listener(_refresh))


class _WaipuProgramSensor(WaipuEntity, SensorEntity):
    _attr_icon = "mdi:television-classic"

    def __init__(self, coordinator: WaipuCoordinator, station_id: str) -> None:
        super().__init__(coordinator)
        self._station_id = station_id

    @property
    def _station(self) -> Station | None:
        return self.coordinator.station(self._station_id)

    def _program(self) -> Program | None:
        raise NotImplementedError

    @property
    def available(self) -> bool:
        return self._station is not None

    @property
    def entity_picture(self) -> str | None:
        program = self._program()
        if program and program.preview_image:
            return program.preview_image
        station = self._station
        return station.logo_url() if station else None

    @property
    def native_value(self) -> str | None:
        program = self._program()
        return program.title if program else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        program = self._program()
        if not program:
            return {}
        return {
            "program_id": program.id,
            "station_id": program.station_id,
            "start_time": program.start_time.isoformat(),
            "stop_time": program.stop_time.isoformat(),
            "duration_minutes": int(program.duration.total_seconds() // 60),
            "episode_title": program.episode_title,
            "genre": program.genre,
            "series_id": program.series_id,
            "recording_forbidden": program.recording_forbidden,
        }


class WaipuNowSensor(_WaipuProgramSensor):
    def __init__(self, coordinator: WaipuCoordinator, station_id: str) -> None:
        super().__init__(coordinator, station_id)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{station_id}_now"
        st = coordinator.station(station_id)
        name = st.display_name if st else station_id
        self._attr_name = f"{name} – jetzt"

    def _program(self) -> Program | None:
        st = self._station
        return st.current_program() if st else None


class WaipuNextSensor(_WaipuProgramSensor):
    def __init__(self, coordinator: WaipuCoordinator, station_id: str) -> None:
        super().__init__(coordinator, station_id)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{station_id}_next"
        st = coordinator.station(station_id)
        name = st.display_name if st else station_id
        self._attr_name = f"{name} – danach"

    def _program(self) -> Program | None:
        st = self._station
        return st.next_program() if st else None
