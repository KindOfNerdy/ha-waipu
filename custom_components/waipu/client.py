"""The one place a WaipuClient is made — for setup, reauth and runtime."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration

from .api import WaipuClient
from .const import DOMAIN


async def async_create_client(hass: HomeAssistant, **kwargs: Any) -> WaipuClient:
    """A client with HA's shared session and a readable User-Agent.

    waipu lists every sign-in as a device in the account (5 at most), named
    after the User-Agent — so it should say what it is.
    """
    integration = await async_get_integration(hass, DOMAIN)
    return WaipuClient(
        async_get_clientsession(hass),
        user_agent=f"Home Assistant (ha-waipu {integration.version})",
        **kwargs,
    )
