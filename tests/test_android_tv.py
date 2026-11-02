"""Android TV control via waipu deep links: channel switching (services,
media_player, select), playing recordings, plus the options flow's channel
source step and the cleanup of options deep links made obsolete."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError

from custom_components.waipu.api import Recording, Station, WaipuClient
from custom_components.waipu.const import (
    ATTR_MODE,
    ATTR_POSITION,
    ATTR_RECORDING_ID,
    ATTR_STATION_ID,
    CHANNEL_SOURCE_ALL,
    CHANNEL_SOURCE_FAVORITES,
    CONF_ANDROID_TV_REMOTE,
    CONF_CHANNEL_SOURCE,
    CONF_DEVICE_ID,
    CONF_SELECTED_CHANNELS,
    CONF_TV_PLATFORM,
    DOMAIN,
    SERVICE_LAUNCH_ON_ANDROID_TV,
    SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
    SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
    TV_PLATFORM_ANDROID,
    TV_PLATFORM_NONE,
)
from .ha_common import MockConfigEntry

REMOTE = "remote.living_room_tv"


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


def _station(station_id: str, name: str, favorite: bool = True) -> Station:
    return Station(
        id=station_id,
        display_name=name,
        description=None,
        logo_template_url=None,
        stream_qualities=(),
        recording_forbidden=False,
        favorite=favorite,
        programs=(),
    )


STATIONS = [
    _station("ard", "Das Erste"),
    _station("zdf", "ZDF"),
    _station("swr_bw", "SWR BW"),
    _station("rtl", "RTL", favorite=False),
]


def _recording(rec_id: str, status: str = "FINISHED") -> Recording:
    return Recording(
        id=rec_id,
        program_id=None,
        station_id="ard",
        station_display="Das Erste",
        title="JENKE.",
        status=status,
        recording_start_time=datetime.now(timezone.utc) - timedelta(days=1),
        duration_seconds=3600,
    )


@pytest.fixture
def waipu_api():
    """Stub every network call for the whole test, so options-flow reloads
    (OptionsFlowWithReload) can set the entry up again too."""
    with (
        patch.object(WaipuClient, "login", _fake_login_ok),
        patch.object(WaipuClient, "get_stations", AsyncMock(return_value=STATIONS)),
        patch.object(
            WaipuClient,
            "get_recordings",
            AsyncMock(
                return_value=[
                    _recording("2115976245"),
                    _recording("2105028496", status="SCHEDULED"),
                ]
            ),
        ),
        patch.object(WaipuClient, "get_programs_in_window", AsyncMock(return_value={})),
        patch.object(WaipuClient, "get_program_details", AsyncMock(return_value={})),
    ):
        yield


@pytest.fixture
def remote_calls(hass):
    """Capture remote.turn_on calls (what actually reaches the TV)."""
    calls: list[dict] = []

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("remote", "turn_on", _turn_on)
    hass.states.async_set(REMOTE, "on", {"current_activity": "com.google.android.tvlauncher"})
    return calls


async def _setup(hass, options=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "hunter2", CONF_DEVICE_ID: "d1"},
        options={CONF_ANDROID_TV_REMOTE: REMOTE, **(options or {})},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, entry.runtime_data


def _activities(calls) -> list[str]:
    return [c["activity"] for c in calls]


# --- channel switching ----------------------------------------------------------


async def test_switch_channel_service_uses_deep_link(hass, waipu_api, remote_calls):
    entry, coordinator = await _setup(hass)
    await hass.services.async_call(
        DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "swr_bw"}, blocking=True
    )
    assert _activities(remote_calls) == ["waipu://tv?id=swr_bw"]
    assert coordinator.selected_station_id == "swr_bw"


async def test_switch_channel_service_works_for_non_visible_station(hass, waipu_api, remote_calls):
    # rtl isn't a favorite (so no HA entities), but waipu can still tune to it.
    await _setup(hass)
    await hass.services.async_call(
        DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "rtl"}, blocking=True
    )
    assert _activities(remote_calls) == ["waipu://tv?id=rtl"]


async def test_switch_channel_service_unknown_station(hass, waipu_api, remote_calls):
    await _setup(hass)
    with pytest.raises(ServiceValidationError, match="Sender unbekannt"):
        await hass.services.async_call(
            DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "nope"}, blocking=True
        )
    assert remote_calls == []


async def test_launch_service_with_and_without_station(hass, waipu_api, remote_calls):
    await _setup(hass)
    await hass.services.async_call(DOMAIN, SERVICE_LAUNCH_ON_ANDROID_TV, {}, blocking=True)
    await hass.services.async_call(
        DOMAIN, SERVICE_LAUNCH_ON_ANDROID_TV, {ATTR_STATION_ID: "zdf"}, blocking=True
    )
    assert _activities(remote_calls) == ["waipu://tv", "waipu://tv?id=zdf"]


async def test_media_player_sources_are_app_sections(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    assert hass.states.get(player).attributes["source_list"] == ["Live TV", "Recordings", "EPG"]
    for source in ("Recordings", "EPG", "Live TV"):
        await hass.services.async_call(
            "media_player", "select_source", {"entity_id": player, "source": source}, blocking=True
        )
    assert _activities(remote_calls) == ["waipu://recordings", "waipu://epg", "waipu://tv"]


async def test_media_player_select_source_live_tv_while_waipu_open(hass, waipu_api, remote_calls):
    await _setup(hass)
    hass.states.async_set(REMOTE, "on", {"current_activity": "de.exaring.waipu/.MainActivity"})
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    await hass.services.async_call(
        "media_player", "select_source", {"entity_id": player, "source": "Live TV"}, blocking=True
    )
    assert _activities(remote_calls) == ["waipu://tv"]


async def test_media_player_select_source_channel_name_still_works(hass, waipu_api, remote_calls):
    # Channel names were the sources up to 1.7 — old automations keep working.
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    await hass.services.async_call(
        "media_player", "select_source", {"entity_id": player, "source": "ZDF"}, blocking=True
    )
    assert _activities(remote_calls) == ["waipu://tv?id=zdf"]


async def test_media_player_next_previous_wrap_around(hass, waipu_api, remote_calls):
    entry, coordinator = await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    coordinator.selected_station_id = "swr_bw"  # last favorite
    await hass.services.async_call(
        "media_player", "media_next_track", {"entity_id": player}, blocking=True
    )
    await hass.services.async_call(
        "media_player", "media_previous_track", {"entity_id": player}, blocking=True
    )
    assert _activities(remote_calls) == ["waipu://tv?id=ard", "waipu://tv?id=swr_bw"]


# --- recordings -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({}, "waipu://recordings?recordingId=2115976245&autoplay=true"),
        (
            {ATTR_MODE: "beginning"},
            "waipu://recordings?recordingId=2115976245&autoplay=true&position=0",
        ),
        ({ATTR_MODE: "details"}, "waipu://recordings?recordingId=2115976245"),
        (
            {ATTR_POSITION: 600},
            "waipu://recordings?recordingId=2115976245&autoplay=true&position=600",
        ),
    ],
)
async def test_play_recording_modes(hass, waipu_api, remote_calls, data, expected):
    await _setup(hass)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245", **data},
        blocking=True,
    )
    assert _activities(remote_calls) == [expected]


async def test_play_recording_unknown_id(hass, waipu_api, remote_calls):
    await _setup(hass)
    with pytest.raises(ServiceValidationError, match="Aufnahme unbekannt"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
            {ATTR_RECORDING_ID: "nope"},
            blocking=True,
        )


async def test_play_recording_scheduled_not_playable(hass, waipu_api, remote_calls):
    await _setup(hass)
    with pytest.raises(ServiceValidationError, match="noch nicht abspielbar"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
            {ATTR_RECORDING_ID: "2105028496"},
            blocking=True,
        )
    assert remote_calls == []


# --- options --------------------------------------------------------------------


async def test_obsolete_launch_delay_option_is_dropped(hass, waipu_api, remote_calls):
    entry, _ = await _setup(hass, options={"android_tv_launch_delay": 10})
    assert "android_tv_launch_delay" not in entry.options
    assert entry.options[CONF_ANDROID_TV_REMOTE] == REMOTE


async def _options_init(hass, entry, **fields):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    return await hass.config_entries.options.async_configure(result["flow_id"], fields)


async def test_options_favorites_skips_channel_step_and_keeps_selection(
    hass, waipu_api, remote_calls
):
    entry, _ = await _setup(hass, options={CONF_SELECTED_CHANNELS: ["rtl"]})
    result = await _options_init(
        hass,
        entry,
        **{CONF_TV_PLATFORM: TV_PLATFORM_ANDROID, CONF_CHANNEL_SOURCE: CHANNEL_SOURCE_FAVORITES},
    )
    assert result["step_id"] == "android_tv"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ANDROID_TV_REMOTE: REMOTE}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_CHANNEL_SOURCE] == CHANNEL_SOURCE_FAVORITES
    assert entry.options[CONF_SELECTED_CHANNELS] == ["rtl"]
    assert entry.options[CONF_ANDROID_TV_REMOTE] == REMOTE


async def test_options_all_channels_asks_for_selection(hass, waipu_api, remote_calls):
    entry, _ = await _setup(hass)
    result = await _options_init(
        hass,
        entry,
        **{CONF_TV_PLATFORM: TV_PLATFORM_ANDROID, CONF_CHANNEL_SOURCE: CHANNEL_SOURCE_ALL},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ANDROID_TV_REMOTE: REMOTE}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "channels"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SELECTED_CHANNELS: ["ard", "rtl"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_CHANNEL_SOURCE] == CHANNEL_SOURCE_ALL
    assert entry.options[CONF_SELECTED_CHANNELS] == ["ard", "rtl"]
    assert entry.options[CONF_ANDROID_TV_REMOTE] == REMOTE


async def test_options_platform_defaults_to_current_tv(hass, waipu_api, remote_calls):
    entry, _ = await _setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema = result["data_schema"].schema
    default = next(k for k in schema if k == CONF_TV_PLATFORM).default()
    assert default == TV_PLATFORM_ANDROID


async def test_options_switching_to_none_drops_tv_options(hass, waipu_api, remote_calls):
    entry, _ = await _setup(hass, options={"apple_tv_entity": "media_player.atv"})
    result = await _options_init(
        hass,
        entry,
        **{CONF_TV_PLATFORM: TV_PLATFORM_NONE, CONF_CHANNEL_SOURCE: CHANNEL_SOURCE_FAVORITES},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_ANDROID_TV_REMOTE not in entry.options
    assert "apple_tv_entity" not in entry.options


# --- media browser ----------------------------------------------------------------


async def _browse(hass, player, content_id=None, content_type=None):
    entity = hass.data["entity_components"]["media_player"].get_entity(player)
    return await entity.async_browse_media(content_type, content_id)


async def test_browse_root_has_recordings_and_channels(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    root = await _browse(hass, player)
    assert [c.media_content_id for c in root.children] == ["recordings", "channels"]


async def test_browse_recordings_lists_all_playable_watched_or_not(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "recordings", "recordings")
    # 2115976245 is FINISHED; 2105028496 is SCHEDULED and must not appear.
    assert [c.media_content_id for c in folder.children] == ["2115976245"]
    assert folder.children[0].can_play


async def test_browse_channels_follows_channel_selection(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "channels", "channels")
    # Favorites mode (default): rtl isn't a favorite.
    assert [c.media_content_id for c in folder.children] == ["ard", "zdf", "swr_bw"]


async def test_play_media_recording_from_browser(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "recordings", "recordings")
    item = folder.children[0]
    await hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": player,
            "media_content_type": item.media_content_type,
            "media_content_id": item.media_content_id,
        },
        blocking=True,
    )
    assert _activities(remote_calls) == [
        "waipu://recordings?recordingId=2115976245&autoplay=true"
    ]


async def test_play_media_channel_from_browser(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    await hass.services.async_call(
        "media_player",
        "play_media",
        {"entity_id": player, "media_content_type": "channel", "media_content_id": "zdf"},
        blocking=True,
    )
    assert _activities(remote_calls) == ["waipu://tv?id=zdf"]
