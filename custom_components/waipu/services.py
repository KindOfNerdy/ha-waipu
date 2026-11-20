"""Services exposed by the waipu.tv integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import Program, WaipuApiError, WaipuPermissionError
from .const import (
    ATTR_AUTOPLAY,
    ATTR_MODE,
    ATTR_POSITION,
    ATTR_PROGRAM_ID,
    ATTR_RECORDING_ID,
    ATTR_REMINDER_ID,
    ATTR_SERIES_ID,
    ATTR_STATION_ID,
    DOMAIN,
    RECORDING_START_MODES,
    RECORDING_START_RESUME,
    SERVICE_ADD_REMINDER,
    SERVICE_CREATE_RECORDING,
    SERVICE_CREATE_SERIAL_RECORDING,
    SERVICE_DELETE_RECORDING,
    SERVICE_DELETE_SERIAL_RECORDING,
    SERVICE_OPEN_PROGRAM_ON_ANDROID_TV,
    SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
    SERVICE_REMOVE_REMINDER,
    SERVICE_RESTART_PROGRAM,
    SERVICE_STOP_RECORDING,
    SERVICE_UPDATE_REMINDER,
)
from .coordinator import first_coordinator
from .media_player import (
    async_open_program,
    async_play_recording,
    async_restart_program,
    current_selected_station_id,
)

_LOGGER = logging.getLogger(__name__)

ADD_REMINDER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_STATION_ID): cv.string,
        # A program (once) or, with series, every episode of its series …
        vol.Optional(ATTR_PROGRAM_ID): cv.string,
        vol.Optional("series", default=False): cv.boolean,
        # … or a time on weekdays (all days if none given).
        vol.Optional("time"): cv.time,
        vol.Optional("days"): cv.weekdays,
        vol.Optional("once", default=False): cv.boolean,
        # Switch the TV at the start; off = only the push.
        vol.Optional("switch", default=True): cv.boolean,
    }
)

UPDATE_REMINDER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_REMINDER_ID): cv.string,
        vol.Optional("enabled"): cv.boolean,
        vol.Optional("switch"): cv.boolean,
        vol.Optional("skip_next"): cv.boolean,
    }
)

REMOVE_REMINDER_SCHEMA = vol.Schema({vol.Required(ATTR_REMINDER_ID): cv.string})

CREATE_RECORDING_SCHEMA = vol.Schema(
    {
        # Optional: defaults to whatever channel this integration currently
        # has tuned (media_player) — see _handle_create_recording.
        vol.Optional(ATTR_STATION_ID): cv.string,
        vol.Optional(ATTR_PROGRAM_ID): cv.string,
    }
)

STOP_RECORDING_SCHEMA = vol.Schema(
    {
        # Optional: defaults to the RECORDING-status recording on whatever
        # channel this integration currently has tuned — see
        # _handle_stop_recording. Handy paired with create_recording (both
        # omitted) for "record a few minutes of whatever's on now".
        vol.Optional(ATTR_RECORDING_ID): cv.string,
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

OPEN_PROGRAM_ANDROID_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATION_ID): cv.string,
        vol.Optional(ATTR_PROGRAM_ID): cv.string,
        vol.Optional(ATTR_AUTOPLAY, default=False): cv.boolean,
    }
)

PLAY_RECORDING_ANDROID_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_RECORDING_ID): cv.string,
        vol.Optional(ATTR_MODE, default=RECORDING_START_RESUME): vol.In(
            RECORDING_START_MODES
        ),
        vol.Optional(ATTR_POSITION): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)


async def _handle_create_recording(call: ServiceCall) -> None:
    coordinator = first_coordinator(call.hass)
    station_id = call.data.get(ATTR_STATION_ID)
    program_id = call.data.get(ATTR_PROGRAM_ID)

    if not station_id:
        station_id = current_selected_station_id(call.hass, coordinator.entry, coordinator)
        if not station_id:
            raise ServiceValidationError(
                "Kein station_id angegeben und aktuell kein Sender über "
                "diese Integration eingestellt (waipu-media_player) — "
                "station_id explizit angeben oder zuerst einen Sender wählen"
            )

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
    coordinator = first_coordinator(call.hass)
    ids: list[str] = call.data[ATTR_RECORDING_ID]
    try:
        await coordinator.client.delete_recordings(ids)
    except WaipuApiError as err:
        raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
    await coordinator.async_request_refresh()


async def _handle_stop_recording(call: ServiceCall) -> None:
    """Stop an actively-recording recording early, keeping what's already
    been captured — pairs with create_recording for "record a few minutes
    of whatever's on now" when both station_id/recording_id are omitted."""
    coordinator = first_coordinator(call.hass)
    recording_id = call.data.get(ATTR_RECORDING_ID)

    if not recording_id:
        station_id = current_selected_station_id(call.hass, coordinator.entry, coordinator)
        if not station_id:
            raise ServiceValidationError(
                "Kein recording_id angegeben und aktuell kein Sender über "
                "diese Integration eingestellt (waipu-media_player) — "
                "recording_id explizit angeben oder zuerst einen Sender wählen"
            )
        running = next(
            (
                r
                for r in (coordinator.data.recordings if coordinator.data else [])
                if r.station_id == station_id and r.status == "RECORDING"
            ),
            None,
        )
        if not running:
            raise ServiceValidationError(
                f"Auf Sender '{station_id}' läuft aktuell keine Aufnahme"
            )
        recording_id = running.id

    try:
        await coordinator.client.stop_recording(recording_id)
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
    coordinator = first_coordinator(call.hass)
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
    coordinator = first_coordinator(call.hass)
    series_id = call.data[ATTR_SERIES_ID]

    try:
        serial = await coordinator.client.get_serial_recording(
            series_id, coordinator.data.recordings if coordinator.data else ()
        )
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


async def _handle_play_recording_on_android_tv(call: ServiceCall) -> None:
    """Open/play a cloud recording on the Android TV via deep link.

    mode: resume (waipu's own resume point), beginning (position 0) or
    details (detail page, no playback). An explicit position (seconds)
    always plays from there.
    """
    coordinator = first_coordinator(call.hass)
    await async_play_recording(
        call.hass,
        coordinator.entry,
        coordinator,
        call.data[ATTR_RECORDING_ID],
        call.data[ATTR_MODE],
        call.data.get(ATTR_POSITION),
    )


async def _handle_open_program_on_android_tv(call: ServiceCall) -> None:
    """Open an EPG program's detail page on the Android TV (or, with
    autoplay, play it). Defaults: the tuned channel, its running program."""
    coordinator = first_coordinator(call.hass)
    station_id = call.data.get(ATTR_STATION_ID) or current_selected_station_id(
        call.hass, coordinator.entry, coordinator
    )
    if not station_id:
        raise ServiceValidationError(
            "Kein station_id angegeben und aktuell kein Sender über diese "
            "Integration eingestellt"
        )
    await async_open_program(
        call.hass,
        coordinator.entry,
        coordinator,
        station_id,
        call.data.get(ATTR_PROGRAM_ID),
        call.data[ATTR_AUTOPLAY],
    )


async def _handle_restart_program(call: ServiceCall) -> None:
    """Start the live program on the TV over from its beginning."""
    coordinator = first_coordinator(call.hass)
    await async_restart_program(call.hass, coordinator.entry, coordinator)


def _reminders(call: ServiceCall):
    return first_coordinator(call.hass).reminders


async def _handle_add_reminder(call: ServiceCall) -> ServiceResponse:
    reminder = _reminders(call).async_add(
        call.data[ATTR_STATION_ID],
        program_id=call.data.get(ATTR_PROGRAM_ID),
        series=call.data["series"],
        at=call.data.get("time"),
        days=call.data.get("days"),
        once=call.data["once"],
        switch=call.data["switch"],
    )
    return {"reminder": dict(reminder)}


async def _handle_update_reminder(call: ServiceCall) -> None:
    _reminders(call).async_update(
        call.data[ATTR_REMINDER_ID],
        enabled=call.data.get("enabled"),
        switch=call.data.get("switch"),
        skip_next=call.data.get("skip_next"),
    )


async def _handle_remove_reminder(call: ServiceCall) -> None:
    _reminders(call).async_remove(call.data[ATTR_REMINDER_ID])


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
        SERVICE_STOP_RECORDING,
        _handle_stop_recording,
        schema=STOP_RECORDING_SCHEMA,
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
        SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        _handle_play_recording_on_android_tv,
        schema=PLAY_RECORDING_ANDROID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_OPEN_PROGRAM_ON_ANDROID_TV,
        _handle_open_program_on_android_tv,
        schema=OPEN_PROGRAM_ANDROID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTART_PROGRAM,
        _handle_restart_program,
        schema=vol.Schema({}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_REMINDER,
        _handle_add_reminder,
        schema=ADD_REMINDER_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_REMINDER,
        _handle_update_reminder,
        schema=UPDATE_REMINDER_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_REMINDER,
        _handle_remove_reminder,
        schema=REMOVE_REMINDER_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    for service in (
        SERVICE_CREATE_RECORDING,
        SERVICE_STOP_RECORDING,
        SERVICE_DELETE_RECORDING,
        SERVICE_CREATE_SERIAL_RECORDING,
        SERVICE_DELETE_SERIAL_RECORDING,
        SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        SERVICE_OPEN_PROGRAM_ON_ANDROID_TV,
        SERVICE_RESTART_PROGRAM,
        SERVICE_ADD_REMINDER,
        SERVICE_UPDATE_REMINDER,
        SERVICE_REMOVE_REMINDER,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
