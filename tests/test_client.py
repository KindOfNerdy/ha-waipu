"""Every sign-in shows up in the waipu account under its User-Agent."""
from __future__ import annotations

import json
from pathlib import Path

from custom_components.waipu.client import async_create_client

MANIFEST = Path(__file__).parents[1] / "custom_components" / "waipu" / "manifest.json"


async def test_client_names_itself_readably(hass):
    client = await async_create_client(hass, device_id="d1")
    version = json.loads(MANIFEST.read_text())["version"]
    assert client._user_agent == f"Home Assistant (ha-waipu {version})"
