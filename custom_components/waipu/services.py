"""Services exposed by the waipu.tv integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import WaipuApiError, WaipuPermissionError
from .const import (
    ATTR_PROGRAM_ID,
    ATTR_RECORDING_ID,
    ATTR_STATION_ID,
    CONF_APPLE_TV_ENTITY,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
    SERVICE_CREATE_RECORDING,
    SERVICE_DELETE_RECORDING,
    SERVICE_LAUNCH_ON_APPLE_TV,
)
from .coordinator import WaipuCoordinator

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

LAUNCH_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_STATION_ID): cv.string,
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
        SERVICE_LAUNCH_ON_APPLE_TV,
        _handle_launch_on_apple_tv,
        schema=LAUNCH_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    for service in (
        SERVICE_CREATE_RECORDING,
        SERVICE_DELETE_RECORDING,
        SERVICE_LAUNCH_ON_APPLE_TV,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
