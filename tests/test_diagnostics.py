"""diagnostics.py — must redact credentials/tokens, must not leak station
or recording titles (just counts)."""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.waipu.api import WaipuClient
from custom_components.waipu.const import CONF_DEVICE_ID, DOMAIN
from custom_components.waipu.diagnostics import async_get_config_entry_diagnostics


def _fake_jwt(**claims) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"


VALID_TOKEN = _fake_jwt(
    exp=9999999999,
    userHandle="user-1",
    userAssets={"account": {"subscription": "Perfect Plus"}},
)


async def _fake_login_ok(self, username, password):
    self._access_token = VALID_TOKEN
    self._refresh_token = "refresh-secret"


async def test_diagnostics_redacts_credentials_and_tokens(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "hunter2",
            CONF_DEVICE_ID: "device-1",
        },
    )
    entry.add_to_hass(hass)

    with (
        patch.object(WaipuClient, "login", _fake_login_ok),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    diag = await async_get_config_entry_diagnostics(hass, entry)

    dumped = json.dumps(diag)
    assert "hunter2" not in dumped
    assert "refresh-secret" not in dumped
    assert VALID_TOKEN not in dumped
    assert diag["entry"]["data"][CONF_PASSWORD] == "**REDACTED**"
    # device_id is not a secret — useful for support, left visible.
    assert diag["entry"]["data"][CONF_DEVICE_ID] == "device-1"

    assert diag["data"]["subscription"] == "Perfect Plus"
    assert diag["data"]["station_count"] == 0
    assert diag["coordinator"]["last_update_success"] is True
