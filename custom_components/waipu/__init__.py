"""The waipu.tv integration."""
from __future__ import annotations

import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WaipuAuthError, WaipuClient
from .cast_follow import async_setup_cast_follow
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    OBSOLETE_OPTIONS,
    TOKEN_REFRESH_THRESHOLD_SEC,
)
from .coordinator import MISSING_ENTITY_CHECKS, WaipuCoordinator
from .services import async_setup_services, async_unload_services

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.CALENDAR,
    Platform.MEDIA_PLAYER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up waipu.tv from a config entry."""
    session = async_get_clientsession(hass)

    if any(key in entry.options for key in OBSOLETE_OPTIONS):
        hass.config_entries.async_update_entry(
            entry,
            options={
                k: v for k, v in entry.options.items() if k not in OBSOLETE_OPTIONS
            },
        )

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
        # Triggers HA's native reauth flow instead of just returning False,
        # which HA would otherwise interpret as "retry setup later" and
        # keep silently failing forever on genuinely stale credentials.
        raise ConfigEntryAuthFailed(f"Authentication failed during setup: {err}") from err

    coordinator = WaipuCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    if coordinator.data and coordinator.data.subscription and entry.title != coordinator.data.subscription:
        hass.config_entries.async_update_entry(
            entry, title=coordinator.data.subscription
        )

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_services(hass)

    unsub_cast = async_setup_cast_follow(hass, entry, coordinator)
    if unsub_cast:
        entry.async_on_unload(unsub_cast)

    # No config entry update listener: options changes reload via
    # OptionsFlowWithReload, reauth via async_update_reload_and_abort (HA
    # deprecated combining the two in 2026.6, error from 2026.12).
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if not any(
            other.entry_id != entry.entry_id
            for other in hass.config_entries.async_loaded_entries(DOMAIN)
        ):
            await async_unload_services(hass)
        # Repairs issues (see coordinator._check_configured_entities) are
        # keyed by entry_id but not otherwise tied to the entry's
        # lifecycle — clear them so a removed/reconfigured entry doesn't
        # leave a stale warning behind. Harmless if none exist.
        for conf_key, _label in MISSING_ENTITY_CHECKS:
            ir.async_delete_issue(hass, DOMAIN, f"{entry.entry_id}_missing_{conf_key}")
    return unload_ok
