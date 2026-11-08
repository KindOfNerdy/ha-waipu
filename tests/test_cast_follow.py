"""Following a channel switch made on the TV itself via its Google Cast
entity (cast_follow.py), plus the media_player re-rendering right when the
shown program ends (WaipuProgramEntity)."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.data_entry_flow import FlowResultType

from custom_components.waipu.api import Program, WaipuClient
from custom_components.waipu.const import (
    ATTR_STATION_ID,
    CHANNEL_SOURCE_FAVORITES,
    CONF_ANDROID_TV_REMOTE,
    CONF_CAST_ENTITY,
    CONF_CHANNEL_SOURCE,
    CONF_TV_PLATFORM,
    DOMAIN,
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


def _set_cast(hass, title, *, app_name="waipu.tv", app_id="AndroidNativeApp", state="playing"):
    attrs = {"app_name": app_name, "app_id": app_id}
    if title:
        attrs["media_title"] = title
    hass.states.async_set(CAST, state, attrs)


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
