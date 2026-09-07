"""config_flow.py: login step, the new tv_setup step (v1.4.0), duplicate-
account handling, and reauth."""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.waipu.api import WaipuAuthError, WaipuClient
from custom_components.waipu.const import (
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_APPLE_TV_REMOTE,
    CONF_DEVICE_ID,
    DOMAIN,
)


def _fake_jwt(**claims) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"


VALID_TOKEN = _fake_jwt(exp=9999999999, userHandle="user-1")


async def _fake_login_ok(self, username, password):
    self._access_token = VALID_TOKEN
    self._refresh_token = "refresh-1"


async def _start_user_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_step_shows_form(hass):
    result = await _start_user_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_step_invalid_auth_shows_error(hass):
    result = await _start_user_flow(hass)
    with patch.object(WaipuClient, "login", AsyncMock(side_effect=WaipuAuthError("nope"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "wrong"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_step_success_advances_to_tv_setup(hass):
    result = await _start_user_flow(hass)
    with patch.object(WaipuClient, "login", _fake_login_ok):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "tv_setup"


async def test_duplicate_account_aborts(hass):
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "x", CONF_DEVICE_ID: "d1"},
    ).add_to_hass(hass)

    result = await _start_user_flow(hass)
    with patch.object(WaipuClient, "login", _fake_login_ok):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            # Case-insensitive: the flow lowercases the username for the
            # unique_id, so "USER@EXAMPLE.COM" must still collide.
            {CONF_USERNAME: "USER@EXAMPLE.COM", CONF_PASSWORD: "hunter2"},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_tv_setup_step_skip_creates_entry_without_extra_options(hass):
    result = await _start_user_flow(hass)
    with patch.object(WaipuClient, "login", _fake_login_ok):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2"},
        )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] == "user@example.com"
    assert result["options"] == {}


async def test_tv_setup_step_with_values_populates_options(hass):
    result = await _start_user_flow(hass)
    with patch.object(WaipuClient, "login", _fake_login_ok):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2"},
        )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_APPLE_TV_ENTITY: "media_player.living_room_apple_tv",
            CONF_ANDROID_TV_REMOTE: "remote.living_room_android_tv",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {
        CONF_APPLE_TV_ENTITY: "media_player.living_room_apple_tv",
        CONF_ANDROID_TV_REMOTE: "remote.living_room_android_tv",
    }
    assert CONF_APPLE_TV_REMOTE not in result["options"]  # left empty, dropped


async def test_reauth_updates_password(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "old-pw", CONF_DEVICE_ID: "d1"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch.object(WaipuClient, "login", _fake_login_ok):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-pw"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-pw"
