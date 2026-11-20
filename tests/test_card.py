"""The bundled dashboard card is served and loaded with the integration."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.waipu.card import CARD_URL, async_register_card

MANIFEST = Path(__file__).parents[1] / "custom_components" / "waipu" / "manifest.json"


async def test_card_served_and_loaded_with_version(hass):
    hass.config.components.add("frontend")
    http = MagicMock()
    http.async_register_static_paths = AsyncMock()
    hass.http = http
    with patch("custom_components.waipu.card.add_extra_js_url") as add_js:
        await async_register_card(hass)

    (static,) = http.async_register_static_paths.call_args.args[0]
    assert static.url_path == CARD_URL
    assert Path(static.path).is_file()
    version = json.loads(MANIFEST.read_text())["version"]
    # The version in the URL makes browsers load the new card after an update.
    add_js.assert_called_once_with(hass, f"{CARD_URL}?v={version}")


async def test_card_skipped_without_frontend(hass):
    with patch("custom_components.waipu.card.add_extra_js_url") as add_js:
        await async_register_card(hass)
    add_js.assert_not_called()
