"""Following a channel switch made on the TV itself via its Google Cast
entity (cast_follow.py), plus the media_player re-rendering right when the
shown program ends (WaipuProgramEntity)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from homeassistant.data_entry_flow import FlowResultType

from custom_components.waipu.api import Program, Recording, WaipuClient
from custom_components.waipu.const import (
    ATTR_MODE,
    ATTR_RECORDING_ID,
    ATTR_STATION_ID,
    CHANNEL_SOURCE_FAVORITES,
    CONF_ANDROID_TV_REMOTE,
    CONF_CAST_ENTITY,
    CONF_CHANNEL_SOURCE,
    CONF_TV_PLATFORM,
    DOMAIN,
    SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
    SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
    TV_PLATFORM_ANDROID,
)

from .ha_common import async_fire_time_changed
from .test_android_tv import (  # noqa: F401 - fixtures are used by name
    REMOTE,
    STATIONS,
    _NOW,
    _options_init,
    _setup,
    _station,
    remote_calls,
    waipu_api,
)

CAST = "media_player.living_room_tv_cast"
WAIPU_IN_FRONT = {"current_activity": "de.exaring.waipu"}


def _set_cast(
    hass,
    title,
    *,
    app_name="waipu.tv",
    app_id="AndroidNativeApp",
    state="playing",
    position=None,
    duration=None,
    image=None,
):
    attrs = {"app_name": app_name, "app_id": app_id}
    if title:
        attrs["media_title"] = title
    if position is not None:
        attrs["media_position"] = position
        attrs["media_position_updated_at"] = datetime.now(timezone.utc)
    if duration is not None:
        attrs["media_duration"] = duration
    if image:
        attrs["entity_picture"] = image
    hass.states.async_set(CAST, state, attrs)


def _set_cast_live(hass, title, *, behind=timedelta(0)):
    """Live TV as Cast reports it: position = Unix time being watched."""
    watched = datetime.now(timezone.utc) - behind
    _set_cast(hass, title, position=watched.timestamp())


EPG_IMAGE = "https://images.wpstr.tv/image/fetch/s-x=//https%3A%2F%2Fcdn.images.simply.tv%2F1"
VOD_IMAGE = "https://images.wpstr.tv/vod/78/987e_0_MOVIE.png?res=640x360"


def _player(hass):
    return next(s for s in hass.states.async_all("media_player") if s.entity_id != CAST)


async def _setup_with_cast(hass):
    _set_cast(hass, None, state="idle")
    entry, coordinator = await _setup(hass, {CONF_CAST_ENTITY: CAST})
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await hass.async_block_till_done()
    return entry, coordinator


async def test_cast_title_selects_matching_channel(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Mittagsmagazin")
    await hass.async_block_till_done()

    assert coordinator.selected_station_id == "zdf"
    player = _player(hass)
    assert player.attributes["station_id"] == "zdf"
    assert player.attributes["media_title"] == "Mittagsmagazin"
    # Following only reads the TV — it must never send anything to it.
    assert remote_calls == []


async def test_cast_already_playing_at_setup_is_followed(hass, waipu_api, remote_calls):
    _set_cast(hass, "Mittagsmagazin")
    _, coordinator = await _setup(hass, {CONF_CAST_ENTITY: CAST})
    assert coordinator.selected_station_id == "zdf"


async def test_other_cast_app_is_ignored(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Mittagsmagazin", app_name="Netflix", app_id="CA5E8412")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id is None


async def test_phone_cast_receiver_counts_as_waipu(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Mittagsmagazin", app_name="", app_id="A1603972")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "zdf"


async def test_unknown_title_keeps_current_channel(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    await hass.services.async_call(
        DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "swr_bw"}, blocking=True
    )
    # e.g. a recording or a Mediathek video — no channel airs it.
    _set_cast(hass, "Watzmann ermittelt")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "swr_bw"


async def test_tuning_from_ha_is_not_reverted_by_old_cast_title(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "zdf"

    # The service fires a coordinator update while Cast still reports the
    # old title for a moment — that must not snap back to ZDF.
    await hass.services.async_call(
        DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "swr_bw"}, blocking=True
    )
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "swr_bw"


async def test_unmatched_title_is_retried_after_next_refresh(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Sondersendung")
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


async def test_without_cast_option_nothing_is_followed(hass, waipu_api, remote_calls):
    _set_cast(hass, "Mittagsmagazin")
    _, coordinator = await _setup(hass)
    _set_cast(hass, "Mittagsmagazin", state="paused")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id is None


async def test_options_flow_stores_and_clears_cast_entity(hass, waipu_api, remote_calls):
    _set_cast(hass, None, state="idle")
    entry, _ = await _setup(hass)
    fields = {CONF_TV_PLATFORM: TV_PLATFORM_ANDROID, CONF_CHANNEL_SOURCE: CHANNEL_SOURCE_FAVORITES}

    result = await _options_init(hass, entry, **fields)
    assert result["step_id"] == "android_tv"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ANDROID_TV_REMOTE: REMOTE, CONF_CAST_ENTITY: CAST}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_CAST_ENTITY] == CAST
    await hass.async_block_till_done()

    result = await _options_init(hass, entry, **fields)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ANDROID_TV_REMOTE: REMOTE}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_CAST_ENTITY not in entry.options


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
        await hass.services.async_call(
            DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "zdf"}, blocking=True
        )
        assert _player(hass).attributes["media_title"] == "Die Fallers"

        freezer.move_to(ends + timedelta(seconds=1))
        async_fire_time_changed(hass, ends + timedelta(seconds=1))
        await hass.async_block_till_done()
        assert _player(hass).attributes["media_title"] == "SWR Aktuell"


# --- recordings / waiputhek / timeshift (Cast values as seen 2026-11-09) ------


async def test_cast_recording_shows_recording(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert coordinator.selected_station_id == "zdf"

    _set_cast(hass, "JENKE.", position=625.7, duration=7361.7, image=EPG_IMAGE)
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.state == "playing"
    assert player.attributes["source"] == "Recordings"
    assert player.attributes["media_title"] == "JENKE."
    assert player.attributes["media_series_title"] == "Das Erste"
    assert player.attributes["recording_id"] == "2115976245"
    assert "station_id" not in player.attributes
    assert remote_calls == []


async def test_cast_waiputhek_shows_mediathek(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Otto - Der Film", position=7.8, duration=4977.2, image=VOD_IMAGE)
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["source"] == "Media library"
    assert player.attributes["media_title"] == "Otto - Der Film"
    assert player.attributes["media_content_type"] == "video"
    assert "media_series_title" not in player.attributes


async def test_back_to_same_live_channel_after_recording(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    _set_cast(hass, "JENKE.", position=10.0, duration=7361.7)
    await hass.async_block_till_done()
    assert coordinator.on_demand is not None

    # Same channel as before the recording — must still end the recording.
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert coordinator.on_demand is None
    player = _player(hass)
    assert player.attributes["source"] == "Live TV"
    assert player.attributes["station_id"] == "zdf"


async def test_recording_played_from_ha_shows_immediately(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await hass.async_block_till_done()
    assert _player(hass).attributes["media_title"] == "JENKE."

    # A poll while Cast still shows the live title must not revert it.
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert _player(hass).attributes["recording_id"] == "2115976245"


async def test_recording_details_mode_does_not_claim_playback(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245", ATTR_MODE: "details"}, blocking=True,
    )
    assert coordinator.on_demand is None


async def test_recording_played_without_cast_still_shown(hass, waipu_api, remote_calls):
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
    await hass.services.async_call(
        DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "zdf"}, blocking=True
    )
    await hass.async_block_till_done()
    assert _player(hass).attributes["source"] == "Live TV"
    assert coordinator.on_demand is None


async def test_unlisted_recording_is_vod_until_next_poll(hass, waipu_api, remote_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Brandneu", position=3.0, duration=1800.0, image=EPG_IMAGE)
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


async def test_timeshift_shows_program_being_watched(hass, waipu_api, remote_calls):
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
        _, coordinator = await _setup_with_cast(hass)
        _set_cast_live(hass, "Hubert und Staller", behind=timedelta(minutes=40))
        await hass.async_block_till_done()
    assert coordinator.selected_station_id == "swr_bw"
    player = _player(hass)
    assert player.attributes["media_title"] == "Hubert und Staller"
    assert player.attributes["timeshift_minutes"] == 40


async def test_ha_playback_not_reverted_by_pending_cast_retry(hass, waipu_api, remote_calls):
    # Cast shows an on-demand title it can't place for sure (retried on the
    # next poll) — then a recording is played from HA. The retry must not
    # put the stale Cast title back.
    _, coordinator = await _setup_with_cast(hass)
    _set_cast(hass, "Brandneu", position=3.0, duration=1800.0, image=EPG_IMAGE)
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
import pytest  # noqa: E402

from custom_components.waipu.api import ProgramDetail  # noqa: E402
from custom_components.waipu.const import SERVICE_RESTART_PROGRAM  # noqa: E402


def _player_entity(hass):
    eid = _player(hass).entity_id
    return hass.data["media_player"].get_entity(eid)


@pytest.fixture
def cast_calls(hass):
    """Capture media_player.* calls sent to the Cast entity. Registered
    after setup in each test, so the player's own methods are called
    directly instead of through these (now replaced) services."""
    calls: list[tuple[str, dict]] = []

    def _install():
        for service in ("media_seek", "media_pause", "media_play"):
            async def _capture(call, service=service):
                calls.append((service, dict(call.data)))
            hass.services.async_register("media_player", service, _capture)
        return calls

    return _install


async def test_on_demand_mirrors_cast_position_and_pause(hass, waipu_api, remote_calls):
    await _setup_with_cast(hass)
    _set_cast(hass, "JENKE.", position=625.7, duration=7361.7)
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["media_position"] == 625.7
    assert player.attributes["media_duration"] == 7361.7
    features = MediaPlayerEntityFeature(player.attributes["supported_features"])
    assert MediaPlayerEntityFeature.PAUSE in features
    assert MediaPlayerEntityFeature.SEEK in features

    _set_cast(hass, "JENKE.", position=630.0, duration=7361.7, state="paused")
    await hass.async_block_till_done()
    assert _player(hass).state == "paused"


async def test_live_has_no_position_or_seek(hass, waipu_api, remote_calls):
    await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    player = _player(hass)
    assert "media_position" not in player.attributes
    features = MediaPlayerEntityFeature(player.attributes["supported_features"])
    assert MediaPlayerEntityFeature.PAUSE in features
    assert MediaPlayerEntityFeature.SEEK not in features
    assert player.attributes["restart_available"] is True


async def test_seek_and_pause_go_to_cast(hass, waipu_api, remote_calls, cast_calls):
    await _setup_with_cast(hass)
    _set_cast(hass, "Otto - Der Film", position=7.8, duration=4977.2, image=VOD_IMAGE)
    await hass.async_block_till_done()
    calls = cast_calls()
    entity = _player_entity(hass)
    await entity.async_media_seek(1800)
    await entity.async_media_pause()
    await entity.async_media_play()
    assert calls == [
        ("media_seek", {"entity_id": CAST, "seek_position": 1800}),
        ("media_pause", {"entity_id": CAST}),
        ("media_play", {"entity_id": CAST}),
    ]
    assert remote_calls == []


async def test_recording_seek_without_cast_uses_deep_link(hass, waipu_api, remote_calls):
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


async def test_seek_on_live_is_refused(hass, waipu_api, remote_calls, cast_calls):
    await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    calls = cast_calls()
    with pytest.raises(ServiceValidationError):
        await _player_entity(hass).async_media_seek(10)
    assert calls == []


async def test_restart_program_seeks_cast_to_program_start(hass, waipu_api, remote_calls, cast_calls):
    _, coordinator = await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    calls = cast_calls()
    await hass.services.async_call(DOMAIN, SERVICE_RESTART_PROGRAM, {}, blocking=True)
    start = coordinator.station("zdf").current_program().start_time
    assert calls == [("media_seek", {"entity_id": CAST, "seek_position": start.timestamp()})]


async def test_restart_refused_where_seeking_is_forbidden(hass, waipu_api, remote_calls, cast_calls):
    forbidden = {"prog-now": ProgramDetail(id="prog-now", seeking_forbidden=True,
                                           pause_forbidden=True)}
    with patch.object(WaipuClient, "get_program_details", AsyncMock(return_value=forbidden)):
        await _setup_with_cast(hass)
        _set_cast_live(hass, "Mittagsmagazin")
        await hass.async_block_till_done()
        calls = cast_calls()
        player = _player(hass)
        assert player.attributes["restart_available"] is False
        features = MediaPlayerEntityFeature(player.attributes["supported_features"])
        assert MediaPlayerEntityFeature.PAUSE not in features
        with pytest.raises(ServiceValidationError, match="nicht erlaubt"):
            await hass.services.async_call(DOMAIN, SERVICE_RESTART_PROGRAM, {}, blocking=True)
    assert calls == []


async def test_restart_needs_cast_entity(hass, waipu_api, remote_calls):
    await _setup(hass)
    hass.states.async_set(REMOTE, "on", WAIPU_IN_FRONT)
    await hass.services.async_call(
        DOMAIN, SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV, {ATTR_STATION_ID: "zdf"}, blocking=True
    )
    with pytest.raises(ServiceValidationError, match="Cast"):
        await hass.services.async_call(DOMAIN, SERVICE_RESTART_PROGRAM, {}, blocking=True)


async def test_seek_within_live_program_updates_timeshift(hass, waipu_api, remote_calls):
    # Restart/seek keeps the title — the lag behind live alone must count.
    _, coordinator = await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert "timeshift_minutes" not in _player(hass).attributes

    _set_cast_live(hass, "Mittagsmagazin", behind=timedelta(minutes=10))
    await hass.async_block_till_done()
    assert _player(hass).attributes["timeshift_minutes"] == 10

    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    assert "timeshift_minutes" not in _player(hass).attributes


async def test_cast_seek_jump_reaches_player(hass, waipu_api, remote_calls):
    await _setup_with_cast(hass)
    _set_cast(hass, "JENKE.", position=625.7, duration=7361.7)
    await hass.async_block_till_done()
    # Same state, only the position jumped (a seek) — must be written.
    _set_cast(hass, "JENKE.", position=1800.0, duration=7361.7)
    await hass.async_block_till_done()
    assert _player(hass).attributes["media_position"] == 1800.0


async def test_ha_started_recording_ignores_stale_live_position(hass, waipu_api, remote_calls):
    # Until Cast catches up it still reports live TV — its position is a
    # Unix timestamp then, not a spot in the recording.
    await _setup_with_cast(hass)
    _set_cast_live(hass, "Mittagsmagazin")
    await hass.async_block_till_done()
    await hass.services.async_call(
        DOMAIN, SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        {ATTR_RECORDING_ID: "2115976245"}, blocking=True,
    )
    await hass.async_block_till_done()
    player = _player(hass)
    assert player.attributes["media_title"] == "JENKE."
    assert "media_position" not in player.attributes
