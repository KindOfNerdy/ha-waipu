"""Entity/device names come from translations (translation_key): a German
Home Assistant must keep exactly the names the integration always had,
an English one gets English names."""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import entity_registry as er

from custom_components.waipu.api import Station, WaipuClient
from custom_components.waipu.const import CONF_ANDROID_TV_REMOTE, CONF_DEVICE_ID, DOMAIN
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


ARD = Station(
    id="ard",
    display_name="ARD",
    description=None,
    logo_template_url=None,
    stream_qualities=(),
    recording_forbidden=False,
    favorite=True,
    programs=(),
)

EXPECTED = {
    "de": {
        "waipu Senderübersicht ARD – jetzt",
        "waipu Senderübersicht ARD – danach",
        "waipu Senderübersicht ARD – aktuelles Programm aufnehmen",
        "waipu Wiedergabe",
        "waipu Wiedergabe Sender wählen",
        "waipu Wiedergabe TV öffnen (Android TV)",
        "waipu Wiedergabe EPG öffnen (Android TV)",
        "waipu Wiedergabe Aufnahmen öffnen (Android TV)",
        "waipu Aufnahmen",
        "waipu Aufnahmen Neue Aufnahmen",
        "waipu Aufnahmen Aufnahmen gesamt",
    },
    "en": {
        "waipu Channel overview ARD – now",
        "waipu Channel overview ARD – next",
        "waipu Channel overview ARD – record current program",
        "waipu Playback",
        "waipu Playback Select channel",
        "waipu Playback Open TV (Android TV)",
        "waipu Playback Open EPG (Android TV)",
        "waipu Playback Open recordings (Android TV)",
        "waipu Recordings",
        "waipu Recordings New recordings",
        "waipu Recordings Total recordings",
    },
}


@pytest.mark.parametrize("language", ["de", "en"])
async def test_entity_names_follow_language(hass, language):
    hass.config.language = language
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2", CONF_DEVICE_ID: "d1"},
        options={CONF_ANDROID_TV_REMOTE: "remote.living_room_android_tv"},
    )
    entry.add_to_hass(hass)
    with (
        patch.object(WaipuClient, "login", _fake_login_ok),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=[ARD])),
        patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[])),
        patch.object(WaipuClient, "get_programs_in_window", AsyncMock(return_value={})),
        patch.object(WaipuClient, "get_program_details", AsyncMock(return_value={})),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    names = {
        hass.states.get(e.entity_id).attributes["friendly_name"]
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }
    assert names == EXPECTED[language]
