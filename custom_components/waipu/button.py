"""Button platform: one-click record-the-current-program per station."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Station, WaipuApiError, WaipuPermissionError
from .const import (
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    CONF_ANDROID_TV_CHANNEL_VIEW,
    CONF_ANDROID_TV_REMOTE,
    CONF_SELECTED_CHANNELS,
    CONF_WAIPU_APP_LINK,
    DEFAULT_WAIPU_APP_LINK,
    DOMAIN,
    WAIPU_EPG_LINK,
    WAIPU_RECORDINGS_LINK,
)
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity

_LOGGER = logging.getLogger(__name__)


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
        app_link = entry.options.get(CONF_WAIPU_APP_LINK) or DEFAULT_WAIPU_APP_LINK
        async_add_entities(
            [
                WaipuAndroidTvShortcutButton(
                    coordinator, entry, "tv", "TV öffnen (Android TV)",
                    app_link, "mdi:television-classic",
                ),
                WaipuAndroidTvShortcutButton(
                    coordinator, entry, "epg", "EPG öffnen (Android TV)",
                    WAIPU_EPG_LINK, "mdi:calendar-text",
                ),
                WaipuAndroidTvShortcutButton(
                    coordinator, entry, "recordings", "Aufnahmen öffnen (Android TV)",
                    WAIPU_RECORDINGS_LINK, "mdi:movie-open-outline",
                ),
            ]
        )


class WaipuAndroidTvShortcutButton(WaipuEntity, ButtonEntity):
    """Jump straight to a waipu app section on Android TV.

    Static, non-DVR shortcuts for the app/section-level deep links
    (waipu://tv, waipu://epg, waipu://recordings) — lets a dashboard offer
    quick back-and-forth between sections. Not a per-channel deep link.
    """

    def __init__(
        self,
        coordinator: WaipuCoordinator,
        entry: ConfigEntry,
        slug: str,
        name: str,
        app_link: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._app_link = app_link
        self._attr_unique_id = f"{coordinator.entry.entry_id}_android_{slug}"
        self._attr_name = name
        self._attr_icon = icon
        # Grouped with the media_player device (playback/control surface),
        # not the shared per-channel device.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    @property
    def _target(self) -> str | None:
        return self._entry.options.get(CONF_ANDROID_TV_REMOTE) or None

    @property
    def available(self) -> bool:
        target = self._target
        return bool(target) and self.hass.states.get(target) is not None

    async def async_press(self) -> None:
        target = self._target
        if not target:
            raise HomeAssistantError(
                "Kein Android TV in den Waipu-Optionen konfiguriert"
            )
        await self.hass.services.async_call(
            "remote",
            "turn_on",
            {"entity_id": target, "activity": self._app_link},
            blocking=True,
        )


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
