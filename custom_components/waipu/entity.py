"""Shared base classes for waipu.tv entities."""
from __future__ import annotations

from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WaipuCoordinator


class WaipuEntity(CoordinatorEntity[WaipuCoordinator]):
    """Common base — every entity shares one device per config entry."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        username = coordinator.entry.data.get(CONF_USERNAME, "")
        subscription = (
            coordinator.data.subscription if coordinator.data else "waipu.tv"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=f"waipu.tv ({username})" if username else "waipu.tv",
            manufacturer="Exaring AG",
            model=subscription or "waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )
