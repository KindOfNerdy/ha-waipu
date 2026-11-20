"""waipu/guide: the TV guide for the guide card."""
from __future__ import annotations

from custom_components.waipu.api import Recording

from .test_android_tv import _setup, remote_calls, waipu_api  # noqa: F401 - fixtures


async def test_guide_lists_visible_channels_with_programs(hass, hass_ws_client, waipu_api, remote_calls):
    _, coordinator = await _setup(hass)
    coordinator.data.recordings.append(
        Recording(id="r1", program_id="prog-next", station_id="zdf", station_display="ZDF",
                  title="Krimi", status="SCHEDULED", recording_start_time=None, duration_seconds=0)
    )
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "waipu/guide"})
    msg = await client.receive_json()
    assert msg["success"]
    result = msg["result"]
    # Same channels and order as the player's channel list (favorites).
    assert [s["id"] for s in result["stations"]] == ["ard", "zdf", "swr_bw"]
    zdf = result["stations"][1]
    assert [p["id"] for p in zdf["programs"]] == ["prog-now", "prog-next"]
    now, nxt = zdf["programs"]
    assert now["recordable"] is True and now["recording"] is None
    assert nxt["recording"] == "SCHEDULED" and nxt["recording_id"] == "r1"
    assert nxt["series_id"] == "s9"
    assert result["dvr"] is True and result["start"] < result["now"] < result["end"]


async def test_guide_without_integration_errors(hass, hass_ws_client):
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, "waipu", {})
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "waipu/guide"})
    msg = await client.receive_json()
    assert not msg["success"] and msg["error"]["code"] == "not_loaded"
