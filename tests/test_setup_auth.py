"""Regression coverage for the reauth-on-auth-failure fix: a genuine
WaipuAuthError (bad/expired password, not a transient network blip) must
raise ConfigEntryAuthFailed — from both initial setup and later
coordinator polls — so Home Assistant triggers its native reauth flow
instead of silently retrying forever or leaving entities unavailable.
"""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.waipu.api import WaipuAuthError, WaipuClient
from custom_components.waipu.const import CONF_DEVICE_ID, CONF_EPG_CACHE_TTL, DOMAIN


def _fake_jwt(**claims) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"


VALID_TOKEN = _fake_jwt(
    exp=9999999999,
    userHandle="user-1",
    userAssets={"account": {"subscription": "Perfect Plus"}},
)


def _entry(hass) -> MockConfigEntry:
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
    return entry


async def _reauth_flow_active(hass, entry) -> bool:
    return any(
        f["context"].get("source") == SOURCE_REAUTH and f["context"].get("entry_id") == entry.entry_id
        for f in hass.config_entries.flow.async_progress()
    )


async def test_setup_with_bad_credentials_triggers_reauth(hass):
    entry = _entry(hass)

    with patch.object(WaipuClient, "login", AsyncMock(side_effect=WaipuAuthError("bad credentials"))):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert result is False
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert await _reauth_flow_active(hass, entry)


async def test_setup_success_does_not_trigger_reauth(hass):
    entry = _entry(hass)

    async def fake_login(self, username, password):
        self._access_token = VALID_TOKEN
        self._refresh_token = "refresh-1"

    with (
        patch.object(WaipuClient, "login", fake_login),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert result is True
    assert entry.state is ConfigEntryState.LOADED
    assert not await _reauth_flow_active(hass, entry)


async def test_coordinator_poll_auth_failure_triggers_reauth(hass):
    """The bug this whole feature fixed: an auth failure discovered *after*
    a successful initial setup (e.g. the refresh token finally expiring)
    used to just raise UpdateFailed, leaving entities unavailable with no
    path back — never triggering reauth."""
    entry = _entry(hass)

    async def fake_login(self, username, password):
        self._access_token = VALID_TOKEN
        self._refresh_token = "refresh-1"

    with (
        patch.object(WaipuClient, "login", fake_login),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert result is True
    assert not await _reauth_flow_active(hass, entry)

    coordinator = entry.runtime_data
    with patch.object(WaipuClient, "get_stations", AsyncMock(side_effect=WaipuAuthError("token revoked"))):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    assert coordinator.last_update_success is False
    assert await _reauth_flow_active(hass, entry)


async def _setup_loaded(hass) -> MockConfigEntry:
    entry = _entry(hass)

    async def fake_login(self, username, password):
        self._access_token = VALID_TOKEN
        self._refresh_token = "refresh-1"

    with (
        patch.object(WaipuClient, "login", fake_login),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    return entry


async def test_reauth_on_loaded_entry_reloads_without_listener_warning(hass, caplog):
    """HA 2026.6 deprecated combining a config entry update listener with
    async_update_reload_and_abort (error from 2026.12) — reauth on a loaded
    entry (token revoked mid-run) must reload cleanly without that warning."""
    entry = await _setup_loaded(hass)

    async def fake_login(self, username, password):
        self._access_token = VALID_TOKEN
        self._refresh_token = "refresh-2"

    with (
        patch.object(WaipuClient, "login", fake_login),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
    ):
        result = await entry.start_reauth_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-pw"}
        )
        await hass.async_block_till_done()

    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-pw"
    assert entry.state is ConfigEntryState.LOADED
    assert "has an update listener" not in caplog.text


async def test_options_change_reloads_entry(hass):
    entry = await _setup_loaded(hass)

    async def fake_login(self, username, password):
        self._access_token = VALID_TOKEN
        self._refresh_token = "refresh-1"

    with (
        patch.object(WaipuClient, "login", fake_login),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
        patch.object(
            hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload
        ) as reload,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_EPG_CACHE_TTL: 30}
        )
        await hass.async_block_till_done()

    assert entry.options[CONF_EPG_CACHE_TTL] == 30
    reload.assert_called_once_with(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
