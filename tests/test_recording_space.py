"""The DVR's free recording time, as a sensor on the recordings device."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.helpers import entity_registry as er

from custom_components.waipu.api import WaipuApiError, WaipuClient
from custom_components.waipu.const import DOMAIN

from .test_android_tv import _setup, remote_calls, waipu_api  # noqa: F401 - fixtures


def _space_sensor(hass) -> str:
    return next(
        e.entity_id
        for e in er.async_get(hass).entities.values()
        if e.platform == DOMAIN and e.translation_key == "recording_space"
    )


async def test_free_recording_space(hass, waipu_api, remote_calls):
    await _setup(hass)
    state = hass.states.get(_space_sensor(hass))
    assert float(state.state) == 140.45
    assert state.attributes["unit_of_measurement"] == "h"
    assert state.attributes["used_hours"] == 10.0
    assert state.attributes["finished_recordings"] == 4
    assert state.attributes["lost_recordings"] == 0


async def test_unavailable_when_waipu_does_not_answer(hass, waipu_api, remote_calls):
    with patch.object(WaipuClient, "get_recording_summary", AsyncMock(side_effect=WaipuApiError("x"))):
        await _setup(hass)
        # The rest of the integration keeps working.
        assert hass.states.get(_space_sensor(hass)).state == "unavailable"
        assert any(s.entity_id.startswith("media_player.") for s in hass.states.async_all())
