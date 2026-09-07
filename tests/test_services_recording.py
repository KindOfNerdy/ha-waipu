"""create_recording's/stop_recording's "no parameters, use whatever
channel this integration currently has tuned" defaulting — the
zero-lookup workflow for spontaneously recording (and cutting short) a
few minutes of whatever's on."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.waipu.api import Program, Recording, Station, WaipuClient
from custom_components.waipu.const import (
    ATTR_PROGRAM_ID,
    ATTR_RECORDING_ID,
    ATTR_STATION_ID,
    CONF_APPLE_TV_ENTITY,
    CONF_DEVICE_ID,
    DOMAIN,
    SERVICE_CREATE_RECORDING,
    SERVICE_STOP_RECORDING,
)

APPLE_TV = "media_player.living_room_apple_tv"


def _fake_jwt(**claims) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"


VALID_TOKEN = _fake_jwt(
    exp=9999999999,
    userHandle="user-1",
    userAssets={"account": {"subscription": "Perfect Plus"}},  # DVR-qualifying,
    # so coordinator.data.recordings actually gets populated in tests below.
)


async def _fake_login_ok(self, username, password):
    self._access_token = VALID_TOKEN
    self._refresh_token = "refresh-1"


def _ard(programs=(), recordings=None) -> Station:
    return Station(
        id="ard",
        display_name="ARD",
        description=None,
        logo_template_url=None,
        stream_qualities=(),
        recording_forbidden=False,
        favorite=True,
        programs=tuple(programs),
    )


async def _setup(hass, *, options=None, stations=None, recordings=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2", CONF_DEVICE_ID: "d1"},
        options=options or {},
    )
    entry.add_to_hass(hass)
    with (
        patch.object(WaipuClient, "login", _fake_login_ok),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=stations or [])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=recordings or [])),
        # Stations with .favorite=True make the coordinator fetch EPG for
        # them, and any recording with a program_id triggers a program-
        # detail fetch — stub both network calls out.
        patch.object(WaipuClient, "get_programs_in_window", AsyncMock(return_value={})),
        patch.object(WaipuClient, "get_program_details", AsyncMock(return_value={})),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, hass.data[DOMAIN][entry.entry_id]


def _tune_apple_tv(hass, coordinator, station_id: str) -> None:
    """Simulate a channel already selected via this integration, on an
    Apple TV that's reported as on — the precondition
    current_selected_station_id needs to return non-None."""
    hass.states.async_set(APPLE_TV, "playing")
    coordinator.selected_station_id = station_id


# --- create_recording: station_id defaulting --------------------------------


async def test_create_recording_without_station_id_or_selection_fails(hass):
    entry, coordinator = await _setup(hass, stations=[_ard()])
    with pytest.raises(ServiceValidationError, match="Kein station_id"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_RECORDING,
            {ATTR_PROGRAM_ID: "prog-1"},
            blocking=True,
        )


async def test_create_recording_defaults_to_selected_channel(hass):
    entry, coordinator = await _setup(
        hass, options={CONF_APPLE_TV_ENTITY: APPLE_TV}, stations=[_ard()]
    )
    _tune_apple_tv(hass, coordinator, "ard")

    with patch.object(WaipuClient, "create_recording", AsyncMock()) as mock_create:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_RECORDING,
            {ATTR_PROGRAM_ID: "prog-1"},
            blocking=True,
        )
    mock_create.assert_awaited_once_with("prog-1", "ard")


async def test_create_recording_explicit_station_id_overrides_selection(hass):
    entry, coordinator = await _setup(
        hass, options={CONF_APPLE_TV_ENTITY: APPLE_TV}, stations=[_ard()]
    )
    _tune_apple_tv(hass, coordinator, "ard")

    with patch.object(WaipuClient, "create_recording", AsyncMock()) as mock_create:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_RECORDING,
            {ATTR_STATION_ID: "zdf", ATTR_PROGRAM_ID: "prog-2"},
            blocking=True,
        )
    mock_create.assert_awaited_once_with("prog-2", "zdf")


# --- stop_recording -----------------------------------------------------------


async def test_stop_recording_with_explicit_id(hass):
    entry, coordinator = await _setup(hass)
    with patch.object(WaipuClient, "stop_recording", AsyncMock()) as mock_stop:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_RECORDING,
            {ATTR_RECORDING_ID: "rec-1"},
            blocking=True,
        )
    mock_stop.assert_awaited_once_with("rec-1")


async def test_stop_recording_without_id_or_selection_fails(hass):
    entry, coordinator = await _setup(hass)
    with pytest.raises(ServiceValidationError, match="Kein recording_id"):
        await hass.services.async_call(
            DOMAIN, SERVICE_STOP_RECORDING, {}, blocking=True
        )


async def test_stop_recording_resolves_running_recording_on_selected_channel(hass):
    now = datetime.now(timezone.utc)
    running = Recording(
        id="rec-running",
        program_id="prog-1",
        station_id="ard",
        station_display="ARD",
        title="Tagesschau",
        status="RECORDING",
        recording_start_time=now - timedelta(minutes=5),
        duration_seconds=900,
    )
    entry, coordinator = await _setup(
        hass,
        options={CONF_APPLE_TV_ENTITY: APPLE_TV},
        stations=[_ard()],
        recordings=[running],
    )
    _tune_apple_tv(hass, coordinator, "ard")

    with patch.object(WaipuClient, "stop_recording", AsyncMock()) as mock_stop:
        await hass.services.async_call(
            DOMAIN, SERVICE_STOP_RECORDING, {}, blocking=True
        )
    mock_stop.assert_awaited_once_with("rec-running")


async def test_stop_recording_no_running_recording_on_selected_channel_fails(hass):
    entry, coordinator = await _setup(
        hass, options={CONF_APPLE_TV_ENTITY: APPLE_TV}, stations=[_ard()]
    )
    _tune_apple_tv(hass, coordinator, "ard")

    with pytest.raises(ServiceValidationError, match="läuft aktuell keine Aufnahme"):
        await hass.services.async_call(
            DOMAIN, SERVICE_STOP_RECORDING, {}, blocking=True
        )
