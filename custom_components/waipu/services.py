"""Services exposed by the waipu.tv integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import Program, WaipuApiError, WaipuPermissionError
from .const import (
    ATTR_MODE,
    ATTR_POSITION,
    ATTR_PROGRAM_ID,
    ATTR_RECORDING_ID,
    ATTR_SERIES_ID,
    ATTR_STATION_ID,
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_WAIPU_APP_LINK,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_WAIPU_APP_LINK,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
    RECORDING_START_MODES,
    RECORDING_START_RESUME,
    RECORDING_WATCHABLE_STATUSES,
    SERVICE_CREATE_RECORDING,
    SERVICE_CREATE_SERIAL_RECORDING,
    SERVICE_DELETE_RECORDING,
    SERVICE_DELETE_SERIAL_RECORDING,
    SERVICE_LAUNCH_ON_ANDROID_TV,
    SERVICE_LAUNCH_ON_APPLE_TV,
    SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
    SERVICE_STOP_RECORDING,
    SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
    waipu_recording_link,
    waipu_station_link,
)
from .coordinator import WaipuCoordinator
from .media_player import async_open_android_link, current_selected_station_id

_LOGGER = logging.getLogger(__name__)

CREATE_RECORDING_SCHEMA = vol.Schema(
    {
        # Optional: defaults to whatever channel this integration currently
        # has tuned (media_player/select) — see _handle_create_recording.
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

PLAY_RECORDING_ANDROID_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_RECORDING_ID): cv.string,
        vol.Optional(ATTR_MODE, default=RECORDING_START_RESUME): vol.In(
            RECORDING_START_MODES
        ),
        vol.Optional(ATTR_POSITION): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)


def _first_coordinator(hass: HomeAssistant) -> WaipuCoordinator:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError("waipu.tv integration is not loaded")
    return entries[0].runtime_data


async def _handle_create_recording(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    station_id = call.data.get(ATTR_STATION_ID)
    program_id = call.data.get(ATTR_PROGRAM_ID)

    if not station_id:
        station_id = current_selected_station_id(call.hass, coordinator.entry, coordinator)
        if not station_id:
            raise ServiceValidationError(
                "Kein station_id angegeben und aktuell kein Sender über "
                "diese Integration eingestellt (media_player/select) — "
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
    coordinator = _first_coordinator(call.hass)
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
    coordinator = _first_coordinator(call.hass)
    recording_id = call.data.get(ATTR_RECORDING_ID)

    if not recording_id:
        station_id = current_selected_station_id(call.hass, coordinator.entry, coordinator)
        if not station_id:
            raise ServiceValidationError(
                "Kein recording_id angegeben und aktuell kein Sender über "
                "diese Integration eingestellt (media_player/select) — "
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


def _android_tv_target(coordinator: WaipuCoordinator, hass: HomeAssistant) -> str:
    """The configured androidtv_remote entity, or a readable error."""
    target = coordinator.entry.options.get(CONF_ANDROID_TV_REMOTE)
    if not target:
        raise HomeAssistantError(
            "Kein Android TV in den Waipu-Optionen konfiguriert"
        )
    if hass.states.get(target) is None:
        raise HomeAssistantError(
            f"Android-TV-Remote-Entity nicht gefunden: {target}"
        )
    return target


def _known_station_id(coordinator: WaipuCoordinator, station_id: str) -> str:
    if not coordinator.data:
        raise HomeAssistantError("waipu-Senderdaten noch nicht geladen")
    if not coordinator.station(station_id):
        raise ServiceValidationError(f"Sender unbekannt: {station_id}")
    return station_id


async def _tune_android_tv(
    hass: HomeAssistant, coordinator: WaipuCoordinator, target: str, station_id: str
) -> None:
    """Deep-link the TV to `station_id` and let media_player/select follow."""
    coordinator.selected_station_id = station_id
    coordinator.async_update_listeners()
    await async_open_android_link(hass, target, waipu_station_link(station_id))


async def _handle_launch_on_android_tv(call: ServiceCall) -> None:
    coordinator = _first_coordinator(call.hass)
    target = _android_tv_target(coordinator, call.hass)
    station_id = call.data.get(ATTR_STATION_ID)
    if station_id:
        await _tune_android_tv(
            call.hass, coordinator, target, _known_station_id(coordinator, station_id)
        )
        return
    app_link = (
        coordinator.entry.options.get(CONF_WAIPU_APP_LINK) or DEFAULT_WAIPU_APP_LINK
    )
    await async_open_android_link(call.hass, target, app_link)


async def _handle_switch_channel_on_android_tv(call: ServiceCall) -> None:
    """Switch channel via waipu's waipu://tv?id=<station> deep link.

    Works from a cold start and while waipu is already running, independent
    of the channel order/view in the app (verified live, see const.py).
    """
    coordinator = _first_coordinator(call.hass)
    target = _android_tv_target(coordinator, call.hass)
    station_id = _known_station_id(coordinator, call.data[ATTR_STATION_ID])
    await _tune_android_tv(call.hass, coordinator, target, station_id)


async def _handle_play_recording_on_android_tv(call: ServiceCall) -> None:
    """Open/play a cloud recording on the Android TV via deep link.

    mode: resume (waipu's own resume point), beginning (position 0) or
    details (detail page, no playback). An explicit position (seconds)
    always plays from there.
    """
    coordinator = _first_coordinator(call.hass)
    target = _android_tv_target(coordinator, call.hass)
    recording_id = call.data[ATTR_RECORDING_ID]
    if not coordinator.data:
        raise HomeAssistantError("waipu-Aufnahmedaten noch nicht geladen")
    recording = next(
        (r for r in coordinator.data.recordings if r.id == recording_id), None
    )
    if recording is None:
        raise ServiceValidationError(f"Aufnahme unbekannt: {recording_id}")
    if recording.status not in RECORDING_WATCHABLE_STATUSES:
        raise ServiceValidationError(
            f"Aufnahme '{recording.title}' ist noch nicht abspielbar "
            f"(Status {recording.status})"
        )
    link = waipu_recording_link(
        recording_id, call.data[ATTR_MODE], call.data.get(ATTR_POSITION)
    )
    await async_open_android_link(call.hass, target, link)


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
    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
        _handle_play_recording_on_android_tv,
        schema=PLAY_RECORDING_ANDROID_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    for service in (
        SERVICE_CREATE_RECORDING,
        SERVICE_STOP_RECORDING,
        SERVICE_DELETE_RECORDING,
        SERVICE_CREATE_SERIAL_RECORDING,
        SERVICE_DELETE_SERIAL_RECORDING,
        SERVICE_LAUNCH_ON_APPLE_TV,
        SERVICE_LAUNCH_ON_ANDROID_TV,
        SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV,
        SERVICE_PLAY_RECORDING_ON_ANDROID_TV,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
