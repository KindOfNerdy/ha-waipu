"""Shared fixtures for the pytest-homeassistant-custom-component-backed
test tier (config_flow, coordinator, ...). The pure-logic tier
(test_api_*.py, test_const.py, test_program_station.py) doesn't need any
of this — see tests/helpers.py for how those load api.py/const.py
standalone, without homeassistant installed at all.
"""
from __future__ import annotations

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Makes custom_components/waipu loadable as a real integration in
    the test hass instance, instead of only the ones bundled with core."""
    yield
