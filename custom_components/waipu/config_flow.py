"""Config flow for the waipu.tv integration."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WaipuAuthError, WaipuClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_APPLE_TV_ENTITY,
    CONF_APPLE_TV_REMOTE,
    CONF_DEVICE_ID,
    CONF_REFRESH_TOKEN,
    CONF_SELECTED_CHANNELS,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class WaipuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()

            device_id = str(uuid.uuid4())
            session = async_get_clientsession(self.hass)
            client = WaipuClient(session, device_id=device_id)
            try:
                await client.login(username, password)
            except WaipuAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during waipu login")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=username,
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_DEVICE_ID: device_id,
                        CONF_ACCESS_TOKEN: client.access_token,
                        CONF_REFRESH_TOKEN: client.refresh_token,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        username = entry.data[CONF_USERNAME]

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = WaipuClient(
                session,
                device_id=entry.data.get(CONF_DEVICE_ID, str(uuid.uuid4())),
            )
            try:
                await client.login(username, user_input[CONF_PASSWORD])
            except WaipuAuthError:
                errors["base"] = "invalid_auth"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        **entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_ACCESS_TOKEN: client.access_token,
                        CONF_REFRESH_TOKEN: client.refresh_token,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={"username": username},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return WaipuOptionsFlow(entry)


class WaipuOptionsFlow(OptionsFlow):
    """Options flow: channel selection + optional Apple TV linkage."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        coordinator = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id)
        channel_choices: list[dict[str, str]] = []
        if coordinator and coordinator.data:
            channel_choices = [
                {"value": s.id, "label": s.display_name}
                for s in sorted(
                    (s for s in coordinator.data.stations if s.usable),
                    key=lambda s: s.display_name,
                )
            ]

        current_selection = self.entry.options.get(
            CONF_SELECTED_CHANNELS,
            [c["value"] for c in channel_choices],
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SELECTED_CHANNELS,
                    default=current_selection,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=channel_choices,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_APPLE_TV_ENTITY,
                    default=self.entry.options.get(CONF_APPLE_TV_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player")
                ),
                vol.Optional(
                    CONF_APPLE_TV_REMOTE,
                    default=self.entry.options.get(CONF_APPLE_TV_REMOTE, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="remote")
                ),
                vol.Optional(
                    CONF_WAIPU_BUNDLE_ID,
                    default=self.entry.options.get(
                        CONF_WAIPU_BUNDLE_ID, DEFAULT_WAIPU_BUNDLE_ID
                    ),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
