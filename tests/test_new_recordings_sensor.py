"""The "new recordings" counter: waipu flags SCHEDULED recordings as isNew
too — only recordings you can already watch (finished or currently
recording) may count."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import entity_registry as er

from custom_components.waipu.api import Recording, WaipuClient
from custom_components.waipu.const import CONF_DEVICE_ID, DOMAIN
from .ha_common import MockConfigEntry


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
    self._refresh_token = "refresh-1"


def _rec(rec_id: str, status: str, is_new: bool) -> Recording:
    return Recording(
        id=rec_id,
        program_id=None,
        station_id="ard",
        station_display="ARD",
        title=f"Show {rec_id}",
        status=status,
        recording_start_time=datetime(2026, 10, 30, 19, 10, tzinfo=timezone.utc),
        duration_seconds=3600,
        is_new=is_new,
    )


async def test_new_recordings_ignores_scheduled_and_failed(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2", CONF_DEVICE_ID: "d1"},
    )
    entry.add_to_hass(hass)
    recordings = [
        _rec("scheduled", "SCHEDULED", True),
        _rec("recording", "RECORDING", True),
        _rec("finished", "FINISHED", True),
        _rec("failed", "FAILED", True),
        _rec("seen", "FINISHED", False),
    ]
    with (
        patch.object(WaipuClient, "login", _fake_login_ok),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=recordings)),
        patch.object(WaipuClient, "get_program_details", AsyncMock(return_value={})),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    new_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_new_recordings")
    all_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_all_recordings")

    new_state = hass.states.get(new_id)
    assert new_state.state == "2"
    assert {r["recording_id"] for r in new_state.attributes["recordings"]} == {"recording", "finished"}
    # The total keeps counting everything, scheduled included.
    assert hass.states.get(all_id).state == "5"
