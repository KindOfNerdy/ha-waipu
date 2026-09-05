"""Select platform: pick a waipu channel directly.

A plain channel dropdown, separate from media_player.waipu_tv_wiedergabe —
useful for a dashboard where the TV's own native media_player (Apple TV /
Android TV) already handles turn on/off, volume, and other apps like
Netflix, and you just want a lightweight way to jump to a waipu channel
alongside it.
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity
from .media_player import async_launch_waipu, visible_stations


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WaipuChannelSelect(coordinator, entry)])


class WaipuChannelSelect(WaipuEntity, SelectEntity):
    _attr_name = "Sender wählen"
    _attr_icon = "mdi:television-classic"

    def __init__(self, coordinator: WaipuCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.entry.entry_id}_channel_select"
        self._current: str | None = None
        # Grouped with the media_player device, not the shared per-channel
        # device — same "Steuerung" box as media_player + shortcut buttons.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    @property
    def options(self) -> list[str]:
        return [s.display_name for s in visible_stations(self._entry, self.coordinator)]

    @property
    def current_option(self) -> str | None:
        return self._current

    async def async_select_option(self, option: str) -> None:
        st = next(
            (
                s
                for s in visible_stations(self._entry, self.coordinator)
                if s.display_name == option
            ),
            None,
        )
        if not st:
            raise HomeAssistantError(f"Unknown station: {option}")
        await async_launch_waipu(self.hass, self._entry, self.coordinator, st.id)
        self._current = option
        self.async_write_ha_state()
