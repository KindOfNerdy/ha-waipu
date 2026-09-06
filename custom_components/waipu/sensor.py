"""Sensor platform: 'now' and 'next' program per configured station."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Program, Recording, Station
from .const import (
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    CONF_ANDROID_TV_CHANNEL_VIEW,
    CONF_SELECTED_CHANNELS,
    DOMAIN,
)
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = hass.data[DOMAIN][entry.entry_id]
    favorites_view = (
        entry.options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
        == ANDROID_TV_CHANNEL_VIEW_FAVORITES
    )
    selected: list[str] | None = entry.options.get(CONF_SELECTED_CHANNELS)
    known: set[str] = set()

    @callback
    def _include(station: Station) -> bool:
        if not station.usable:
            return False
        if favorites_view:
            # Favorites-view mode: follow waipu's own favorite flag live,
            # ignoring any manually saved channel selection.
            return station.favorite
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

    if coordinator.data and coordinator.data.has_dvr:
        async_add_entities(
            [
                WaipuNewRecordingsSensor(coordinator),
                WaipuAllRecordingsSensor(coordinator),
            ]
        )


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
        attrs: dict[str, Any] = {
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
        # Not in the EPG grid — fetched separately per program id, so this
        # may briefly be missing right after a program changes.
        detail = self.coordinator.program_detail(program.id)
        if detail:
            attrs["description"] = detail.description
            attrs["parental_guidance"] = detail.parental_guidance
            attrs["rerun"] = detail.rerun
        return attrs


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


class WaipuNewRecordingsSensor(WaipuEntity, SensorEntity):
    """Count of unwatched recordings — grouped with the recordings calendar."""

    _attr_icon = "mdi:movie-plus"
    _attr_name = "Neue Aufnahmen"

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_new_recordings"
        # Grouped with the media_player device ("waipu Steuerung"), same as
        # the recordings calendar — this is about managing recordings, not
        # a per-channel sensor.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="waipu Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    def _new_recordings(self) -> list[Recording]:
        if not self.coordinator.data:
            return []
        return [r for r in self.coordinator.data.recordings if r.is_new]

    @property
    def native_value(self) -> int:
        return len(self._new_recordings())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"titles": [r.title for r in self._new_recordings()]}


class WaipuAllRecordingsSensor(WaipuEntity, SensorEntity):
    """Total recording count — grouped with the recordings calendar."""

    _attr_icon = "mdi:movie-roll"
    _attr_name = "Aufnahmen gesamt"

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_all_recordings"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="waipu Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    def _recordings(self) -> list[Recording]:
        if not self.coordinator.data:
            return []
        return list(self.coordinator.data.recordings)

    @property
    def native_value(self) -> int:
        return len(self._recordings())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for r in self._recordings():
            by_status[r.status] = by_status.get(r.status, 0) + 1
        return {"by_status": by_status}
