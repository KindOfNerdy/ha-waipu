"""Button platform: one-click record-the-current-program per station."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Station, WaipuApiError, WaipuPermissionError
from .const import CONF_SELECTED_CHANNELS, DOMAIN
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity

_LOGGER = logging.getLogger(__name__)


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
        if not station.usable or station.recording_forbidden:
            return False
        if selected:
            return station.id in selected
        return station.favorite

    @callback
    def _refresh() -> None:
        if not coordinator.data or not coordinator.data.has_dvr:
            return
        new_entities: list[ButtonEntity] = []
        for station in coordinator.data.stations:
            if station.id in known or not _include(station):
                continue
            known.add(station.id)
            new_entities.append(WaipuRecordCurrentButton(coordinator, station.id))
        if new_entities:
            async_add_entities(new_entities)

    _refresh()
    entry.async_on_unload(coordinator.async_add_listener(_refresh))


class WaipuRecordCurrentButton(WaipuEntity, ButtonEntity):
    _attr_icon = "mdi:record-rec"

    def __init__(self, coordinator: WaipuCoordinator, station_id: str) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{station_id}_record_current"
        )
        st = coordinator.station(station_id)
        name = st.display_name if st else station_id
        self._attr_name = f"{name} – aktuelles Programm aufnehmen"

    @property
    def _station(self) -> Station | None:
        return self.coordinator.station(self._station_id)

    @property
    def available(self) -> bool:
        st = self._station
        return (
            self.coordinator.data is not None
            and self.coordinator.data.has_dvr
            and st is not None
            and st.current_program() is not None
        )

    async def async_press(self) -> None:
        station = self._station
        if not station:
            raise HomeAssistantError("Sender unbekannt")
        program = station.current_program()
        if not program:
            raise HomeAssistantError("Kein laufendes Programm")
        if program.recording_forbidden:
            raise HomeAssistantError(
                "Diese Sendung ist nicht aufnehmbar"
            )
        try:
            await self.coordinator.client.create_recording(program.id, station.id)
        except WaipuPermissionError as err:
            raise HomeAssistantError(
                "Aufnahme nicht erlaubt (Abo prüfen)"
            ) from err
        except WaipuApiError as err:
            raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
        await self.coordinator.async_request_refresh()
