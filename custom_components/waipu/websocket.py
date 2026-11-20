"""Dashboard API: the TV guide for the waipu guide card (``waipu/guide``)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import EPG_LOOKAHEAD, EPG_LOOKBEHIND
from .coordinator import first_coordinator
from .media_player import can_record, visible_stations

# Recording states a guide entry is marked with (planned or running).
_MARKED_STATUSES = ("SCHEDULED", "RECORDING")


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_guide)


@websocket_api.websocket_command({vol.Required("type"): "waipu/guide"})
@callback
def ws_guide(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """The visible channels with the programs already loaded (from half an
    hour ago to six hours ahead), each marked recordable / recorded."""
    try:
        coordinator = first_coordinator(hass)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return
    connection.send_result(msg["id"], guide(coordinator))


def guide(coordinator: Any) -> dict[str, Any]:
    now = dt_util.utcnow()
    data = coordinator.data
    marked = {
        r.program_id: r
        for r in (data.recordings if data else [])
        if r.program_id and r.status in _MARKED_STATUSES
    }
    stations = []
    for station in visible_stations(coordinator.entry, coordinator):
        programs = [
            {
                "id": p.id,
                "title": p.title,
                "episode_title": p.episode_title,
                "start": p.start_time.isoformat(),
                "stop": p.stop_time.isoformat(),
                "series_id": p.series_id,
                "recordable": can_record(coordinator, station, p),
                "recording": marked[p.id].status if p.id in marked else None,
                "recording_id": marked[p.id].id if p.id in marked else None,
            }
            for p in station.programs
            if p.stop_time > now - EPG_LOOKBEHIND
        ]
        stations.append(
            {
                "id": station.id,
                "name": station.display_name,
                "logo": station.logo_url(),
                "programs": programs,
            }
        )
    return {
        "now": now.isoformat(),
        "start": (now - EPG_LOOKBEHIND).isoformat(),
        "end": (now + EPG_LOOKAHEAD).isoformat(),
        "dvr": bool(data and data.has_dvr),
        "stations": stations,
    }
