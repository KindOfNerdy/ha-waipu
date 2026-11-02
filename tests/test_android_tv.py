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

from custom_components.waipu.api import Program, Recording, Station, WaipuClient
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
    SERVICE_OPEN_PROGRAM_ON_ANDROID_TV,
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


_NOW = datetime.now(timezone.utc)
ZDF_PROGRAMS = (
    Program(
        id="prog-now",
        title="Mittagsmagazin",
        start_time=_NOW - timedelta(minutes=30),
        stop_time=_NOW + timedelta(minutes=30),
        station_id="zdf",
    ),
    Program(
        id="prog-next",
        title="Krimi",
        episode_title="Folge 3",
        series_id="s9",
        start_time=_NOW + timedelta(minutes=30),
        stop_time=_NOW + timedelta(minutes=90),
        station_id="zdf",
    ),
)


def _station(
    station_id: str, name: str, favorite: bool = True, programs: tuple = ()
) -> Station:
    return Station(
        id=station_id,
        display_name=name,
        description=None,
        logo_template_url=None,
        stream_qualities=(),
        recording_forbidden=False,
        favorite=favorite,
        programs=programs,
    )


STATIONS = [
    _station("ard", "Das Erste"),
    _station("zdf", "ZDF", programs=ZDF_PROGRAMS),
    _station("swr_bw", "SWR BW"),
    _station("rtl", "RTL", favorite=False),
]


def _recording(
    rec_id: str,
    status: str = "FINISHED",
    *,
    title: str = "JENKE.",
    series_id: str | None = None,
    episode_title: str | None = None,
    days_ago: int = 1,
    fully_watched: bool = False,
) -> Recording:
    return Recording(
        id=rec_id,
        program_id=None,
        station_id="ard",
        station_display="Das Erste",
        title=title,
        status=status,
        recording_start_time=datetime.now(timezone.utc) - timedelta(days=days_ago),
        duration_seconds=3600,
        series_id=series_id,
        episode_title=episode_title,
        fully_watched=fully_watched,
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
                    # Two episodes of one series -> one folder; the watched
                    # one must still be listed.
                    _recording("ep-1", title="Tatort", series_id="777",
                               episode_title="Folge 1", days_ago=3),
                    _recording("ep-2", title="Tatort", series_id="777",
                               episode_title="Folge 2", days_ago=2, fully_watched=True),
                    # A second series sorting before "Tatort" by title.
                    _recording("ab-1", title="Akte X", series_id="555",
                               episode_title="Pilot", days_ago=9),
                    _recording("ab-2", title="Akte X", series_id="555",
                               episode_title="Teil 2", days_ago=8),
                    # A series with a single recorded episode stays flat.
                    _recording("solo", title="Krimi", series_id="888",
                               episode_title="Einzelfolge", days_ago=5),
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
    assert [c.media_content_id for c in root.children] == ["recordings", "channels", "guide"]


async def test_browse_recordings_lists_all_playable_watched_or_not(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "recordings", "recordings")
    # Series folders first, by title; then single recordings, newest first.
    # 2105028496 is SCHEDULED and must not appear.
    assert [c.media_content_id for c in folder.children] == [
        "series:555",
        "series:777",
        "2115976245",
        "solo",
    ]
    series = folder.children[1]
    assert series.can_expand and not series.can_play
    assert series.title == "Tatort (2 episodes)"
    assert folder.children[2].can_play
    assert folder.children[3].title.startswith("Krimi – Einzelfolge")


async def test_browse_series_folder_lists_episodes(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "series:777", "recordings")
    assert [c.media_content_id for c in folder.children] == ["ep-2", "ep-1"]
    # Inside the folder only the episode title (plus date) is shown.
    assert folder.children[0].title.startswith("Folge 2 (")
    assert all(c.can_play for c in folder.children)


async def test_browse_unknown_series_folder_errors(hass, waipu_api, remote_calls):
    from homeassistant.components.media_player import BrowseError

    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    with pytest.raises(BrowseError):
        await _browse(hass, player, "series:nope", "recordings")


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
    item = next(c for c in folder.children if c.can_play)
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


# --- TV guide / program detail page ---------------------------------------------


async def test_browse_guide_lists_channels_with_current_program(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    guide = await _browse(hass, player, "guide", "guide")
    assert [c.media_content_id for c in guide.children] == [
        "guide:ard",
        "guide:zdf",
        "guide:swr_bw",
    ]
    assert guide.children[1].title == "ZDF · Mittagsmagazin"


async def test_browse_guide_channel_lists_running_and_upcoming(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "guide:zdf", "guide")
    # Running program plays directly; the upcoming one is a folder of actions.
    assert [c.media_content_id for c in folder.children] == [
        "zdf/prog-now",
        "program:zdf/prog-next",
    ]
    assert folder.children[0].title == "Now · Mittagsmagazin"
    assert folder.children[0].can_play
    assert folder.children[1].can_expand and not folder.children[1].can_play
    assert folder.children[1].title.endswith("· Krimi – Folge 3")


@pytest.mark.parametrize(
    ("program", "expected"),
    [
        # Running program: play it (live).
        ("prog-now", "waipu://epgdetails?channelId=zdf&programId=prog-now&autoplay=true"),
        # Upcoming program (direct id, e.g. from automations): detail page.
        ("prog-next", "waipu://epgdetails?channelId=zdf&programId=prog-next"),
    ],
)
async def test_play_media_program_from_guide(hass, waipu_api, remote_calls, program, expected):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    await hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": player,
            "media_content_type": "waipu_program",
            "media_content_id": f"zdf/{program}",
        },
        blocking=True,
    )
    assert _activities(remote_calls) == [expected]


async def test_open_program_service_defaults_to_running_program(hass, waipu_api, remote_calls):
    await _setup(hass)
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_PROGRAM_ON_ANDROID_TV, {ATTR_STATION_ID: "zdf"}, blocking=True
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_PROGRAM_ON_ANDROID_TV,
        {ATTR_STATION_ID: "zdf", "program_id": "prog-next", "autoplay": True},
        blocking=True,
    )
    assert _activities(remote_calls) == [
        "waipu://epgdetails?channelId=zdf&programId=prog-now",
        "waipu://epgdetails?channelId=zdf&programId=prog-next&autoplay=true",
    ]


async def test_open_program_service_needs_a_station(hass, waipu_api, remote_calls):
    await _setup(hass)
    with pytest.raises(ServiceValidationError, match="Kein station_id"):
        await hass.services.async_call(
            DOMAIN, SERVICE_OPEN_PROGRAM_ON_ANDROID_TV, {}, blocking=True
        )


async def test_play_media_recording_fully_watched_starts_over(hass, waipu_api, remote_calls):
    # ep-2 is fully watched: its resume point would be in the credits.
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    for rec_id in ("ep-1", "ep-2"):
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": player,
                "media_content_type": "waipu_recording",
                "media_content_id": rec_id,
            },
            blocking=True,
        )
    assert _activities(remote_calls) == [
        "waipu://recordings?recordingId=ep-1&autoplay=true",
        "waipu://recordings?recordingId=ep-2&autoplay=true&position=0",
    ]


# --- actions on upcoming programs ----------------------------------------------


async def _actions(hass, player, program="prog-next"):
    folder = await _browse(hass, player, f"program:zdf/{program}", "guide")
    return [c.media_content_id.split("/")[0] for c in folder.children], folder


async def test_upcoming_program_offers_details_and_recording(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    actions, folder = await _actions(hass, player)
    assert actions == ["details", "record", "record_series"]
    assert all(c.can_play for c in folder.children)


async def test_upcoming_program_planned_offers_delete(hass, waipu_api, remote_calls):
    entry, coordinator = await _setup(hass)
    coordinator.data.recordings.append(
        Recording(
            id="rec-planned",
            program_id="prog-next",
            station_id="zdf",
            station_display="ZDF",
            title="Krimi",
            status="SCHEDULED",
            recording_start_time=_NOW + timedelta(minutes=30),
            duration_seconds=3600,
        )
    )
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    actions, folder = await _actions(hass, player)
    assert actions == ["details", "delete", "record_series"]
    assert folder.title.endswith("⏺ scheduled")
    with patch.object(WaipuClient, "delete_recordings", AsyncMock()) as mock_delete:
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": player,
                "media_content_type": "waipu_program_action",
                "media_content_id": "delete/zdf/prog-next",
            },
            blocking=True,
        )
    mock_delete.assert_awaited_once_with(["rec-planned"])


@pytest.mark.parametrize(
    ("action", "method", "args"),
    [
        ("record", "create_recording", ("prog-next", "zdf")),
        ("record_series", "create_serial_recording", ("zdf", "Krimi", "s9")),
    ],
)
async def test_upcoming_program_record_actions(hass, waipu_api, remote_calls, action, method, args):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    with patch.object(WaipuClient, method, AsyncMock()) as mock_call:
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": player,
                "media_content_type": "waipu_program_action",
                "media_content_id": f"{action}/zdf/prog-next",
            },
            blocking=True,
        )
    mock_call.assert_awaited_once_with(*args)
    assert remote_calls == []  # recording needs no TV


async def test_upcoming_program_details_action_opens_detail_page(hass, waipu_api, remote_calls):
    await _setup(hass)
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    await hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": player,
            "media_content_type": "waipu_program_action",
            "media_content_id": "details/zdf/prog-next",
        },
        blocking=True,
    )
    assert _activities(remote_calls) == ["waipu://epgdetails?channelId=zdf&programId=prog-next"]


async def test_upcoming_program_without_recording_rights_opens_details_directly(
    hass, waipu_api, remote_calls
):
    entry, coordinator = await _setup(hass)
    zdf = coordinator.station("zdf")
    forbidden = tuple(
        Program(**{**p.__dict__, "recording_forbidden": True}) for p in zdf.programs
    )
    coordinator.data.stations[coordinator.data.stations.index(zdf)] = Station(
        **{**zdf.__dict__, "programs": forbidden}
    )
    player = next(s.entity_id for s in hass.states.async_all("media_player"))
    folder = await _browse(hass, player, "guide:zdf", "guide")
    upcoming = folder.children[1]
    assert upcoming.media_content_id == "zdf/prog-next"
    assert upcoming.can_play and not upcoming.can_expand
