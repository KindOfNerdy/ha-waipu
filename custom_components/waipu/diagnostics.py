"""Diagnostics support — the 'Download diagnostics' button under
Settings → Devices & services → waipu.tv → ⋮ → Download diagnostics.

Redacts credentials/tokens; everything else here is either already public
(subscription tier name, station/recording counts) or a HA-internal
identifier (entry title, options), useful for a bug report without
exposing the account itself.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import WaipuCoordinator

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: WaipuCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data

    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": repr(coordinator.last_exception) if coordinator.last_exception else None,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds() if coordinator.update_interval else None
            ),
        },
        # Counts and booleans only — no station/program/recording titles,
        # which aren't needed to diagnose most reported issues and would
        # otherwise leak the user's actual viewing habits into a report.
        "data": (
            {
                "subscription": data.subscription,
                "has_dvr": data.has_dvr,
                "user_handle_present": bool(data.user_handle),
                "station_count": len(data.stations),
                "usable_station_count": sum(1 for s in data.stations if s.usable),
                "favorite_station_count": sum(1 for s in data.stations if s.favorite),
                "recording_count": len(data.recordings),
            }
            if data
            else None
        ),
    }
