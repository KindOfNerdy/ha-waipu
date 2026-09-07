"""Repairs: a configured Apple TV/Android TV entity that no longer
exists should raise a Repairs issue (coordinator._check_configured_entities)
and clear it again once the entity reappears or the pairing is removed."""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

from homeassistant.helpers import issue_registry as ir
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.waipu.api import WaipuClient
from custom_components.waipu.const import CONF_APPLE_TV_ENTITY, CONF_DEVICE_ID, DOMAIN


def _fake_jwt(**claims) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"


VALID_TOKEN = _fake_jwt(exp=9999999999, userHandle="user-1")


async def _fake_login_ok(self, username, password):
    self._access_token = VALID_TOKEN
    self._refresh_token = "refresh-1"


def _issue_id(entry: MockConfigEntry) -> str:
    return f"{entry.entry_id}_missing_{CONF_APPLE_TV_ENTITY}"


def _has_issue(hass, entry: MockConfigEntry) -> bool:
    return ir.async_get(hass).async_get_issue(DOMAIN, _issue_id(entry)) is not None


async def _setup(hass, options):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2", CONF_DEVICE_ID: "d1"},
        options=options,
    )
    entry.add_to_hass(hass)
    with (
        patch.object(WaipuClient, "login", _fake_login_ok),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_missing_entity_creates_issue(hass):
    entry = await _setup(hass, {CONF_APPLE_TV_ENTITY: "media_player.does_not_exist"})
    assert _has_issue(hass, entry)


async def test_existing_entity_creates_no_issue(hass):
    hass.states.async_set("media_player.living_room_apple_tv", "off")
    entry = await _setup(hass, {CONF_APPLE_TV_ENTITY: "media_player.living_room_apple_tv"})
    assert not _has_issue(hass, entry)


async def test_unconfigured_field_creates_no_issue(hass):
    entry = await _setup(hass, {})
    assert not _has_issue(hass, entry)


async def test_issue_clears_once_entity_reappears(hass):
    entry = await _setup(hass, {CONF_APPLE_TV_ENTITY: "media_player.living_room_apple_tv"})
    assert _has_issue(hass, entry)

    hass.states.async_set("media_player.living_room_apple_tv", "off")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    with patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[])):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    assert not _has_issue(hass, entry)


async def test_issue_cleared_on_unload(hass):
    entry = await _setup(hass, {CONF_APPLE_TV_ENTITY: "media_player.does_not_exist"})
    assert _has_issue(hass, entry)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert not _has_issue(hass, entry)
