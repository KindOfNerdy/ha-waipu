"""Services exposed by the waipu.tv integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import Program, WaipuApiError, WaipuPermissionError
from .const import (
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    ATTR_PROGRAM_ID,
    ATTR_RECORDING_ID,
    ATTR_SERIES_ID,
    ATTR_STATION_ID,
    CONF_ANDROID_TV_CHANNEL_VIEW,
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_WAIPU_APP_LINK,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_WAIPU_APP_LINK,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
    SERVICE_CREATE_RECORDING,
    SERVICE_CREATE_SERIAL_RECORDING,
    SERVICE_DELETE_RECORDING,
    SERVICE_DELETE_SERIAL_RECORDING,
    SERVICE_LAUNCH_ON_ANDROID_TV,
    SERVICE_LAUNCH_ON_APPLE_TV,
    SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
)
from .coordinator import WaipuCoordinator
from .media_player import _countable_stations

_LOGGER = logging.getLogger(__name__)

CREATE_RECORDING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_STATION_ID): cv.string,
        vol.Optional(ATTR_PROGRAM_ID): cv.string,
    }
)

DELETE_RECORDING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_RECORDING_ID): vol.All(cv.ensure_list, [cv.string]),
    }
)

CREATE_SERIAL_RECORDING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_STATION_ID): cv.string,
        vol.Optional(ATTR_PROGRAM_ID): cv.string,
    }
)

DELETE_SERIAL_RECORDING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERIES_ID): cv.string,
        vol.Optional("delete_finished_recordings", default=False): cv.boolean,
        vol.Optional("delete_running_recordings", default=False): cv.boolean,
    }
)

LAUNCH_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATION_ID): cv.string,
    }
)

LAUNCH_ANDROID_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATION_ID): cv.string,
    }
)

SWITCH_CHANNEL_ANDROID_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_STATION_ID): cv.string,
    }
)


def _first_coordinator(hass: HomeAssistant) -> WaipuCoordinator:
    coordinators: dict[str, WaipuCoordinator] = hass.data.get(DOMAIN, {})
    if not coordinators:
        raise HomeAssistantError("waipu.tv integration is not loaded")
    return next(iter(coordinators.values()))


async def _handle_create_recording(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    station_id = call.data[ATTR_STATION_ID]
    program_id = call.data.get(ATTR_PROGRAM_ID)

    if not program_id:
        station = coordinator.station(station_id)
        if not station:
            raise ServiceValidationError(f"Sender unbekannt: {station_id}")
        current = station.current_program()
        if not current:
            raise ServiceValidationError(
                f"Kein laufendes Programm auf '{station_id}'"
            )
        if current.recording_forbidden:
            raise ServiceValidationError("Diese Sendung ist nicht aufnehmbar")
        program_id = current.id

    try:
        await coordinator.client.create_recording(program_id, station_id)
    except WaipuPermissionError as err:
        raise HomeAssistantError(
            "Aufnahme nicht erlaubt (Abo prüfen)"
        ) from err
    except WaipuApiError as err:
        raise HomeAssistantError(f"waipu API-Fehler: {err}") from err

    await coordinator.async_request_refresh()


async def _handle_delete_recording(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    ids: list[str] = call.data[ATTR_RECORDING_ID]
    try:
        await coordinator.client.delete_recordings(ids)
    except WaipuApiError as err:
        raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
    await coordinator.async_request_refresh()


async def _handle_create_serial_recording(call: ServiceCall) -> None:
    """Record every future episode of a series, not just this one airing.

    Experimental — a separate waipu API (recording-scheduler) from the
    regular recordings one, only ever exercised via its request shapes in
    the waipu web client, never a real response. See api.py's module
    docstring.
    """
    coordinator = _first_coordinator(call.hass)
    station_id = call.data[ATTR_STATION_ID]
    program_id = call.data.get(ATTR_PROGRAM_ID)

    station = coordinator.station(station_id)
    if not station:
        raise ServiceValidationError(f"Sender unbekannt: {station_id}")

    program: Program | None
    if program_id:
        program = next((p for p in station.programs if p.id == program_id), None)
    else:
        program = station.current_program()
    if not program:
        raise ServiceValidationError(
            f"Programm nicht gefunden (Sender '{station_id}'"
            + (f", program_id={program_id}" if program_id else "")
            + ") — evtl. außerhalb des geladenen EPG-Fensters"
        )
    if not program.series_id:
        raise ServiceValidationError(
            f"'{program.title}' hat keine Serien-ID — vermutlich keine "
            "fortlaufende Serie, Serien-Aufnahme nicht möglich"
        )

    try:
        await coordinator.client.create_serial_recording(
            station_id, program.title, program.series_id
        )
    except WaipuPermissionError as err:
        raise HomeAssistantError(
            "Serien-Aufnahme nicht erlaubt (Abo prüfen)"
        ) from err
    except WaipuApiError as err:
        raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
    await coordinator.async_request_refresh()


async def _handle_delete_serial_recording(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    series_id = call.data[ATTR_SERIES_ID]

    try:
        serial = await coordinator.client.get_serial_recording(series_id)
    except WaipuApiError as err:
        raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
    if not serial:
        raise ServiceValidationError(
            f"Keine aktive Serien-Aufnahme für Serie '{series_id}' gefunden"
        )

    try:
        await coordinator.client.delete_serial_recording(
            serial.id,
            delete_finished_recordings=call.data["delete_finished_recordings"],
            delete_running_recordings=call.data["delete_running_recordings"],
        )
    except WaipuApiError as err:
        raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
    await coordinator.async_request_refresh()


async def _handle_launch_on_apple_tv(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    options = coordinator.entry.options
    target = options.get(CONF_APPLE_TV_ENTITY)
    bundle_id = options.get(CONF_WAIPU_BUNDLE_ID) or DEFAULT_WAIPU_BUNDLE_ID

    if not target:
        raise HomeAssistantError(
            "Kein Apple TV in den Waipu-Optionen konfiguriert"
        )

    await call.hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": target,
            "media_content_type": "app",
            "media_content_id": bundle_id,
        },
        blocking=True,
    )


async def _handle_launch_on_android_tv(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    options = coordinator.entry.options
    target = options.get(CONF_ANDROID_TV_REMOTE)
    app_link = options.get(CONF_WAIPU_APP_LINK) or DEFAULT_WAIPU_APP_LINK

    if not target:
        raise HomeAssistantError(
            "Kein Android TV in den Waipu-Optionen konfiguriert"
        )
    if call.hass.states.get(target) is None:
        raise HomeAssistantError(
            f"Android-TV-Remote-Entity nicht gefunden: {target}"
        )

    await call.hass.services.async_call(
        "remote",
        "turn_on",
        {
            "entity_id": target,
            "activity": app_link,
        },
        blocking=True,
    )


async def _handle_switch_channel_on_android_tv(call: ServiceCall) -> None:
    """Switch channel by sending the channel's on-screen number as key presses.

    waipu numbers channels by their position in the account's own channel
    list, exactly as the waipu app displays them (verified: position N in the
    "all channels" list == the Nth entry returned by the API, in order). This
    ONLY works if the waipu app on the Android TV is currently showing the
    same list (all channels vs. favorites-only) as CONF_ANDROID_TV_CHANNEL_VIEW
    — that's an app-side display setting we have no way to read or enforce.
    """
    coordinator = _first_coordinator(call.hass)
    options = coordinator.entry.options
    target = options.get(CONF_ANDROID_TV_REMOTE)
    station_id = call.data[ATTR_STATION_ID]

    if not target:
        raise HomeAssistantError(
            "Kein Android TV in den Waipu-Optionen konfiguriert"
        )
    if call.hass.states.get(target) is None:
        raise HomeAssistantError(
            f"Android-TV-Remote-Entity nicht gefunden: {target}"
        )
    if not coordinator.data:
        raise HomeAssistantError("waipu-Senderdaten noch nicht geladen")

    favorites_view = (
        options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
        == ANDROID_TV_CHANNEL_VIEW_FAVORITES
    )
    countable = _countable_stations(coordinator.entry, coordinator)
    try:
        position = next(
            i for i, s in enumerate(countable, start=1) if s.id == station_id
        )
    except StopIteration as err:
        view_hint = "Favoriten" if favorites_view else "allen Sendern"
        raise ServiceValidationError(
            f"Sender '{station_id}' nicht in der Kanalliste ({view_hint}) "
            "gefunden — unbekannt, ausgeblendet, oder (im Favoriten-Modus) "
            "kein Favorit"
        ) from err

    await call.hass.services.async_call(
        "remote",
        "send_command",
        {
            "entity_id": target,
            "command": list(str(position)),
            "delay_secs": 0.5,
        },
        blocking=True,
    )


async def async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_CREATE_RECORDING):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_RECORDING,
        _handle_create_recording,
        schema=CREATE_RECORDING_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_RECORDING,
        _handle_delete_recording,
        schema=DELETE_RECORDING_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_SERIAL_RECORDING,
        _handle_create_serial_recording,
        schema=CREATE_SERIAL_RECORDING_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_SERIAL_RECORDING,
        _handle_delete_serial_recording,
        schema=DELETE_SERIAL_RECORDING_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LAUNCH_ON_APPLE_TV,
        _handle_launch_on_apple_tv,
        schema=LAUNCH_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LAUNCH_ON_ANDROID_TV,
        _handle_launch_on_android_tv,
        schema=LAUNCH_ANDROID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
        _handle_switch_channel_on_android_tv,
        schema=SWITCH_CHANNEL_ANDROID_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    for service in (
        SERVICE_CREATE_RECORDING,
        SERVICE_DELETE_RECORDING,
        SERVICE_CREATE_SERIAL_RECORDING,
        SERVICE_DELETE_SERIAL_RECORDING,
        SERVICE_LAUNCH_ON_APPLE_TV,
        SERVICE_LAUNCH_ON_ANDROID_TV,
        SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
