"""MockConfigEntry and time helpers from whichever Home Assistant test
harness is installed: pytest-homeassistant-custom-component (community, up
to HA 2026.10) or the official pytest-home-assistant shipped with HA
2026.11+ — switching only needs a requirements_test.txt change, not a test
rewrite."""
from __future__ import annotations

try:
    from pytest_homeassistant_custom_component.common import (
        MockConfigEntry,
        async_fire_time_changed,
    )
except ImportError:
    from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

__all__ = ["MockConfigEntry", "async_fire_time_changed"]
