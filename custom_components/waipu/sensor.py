"""Sensor platform: 'now' and 'next' program per configured station."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time

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
    """Base for the 'jetzt'/'danach' sensors.

    Besides refreshing on the normal coordinator poll (every
    DEFAULT_SCAN_INTERVAL), this also schedules a one-shot state write
    for the exact moment the *currently known* program ends (or, if
    none is airing, when the next one starts) — so "jetzt"/"danach"
    flip over right on time instead of up to 5 minutes late. This is
    purely a display-timing improvement: it doesn't fetch anything, it
    just re-evaluates current_program()/next_program() against the data
    already in hand. A schedule *correction* still only arrives with the
    next coordinator poll (or cached EPG refetch, see CONF_EPG_CACHE_TTL).
    """

    _attr_icon = "mdi:television-classic"

    def __init__(self, coordinator: WaipuCoordinator, station_id: str) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._boundary_unsub: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._schedule_boundary_update()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_boundary_update()
        await super().async_will_remove_from_hass()

    def _handle_coordinator_update(self) -> None:
        self._schedule_boundary_update()
        super()._handle_coordinator_update()

    def _cancel_boundary_update(self) -> None:
        if self._boundary_unsub:
            self._boundary_unsub()
            self._boundary_unsub = None

    def _schedule_boundary_update(self) -> None:
        """(Re-)arm a timer for the next known now/next transition."""
        self._cancel_boundary_update()
        st = self._station
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = super().extra_state_attributes
        st = self._station
        if st:
            attrs["upcoming"] = [
                {
                    "program_id": p.id,
                    "title": p.title,
                    "episode_title": p.episode_title,
                    "start_time": p.start_time.isoformat(),
                    "series_id": p.series_id,
                }
                for p in st.upcoming_programs()
            ]
        return attrs


def _recording_list(recordings: list[Recording]) -> list[dict[str, Any]]:
    """Title + recording date + the ids needed to act on an entry, newest
    first — shared by both recording sensors below."""
    ordered = sorted(
        recordings,
        key=lambda r: r.recording_start_time or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return [
        {
            "title": r.title,
            "episode_title": r.episode_title,
            "date": r.recording_start_time.isoformat() if r.recording_start_time else None,
            "status": r.status,  # SCHEDULED | RECORDING | FINISHED | FAILED
            "is_new": r.is_new,
            "fully_watched": r.fully_watched,
            "partially_watched": r.partially_watched,
            "recording_id": r.id,  # for waipu.delete_recording
            "series_id": r.series_id,  # for waipu.delete_serial_recording
        }
        for r in ordered
    ]


class WaipuNewRecordingsSensor(WaipuEntity, SensorEntity):
    """Count of unwatched recordings — grouped with the recordings calendar."""

    _attr_icon = "mdi:movie-plus"
    _attr_name = "Neue Aufnahmen"

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_new_recordings"
        # Own "waipu Aufnahmen" device — recording management is its own
        # concern, separate from "waipu Wiedergabe" (TV playback control)
        # and the per-channel "waipu Senderübersicht" device.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_recordings")},
            name="waipu Aufnahmen",
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
        return {"recordings": _recording_list(self._new_recordings())}


class WaipuAllRecordingsSensor(WaipuEntity, SensorEntity):
    """Total recording count — grouped with the recordings calendar."""

    _attr_icon = "mdi:movie-roll"
    _attr_name = "Aufnahmen gesamt"

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_all_recordings"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_recordings")},
            name="waipu Aufnahmen",
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
        recordings = self._recordings()
        by_status: dict[str, int] = {}
        for r in recordings:
            by_status[r.status] = by_status.get(r.status, 0) + 1
        return {"by_status": by_status, "recordings": _recording_list(recordings)}
