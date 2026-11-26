"""Following a channel switch made on the TV itself via Android's media
session, read over ADB (tv_follow.py), plus the media_player re-rendering
right when the shown program ends (WaipuProgramEntity)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.waipu.api import Program, Recording, WaipuClient
from custom_components.waipu.const import (
    ATTR_MODE,
    ATTR_RECORDING_ID,
    CHANNEL_SOURCE_FAVORITES,
    CONF_ADB_ENTITY,
    CONF_ANDROID_TV_REMOTE,
    CONF_CHANNEL_SOURCE,
    CONF_TV_PLATFORM,
    DOMAIN,
    SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
    TV_PLATFORM_ANDROID,
    TV_POLL_INTERVAL,
)

from custom_components.waipu.const import waipu_station_link

from .ha_common import async_fire_time_changed
from .test_android_tv import (  # noqa: F401 - fixtures are used by name
    REMOTE,
    STATIONS,
    _NOW,
    _options_init,
    _setup,
    _station,
    remote_calls,
    tune_channel,
    waipu_api,
)

ADB = "media_player.living_room_tv_adb"
WAIPU_IN_FRONT = {"current_activity": "de.exaring.waipu"}
# What the TV answers; None = waipu has no media session. Per test (the
# `tv` fixture resets it).
_ANSWER: dict[str, str | None] = {"text": None}
_BUMP = [0]


def _session(title, *, package="de.exaring.waipu", state=3, position_ms=0):
    """`dumpsys media_session | grep -A 14 package=…` as seen 2026-11-26."""
    return (
        f"      package={package}\n"
        "      launchIntent=null\n"
        "      mediaButtonReceiver=null\n"
        "      active=true\n"
        "      flags=3\n"
        "      rating type=0\n"
        "      controllers: 4\n"
        f"      state=PlaybackState {{state={state}, position={position_ms}, buffered position=0, "
        "speed=1.0, updated=20196877, actions=895, custom actions=[], active item id=-1, "
        "error=null}\n"
        "      audioAttrs=AudioAttributes: usage=USAGE_MEDIA content=CONTENT_TYPE_UNKNOWN\n"
        "      volumeType=1, controlType=2, max=0, current=0\n"
        f"      metadata: size=2, description={title}, null, null\n"
        "      queueTitle=null, size=0\n"
    )


def _set_tv(hass, title, *, state="playing", position=None, behind=timedelta(0)):
    """What waipu plays per the TV — and ask it right away (a change of the
    remote entity does that). Without `position` (seconds on demand) it is
    live TV: position = Unix time (ms) being watched."""
    if title is None:
        _ANSWER["text"] = None
    else:
        if position is None:
            position = (datetime.now(timezone.utc) - behind).timestamp()
        _ANSWER["text"] = _session(
            title, state=2 if state == "paused" else 3, position_ms=int(position * 1000)
        )
    _BUMP[0] += 1
    hass.states.async_set(REMOTE, "on", {**WAIPU_IN_FRONT, "bump": _BUMP[0]})


@pytest.fixture
def tv(hass):
    """HA's Android Debug Bridge entity: answers androidtv.adb_command the
    way the integration does, by writing the adb_response attribute."""
    commands: list[str] = []
    _ANSWER["text"] = None

    async def _adb_command(call):
        commands.append(call.data["command"])
        hass.states.async_set(ADB, "idle", {"adb_response": _ANSWER["text"] or ""})

    hass.services.async_register("androidtv", "adb_command", _adb_command)
    hass.states.async_set(ADB, "idle", {"adb_response": None})
    return commands


def _player(hass):
    return next(s for s in hass.states.async_all("media_player") if s.entity_id != ADB)


async def _setup_with_tv(hass):
    entry, coordinator = await _setup(hass, {CONF_ADB_ENTITY: ADB})
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await hass.async_block_till_done()
    return entry, coordinator


async def test_tv_title_selects_matching_channel(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()

    assert coordinator.selected_station_id == "zdf"
    player = _player(hass)
    assert player.attributes["station_id"] == "zdf"
    assert player.attributes["media_title"] == "Mittagsmagazin"
    # Following only reads the TV — it must never send anything to it.
    assert remote_calls == []


async def test_already_playing_at_setup_is_followed(hass, waipu_api, remote_calls, tv):
    _set_tv(hass, "Mittagsmagazin")
    _, coordinator = await _setup(hass, {CONF_ADB_ENTITY: ADB})
    assert coordinator.selected_station_id == "zdf"
    assert tv[0] == "dumpsys media_session | grep -A 14 'package=de.exaring.waipu'"


async def test_other_apps_session_is_ignored(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _ANSWER["text"] = _session("Mittagsmagazin", package="com.netflix.ninja")
    hass.states.async_set(REMOTE, "on", {**WAIPU_IN_FRONT, "bump": -1})
    await hass.async_block_till_done()
    assert coordinator.selected_station_id is None


async def test_tv_is_not_asked_while_another_app_is_in_front(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert _player(hass).attributes["station_id"] == "zdf"

    hass.states.async_set(REMOTE, "on", {"current_activity": "com.netflix.ninja"})
    await hass.async_block_till_done()
    tv.clear()
    async_fire_time_changed(hass, datetime.now(timezone.utc) + TV_POLL_INTERVAL)
    await hass.async_block_till_done()
    assert tv == []
    assert coordinator.tv_playback is None
    assert "station_id" not in _player(hass).attributes


async def test_channel_switch_is_seen_on_the_next_tick(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    assert coordinator.selected_station_id is None
    # Switched with the TV's own remote: nothing tells HA, only the tick.
    _ANSWER["text"] = _session(
        "Mittagsmagazin", position_ms=int(datetime.now(timezone.utc).timestamp() * 1000)
    )
    async_fire_time_changed(hass, datetime.now(timezone.utc) + TV_POLL_INTERVAL)
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "zdf"


async def test_adb_failure_keeps_the_player_working(hass, waipu_api, remote_calls):
    # No androidtv.adb_command service at all (integration not loaded).
    _, coordinator = await _setup(hass, {CONF_ADB_ENTITY: ADB})
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await hass.async_block_till_done()
    await tune_channel(hass, "zdf")
    assert _player(hass).attributes["station_id"] == "zdf"


def _simulcast_stations():
    """"Mittagsmagazin" on ZDF and Das Erste at once, "Punkt 12" on RTL."""
    def now_on(station_id, title):
        return (Program(id=f"p-{station_id}", title=title,
                        start_time=_NOW - timedelta(minutes=30),
                        stop_time=_NOW + timedelta(minutes=30), station_id=station_id),)
    return [
        _station("zdf", "ZDF", programs=now_on("zdf", "Mittagsmagazin")),
        _station("ard", "Das Erste", programs=now_on("ard", "Mittagsmagazin")),
        _station("rtl", "RTL", programs=now_on("rtl", "Punkt 12")),
    ]


async def test_back_to_a_simulcast_goes_to_the_channel_watched_before(
    hass, waipu_api, remote_calls, tv
):
    with patch.object(WaipuClient, "get_stations", AsyncMock(return_value=_simulcast_stations())):
        _, coordinator = await _setup_with_tv(hass)
        await tune_channel(hass, "ard")
        _set_tv(hass, "Punkt 12")
        await hass.async_block_till_done()
        assert coordinator.selected_station_id == "rtl"

        _set_tv(hass, "Mittagsmagazin")
        await hass.async_block_till_done()
    assert coordinator.selected_station_id == "ard"


async def test_simulcast_never_watched_shows_title_without_channel(
    hass, waipu_api, remote_calls, tv
):
    with patch.object(WaipuClient, "get_stations", AsyncMock(return_value=_simulcast_stations())):
        _, coordinator = await _setup_with_tv(hass)
        _set_tv(hass, "Punkt 12")
        await hass.async_block_till_done()
        assert _player(hass).attributes["station_id"] == "rtl"

        # Neither ZDF nor Das Erste was watched before: not RTL anymore,
        # but which of the two can't be told.
        _set_tv(hass, "Mittagsmagazin")
        await hass.async_block_till_done()
    assert coordinator.selected_station_id is None
    player = _player(hass)
    assert player.state == "playing"
    assert player.attributes["media_title"] == "Mittagsmagazin"
    assert "station_id" not in player.attributes


async def test_unknown_title_keeps_current_channel(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    await tune_channel(hass, "swr_bw")
    # e.g. a recording or a Mediathek video — no channel airs it.
    _set_tv(hass, "Watzmann ermittelt")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "swr_bw"


async def test_tuning_from_ha_is_not_reverted_by_old_tv_title(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "zdf"

    # The service fires a coordinator update while the TV still reports the
    # old title for a moment — that must not snap back to ZDF.
    await tune_channel(hass, "swr_bw")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "swr_bw"


async def test_unmatched_title_is_retried_after_next_refresh(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Sondersendung")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id is None

    special = Program(
        id="prog-special",
        title="Sondersendung",
        start_time=_NOW - timedelta(minutes=5),
        stop_time=_NOW + timedelta(minutes=55),
        station_id="ard",
    )
    stations = [
        _station("ard", "Das Erste", programs=(special,)),
        *[s for s in STATIONS if s.id != "ard"],
    ]
    with patch.object(WaipuClient, "get_stations", AsyncMock(return_value=stations)):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert coordinator.selected_station_id == "ard"


async def test_without_adb_option_nothing_is_followed(hass, waipu_api, remote_calls, tv):
    _set_tv(hass, "Mittagsmagazin")
    _, coordinator = await _setup(hass)
    _set_tv(hass, "Mittagsmagazin", state="paused")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id is None
    assert tv == []


async def test_options_flow_stores_and_clears_adb_entity(hass, waipu_api, remote_calls, tv):
    entry, _ = await _setup(hass)
    fields = {CONF_TV_PLATFORM: TV_PLATFORM_ANDROID, CONF_CHANNEL_SOURCE: CHANNEL_SOURCE_FAVORITES}

    result = await _options_init(hass, entry, **fields)
    assert result["step_id"] == "android_tv"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ANDROID_TV_REMOTE: REMOTE, CONF_ADB_ENTITY: ADB}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ADB_ENTITY] == ADB
    await hass.async_block_till_done()

    result = await _options_init(hass, entry, **fields)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ANDROID_TV_REMOTE: REMOTE}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_ADB_ENTITY not in entry.options


async def test_player_title_flips_when_program_ends(hass, waipu_api, remote_calls, freezer):
    # The program ends 2 minutes in — well before the next coordinator
    # poll (DEFAULT_SCAN_INTERVAL, 5 min), so only the program-end timer
    # can make the title change.
    freezer.move_to(_NOW)
    ends = _NOW + timedelta(minutes=2)
    programs = (
        Program(id="p-old", title="Die Fallers", start_time=_NOW - timedelta(minutes=28),
                stop_time=ends, station_id="zdf"),
        Program(id="p-new", title="SWR Aktuell", start_time=ends,
                stop_time=ends + timedelta(minutes=30), station_id="zdf"),
    )
    stations = [
        _station("zdf", "ZDF", programs=programs),
        *[s for s in STATIONS if s.id != "zdf"],
    ]
    with patch.object(WaipuClient, "get_stations", AsyncMock(return_value=stations)):
        await _setup(hass)
        hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
        await tune_channel(hass, "zdf")
        assert _player(hass).attributes["media_title"] == "Die Fallers"

        freezer.move_to(ends + timedelta(seconds=1))
        async_fire_time_changed(hass, ends + timedelta(seconds=1))
        await hass.async_block_till_done()
        assert _player(hass).attributes["media_title"] == "SWR Aktuell"


# --- recordings / waiputhek / timeshift (on demand: position in seconds) ------


async def test_tv_recording_shows_recording(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "zdf"

    _set_tv(hass, "JENKE.", position=625.7)
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.state == "playing"
    assert player.attributes["source"] == "Recordings"
    assert player.attributes["media_title"] == "JENKE."
    assert player.attributes["media_series_title"] == "Das Erste"
    assert player.attributes["recording_id"] == "2115976245"
    assert "station_id" not in player.attributes
    assert remote_calls == []


async def test_tv_waiputhek_shows_mediathek(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Otto - Der Film", position=7.8)
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["source"] == "Media library"
    assert player.attributes["media_title"] == "Otto - Der Film"
    assert player.attributes["media_content_type"] == "video"
    assert "media_series_title" not in player.attributes


async def test_back_to_same_live_channel_after_recording(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    _set_tv(hass, "JENKE.", position=10.0)
    await hass.async_block_till_done()
    assert coordinator.on_demand is not None

    # Same channel as before the recording — must still end the recording.
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert coordinator.on_demand is None
    player = _player(hass)
    assert player.attributes["source"] == "Live TV"
    assert player.attributes["station_id"] == "zdf"


async def test_recording_played_from_ha_shows_immediately(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await hass.async_block_till_done()
    assert _player(hass).attributes["media_title"] == "JENKE."

    # A poll while the TV still shows the live title must not revert it.
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _player(hass).attributes["recording_id"] == "2115976245"


async def test_recording_details_mode_does_not_claim_playback(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245", ATTR_MODE: "details"}, blocking=True,
    )
    assert coordinator.on_demand is None


async def test_recording_played_without_adb_still_shown(hass, waipu_api, remote_calls):
    _, coordinator = await _setup(hass)
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["source"] == "Recordings"
    assert player.attributes["media_title"] == "JENKE."

    # Tuning a channel from HA ends it.
    await tune_channel(hass, "zdf")
    await hass.async_block_till_done()
    assert _player(hass).attributes["source"] == "Live TV"
    assert coordinator.on_demand is None


async def test_unlisted_recording_is_vod_until_next_poll(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Brandneu", position=3.0)
    await hass.async_block_till_done()
    assert _player(hass).attributes["source"] == "Media library"

    fresh = Recording(
        id="rec-new", program_id=None, station_id="rtl", station_display="RTL",
        title="Brandneu", status="FINISHED", recording_start_time=_NOW,
        duration_seconds=1800,
    )
    with patch.object(WaipuClient, "get_recordings", AsyncMock(return_value=[fresh])):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["source"] == "Recordings"
    assert player.attributes["media_series_title"] == "RTL"


async def test_timeshift_shows_program_being_watched(hass, waipu_api, remote_calls, tv):
    # 40 minutes behind live on a program that ended live 10 minutes ago.
    now = datetime.now(timezone.utc)
    programs = (
        Program(id="p-old", title="Hubert und Staller", start_time=now - timedelta(minutes=60),
                stop_time=now - timedelta(minutes=10), station_id="swr_bw"),
        Program(id="p-now", title="SWR Aktuell", start_time=now - timedelta(minutes=10),
                stop_time=now + timedelta(minutes=20), station_id="swr_bw"),
    )
    stations = [
        _station("swr_bw", "SWR BW", programs=programs),
        *[s for s in STATIONS if s.id != "swr_bw"],
    ]
    with patch.object(WaipuClient, "get_stations", AsyncMock(return_value=stations)):
        _, coordinator = await _setup_with_tv(hass)
        _set_tv(hass, "Hubert und Staller", behind=timedelta(minutes=40))
        await hass.async_block_till_done()
    assert coordinator.selected_station_id == "swr_bw"
    player = _player(hass)
    assert player.attributes["media_title"] == "Hubert und Staller"
    assert player.attributes["timeshift_minutes"] == 40


async def test_ha_playback_not_reverted_by_pending_tv_retry(hass, waipu_api, remote_calls, tv):
    # The TV shows an on-demand title it can't place for sure (retried on the
    # next poll) — then a recording is played from HA. The retry must not
    # put the stale TV title back.
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Brandneu", position=3.0)
    await hass.async_block_till_done()
    assert coordinator.on_demand.tentative

    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _player(hass).attributes["media_title"] == "JENKE."


# --- playback controls (tested live 2026-11-09) ------------------------------
from homeassistant.components.media_player import MediaPlayerEntityFeature  # noqa: E402
from homeassistant.exceptions import ServiceValidationError  # noqa: E402

from custom_components.waipu.api import ProgramDetail  # noqa: E402
from custom_components.waipu.const import SERVICE_RESTART_PROGRAM  # noqa: E402


def _player_entity(hass):
    eid = _player(hass).entity_id
    return hass.data["media_player"].get_entity(eid)


@pytest.fixture
def key_calls(hass):
    """Capture remote.send_command calls (keys pressed on the TV)."""
    calls: list[list[str]] = []

    async def _send_command(call):
        calls.append(list(call.data["command"]))

    hass.services.async_register("remote", "send_command", _send_command)
    return calls


async def test_on_demand_mirrors_tv_position_and_pause(hass, waipu_api, remote_calls, tv):
    await _setup_with_tv(hass)
    _set_tv(hass, "JENKE.", position=625.7)
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["media_position"] == 625.7
    # The TV reports no length — a recording's comes from the list.
    assert player.attributes["media_duration"] == 3600
    features = MediaPlayerEntityFeature(player.attributes["supported_features"])
    assert MediaPlayerEntityFeature.PAUSE in features
    assert MediaPlayerEntityFeature.SEEK in features

    _set_tv(hass, "JENKE.", position=630.0, state="paused")
    await hass.async_block_till_done()
    assert _player(hass).state == "paused"


async def test_live_has_no_position_but_can_jump(hass, waipu_api, remote_calls, tv):
    await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    player = _player(hass)
    assert "media_position" not in player.attributes
    features = MediaPlayerEntityFeature(player.attributes["supported_features"])
    assert MediaPlayerEntityFeature.PAUSE in features
    # Live, a seek is a jump within waipu's timeshift buffer (Unix time).
    assert MediaPlayerEntityFeature.SEEK in features
    assert player.attributes["restart_available"] is True


async def test_pause_and_play_press_the_key_only_when_needed(
    hass, waipu_api, remote_calls, tv, key_calls
):
    await _setup_with_tv(hass)
    _set_tv(hass, "JENKE.", position=625.7)
    await hass.async_block_till_done()
    entity = _player_entity(hass)
    await entity.async_media_play()  # already playing: the key would pause
    assert key_calls == []
    await entity.async_media_pause()
    assert key_calls == [["MEDIA_PLAY_PAUSE"]]

    _set_tv(hass, "JENKE.", position=626.0, state="paused")
    await hass.async_block_till_done()
    await entity.async_media_pause()  # already paused
    assert key_calls == [["MEDIA_PLAY_PAUSE"]]
    await entity.async_media_play()
    assert key_calls == [["MEDIA_PLAY_PAUSE"], ["MEDIA_PLAY_PAUSE"]]


async def test_pause_without_adb_toggles(hass, waipu_api, remote_calls, key_calls):
    await _setup(hass)
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await tune_channel(hass, "zdf")
    await _player_entity(hass).async_media_pause()
    assert key_calls == [["MEDIA_PLAY_PAUSE"]]


async def test_waiputhek_cannot_seek(hass, waipu_api, remote_calls, tv):
    await _setup_with_tv(hass)
    _set_tv(hass, "Otto - Der Film", position=7.8)
    await hass.async_block_till_done()
    player = _player(hass)
    features = MediaPlayerEntityFeature(player.attributes["supported_features"])
    assert MediaPlayerEntityFeature.SEEK not in features
    assert "media_duration" not in player.attributes
    with pytest.raises(ServiceValidationError, match="Mediathek"):
        await _player_entity(hass).async_media_seek(1800)
    assert remote_calls == []


async def test_recording_seek_uses_deep_link(hass, waipu_api, remote_calls):
    await _setup(hass)
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await hass.async_block_till_done()
    remote_calls.clear()
    await _player_entity(hass).async_media_seek(600.4)
    assert [c["activity"] for c in remote_calls] == [
        "waipu://recordings?recordingId=2115976245&autoplay=true&position=600"
    ]


async def test_seek_on_live_jumps_within_the_timeshift(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    remote_calls.clear()
    back = datetime.now(timezone.utc) - timedelta(seconds=90)
    await _player_entity(hass).async_media_seek(back.timestamp())
    assert remote_calls[-1]["activity"] == f"waipu://tv?id=zdf&position={int(back.timestamp() * 1000)}"
    assert timedelta(seconds=85) < coordinator.timeshift < timedelta(seconds=95)
    assert _player(hass).attributes["timeshift_seconds"] in range(85, 96)
    # Seeking to now (or later) goes back to live — no position.
    await _player_entity(hass).async_media_seek(datetime.now(timezone.utc).timestamp() + 60)
    assert remote_calls[-1]["activity"] == "waipu://tv?id=zdf"
    assert coordinator.timeshift == timedelta(0)


async def test_restart_program_opens_channel_at_program_start(hass, waipu_api, remote_calls, tv):
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    remote_calls.clear()
    await hass.services.async_call(DOMAIN, SERVICE_RESTART_PROGRAM, {}, blocking=True)
    start = coordinator.station("zdf").current_program().start_time
    # waipu's channel link with the start as position (Unix ms).
    assert [c["activity"] for c in remote_calls] == [waipu_station_link("zdf", start)]
    assert f"position={int(start.timestamp() * 1000)}" in remote_calls[0]["activity"]
    assert coordinator.timeshift > timedelta(0)


async def test_restart_refused_where_seeking_is_forbidden(hass, waipu_api, remote_calls, tv):
    forbidden = {"prog-now": ProgramDetail(id="prog-now", seeking_forbidden=True,
                                           pause_forbidden=True)}
    with patch.object(WaipuClient, "get_program_details", AsyncMock(return_value=forbidden)):
        await _setup_with_tv(hass)
        _set_tv(hass, "Mittagsmagazin")
        await hass.async_block_till_done()
        player = _player(hass)
        assert player.attributes["restart_available"] is False
        features = MediaPlayerEntityFeature(player.attributes["supported_features"])
        assert MediaPlayerEntityFeature.PAUSE not in features
        with pytest.raises(ServiceValidationError, match="kein Spulen"):
            await hass.services.async_call(DOMAIN, SERVICE_RESTART_PROGRAM, {}, blocking=True)


async def test_restart_works_without_adb_entity(hass, waipu_api, remote_calls):
    entry, coordinator = await _setup(hass)
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await tune_channel(hass, "zdf")
    await hass.async_block_till_done()
    assert _player(hass).attributes["restart_available"] is True
    remote_calls.clear()
    await hass.services.async_call(DOMAIN, SERVICE_RESTART_PROGRAM, {}, blocking=True)
    start = coordinator.station("zdf").current_program().start_time
    assert [c["activity"] for c in remote_calls] == [waipu_station_link("zdf", start)]


async def test_seek_within_live_program_updates_timeshift(hass, waipu_api, remote_calls, tv):
    # Restart/seek keeps the title — the lag behind live alone must count.
    _, coordinator = await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert "timeshift_minutes" not in _player(hass).attributes

    _set_tv(hass, "Mittagsmagazin", behind=timedelta(minutes=10))
    await hass.async_block_till_done()
    assert _player(hass).attributes["timeshift_minutes"] == 10

    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert "timeshift_minutes" not in _player(hass).attributes


async def test_tv_seek_jump_reaches_player(hass, waipu_api, remote_calls, tv):
    await _setup_with_tv(hass)
    _set_tv(hass, "JENKE.", position=625.7)
    await hass.async_block_till_done()
    # Same state, only the position jumped (a seek) — must be written.
    _set_tv(hass, "JENKE.", position=1800.0)
    await hass.async_block_till_done()
    assert _player(hass).attributes["media_position"] == 1800.0


async def test_ha_started_recording_ignores_stale_live_position(hass, waipu_api, remote_calls, tv):
    # Until the TV catches up it still reports live TV — its position is a
    # Unix timestamp then, not a spot in the recording.
    await _setup_with_tv(hass)
    _set_tv(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["media_title"] == "JENKE."
    assert "media_position" not in player.attributes
