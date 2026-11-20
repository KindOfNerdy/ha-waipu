"""Button platform: one-click record-the-current-program per station."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Station, WaipuApiError, WaipuPermissionError
from .const import (
    CHANNEL_SOURCE_FAVORITES,
    CONF_CHANNEL_SOURCE,
    CONF_ANDROID_TV_REMOTE,
    CONF_SELECTED_CHANNELS,
)
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity, waipu_device
from .media_player import (
    SOURCE_EPG,
    SOURCE_LIVE,
    SOURCE_MEDIATHEK,
    SOURCE_RECORDINGS,
    async_open_section,
)

# Shortcut buttons: (slug for unique_id/translation, app section, icon).
SHORTCUTS = (
    ("tv", SOURCE_LIVE, "mdi:television-classic"),
    ("epg", SOURCE_EPG, "mdi:calendar-text"),
    ("recordings", SOURCE_RECORDINGS, "mdi:movie-open-outline"),
    ("mediathek", SOURCE_MEDIATHEK, "mdi:filmstrip-box-multiple"),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = entry.runtime_data
    favorites_view = (
        entry.options.get(CONF_CHANNEL_SOURCE)
        == CHANNEL_SOURCE_FAVORITES
    )
    selected: list[str] | None = entry.options.get(CONF_SELECTED_CHANNELS)
    known: set[str] = set()

    @callback
    def _include(station: Station) -> bool:
        if not station.usable or station.recording_forbidden:
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

    if entry.options.get(CONF_ANDROID_TV_REMOTE):
        async_add_entities(
            WaipuAndroidTvShortcutButton(coordinator, entry, slug, section, icon)
            for slug, section, icon in SHORTCUTS
        )


class WaipuAndroidTvShortcutButton(WaipuEntity, ButtonEntity):
    """Jump straight to a waipu app section on Android TV.

    Live TV, the TV guide (on the tuned channel), recordings and the
    waiputhek — the same sections as the media_player's sources, opened
    the same way (media_player.async_open_section).
    """

    def __init__(
        self,
        coordinator: WaipuCoordinator,
        entry: ConfigEntry,
        slug: str,
        section: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._section = section
        self._attr_unique_id = f"{coordinator.entry.entry_id}_android_{slug}"
        self._attr_translation_key = f"android_tv_{slug}"
        self._attr_icon = icon
        # Grouped with the media_player device (playback/control surface),
        # not the shared per-channel device.
        self._attr_device_info = waipu_device(coordinator, "player")

    @property
    def _target(self) -> str | None:
        return self._entry.options.get(CONF_ANDROID_TV_REMOTE) or None

    @property
    def available(self) -> bool:
        target = self._target
        return bool(target) and self.hass.states.get(target) is not None

    async def async_press(self) -> None:
        await async_open_section(self.hass, self._entry, self.coordinator, self._section)


class WaipuRecordCurrentButton(WaipuEntity, ButtonEntity):
    _attr_icon = "mdi:record-rec"
    # One per channel — off by default; the media_player's browser and
    # waipu.create_recording cover recording too.
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: WaipuCoordinator, station_id: str) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{station_id}_record_current"
        )
        st = coordinator.station(station_id)
        name = st.display_name if st else station_id
        self._attr_translation_key = "record_current"
        self._attr_translation_placeholders = {"station": name}

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
