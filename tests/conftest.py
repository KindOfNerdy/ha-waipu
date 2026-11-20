"""Shared fixtures for the pytest-homeassistant-custom-component-backed
test tier (config_flow, coordinator, ...). The pure-logic tier
(test_api_*.py, test_const.py, test_program_station.py) doesn't need any
of this — see tests/helpers.py for how those load api.py/const.py
standalone, without homeassistant installed at all.
"""
from __future__ import annotations

import pytest

try:
    import pytest_homeassistant_custom_component  # noqa: F401
except ImportError:
    # Official pytest-home-assistant (HA 2026.11+) registers itself as a
    # pytest plugin — nothing to load here.
    pass
else:
    pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Makes custom_components/waipu loadable as a real integration in
    the test hass instance, instead of only the ones bundled with core."""
    yield


@pytest.fixture(autouse=True)
def recording_summary():
    """waipu's DVR fill level — answered for every test that sets up the
    integration, so none of them reaches the network for it."""
    try:
        from custom_components.waipu.api import RecordingSummary, WaipuClient
    except ImportError:  # pure-logic tier without homeassistant
        yield None
        return
    from unittest.mock import AsyncMock, patch

    summary = RecordingSummary(available_hours=140.45, finished_seconds=36000,
                               finished_count=4, lost_count=0)
    with patch.object(WaipuClient, "get_recording_summary", AsyncMock(return_value=summary)):
        yield summary
