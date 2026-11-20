"""The bundled dashboard card: served by the integration and loaded in the
frontend, so it needs no separate install and always matches this version."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_FILE = "waipu-card.js"
CARD_URL = f"/{DOMAIN}_static/{CARD_FILE}"
CARD_PATH = Path(__file__).parent / "frontend" / CARD_FILE


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card and add it to every dashboard, once per HA run.

    The version in the URL makes browsers fetch the new file after an
    update. Without the frontend (e.g. in tests) there is nothing to do.
    """
    if "frontend" not in hass.config.components or hass.http is None:
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=True)]
    )
    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")
