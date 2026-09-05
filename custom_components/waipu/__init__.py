"""The waipu.tv integration."""
from __future__ import annotations

import logging
import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WaipuAuthError, WaipuClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    TOKEN_REFRESH_THRESHOLD_SEC,
)
from .coordinator import WaipuCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.CALENDAR,
    Platform.MEDIA_PLAYER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up waipu.tv from a config entry."""
    session = async_get_clientsession(hass)

    device_id = entry.data.get(CONF_DEVICE_ID) or str(uuid.uuid4())
    if device_id != entry.data.get(CONF_DEVICE_ID):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_DEVICE_ID: device_id}
        )

    async def _persist_tokens(access: str | None, refresh: str | None) -> None:
        new_data = {
            **entry.data,
            CONF_ACCESS_TOKEN: access,
            CONF_REFRESH_TOKEN: refresh,
        }
        hass.config_entries.async_update_entry(entry, data=new_data)

    client = WaipuClient(
        session,
        device_id=device_id,
        access_token=entry.data.get(CONF_ACCESS_TOKEN),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
        on_token_change=_persist_tokens,
        refresh_threshold_sec=TOKEN_REFRESH_THRESHOLD_SEC,
    )

    # Make sure we can authenticate. We always have access to the password
    # so we can re-issue a password grant if both tokens are gone.
    client.set_credentials(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    try:
        if not client.access_token:
            await client.login(
                entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
            )
        else:
            await client.ensure_token()
    except WaipuAuthError as err:
        _LOGGER.error("Authentication failed during setup: %s", err)
        return False

    coordinator = WaipuCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    if coordinator.data and coordinator.data.subscription and entry.title != coordinator.data.subscription:
        hass.config_entries.async_update_entry(
            entry, title=coordinator.data.subscription
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
