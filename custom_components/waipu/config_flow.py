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
    ANDROID_TV_CHANNEL_VIEW_ALL,
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    CONF_ACCESS_TOKEN,
    CONF_ANDROID_TV_CHANNEL_VIEW,
    CONF_ANDROID_TV_LAUNCH_DELAY,
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_APPLE_TV_REMOTE,
    CONF_DEVICE_ID,
    CONF_EPG_CACHE_TTL,
    CONF_REFRESH_TOKEN,
    CONF_SELECTED_CHANNELS,
    CONF_WAIPU_APP_LINK,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_ANDROID_TV_CHANNEL_VIEW,
    DEFAULT_ANDROID_TV_LAUNCH_DELAY_SEC,
    DEFAULT_EPG_CACHE_TTL_MIN,
    DEFAULT_WAIPU_APP_LINK,
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

STEP_TV_SETUP_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_APPLE_TV_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="media_player")
        ),
        vol.Optional(CONF_APPLE_TV_REMOTE): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="remote")
        ),
        vol.Optional(CONF_ANDROID_TV_REMOTE): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="remote")
        ),
    }
)


class WaipuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._entry_data: dict[str, Any] = {}

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
                self._entry_data = {
                    CONF_USERNAME: username,
                    CONF_PASSWORD: password,
                    CONF_DEVICE_ID: device_id,
                    CONF_ACCESS_TOKEN: client.access_token,
                    CONF_REFRESH_TOKEN: client.refresh_token,
                }
                return await self.async_step_tv_setup()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_tv_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Optional Apple TV / Android TV pairing, offered right after login.

        Every field here (plus channel filtering and the more advanced
        options) can still be changed later via the integration's
        "Configure" options flow — this step just surfaces the two most
        commonly-needed settings during initial setup instead of leaving
        them undiscoverable behind a settings click.
        """
        if user_input is not None:
            options = {k: v for k, v in user_input.items() if v not in (None, "")}
            return self.async_create_entry(
                title="waipu.tv", data=self._entry_data, options=options
            )

        return self.async_show_form(
            step_id="tv_setup", data_schema=STEP_TV_SETUP_SCHEMA
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
        usable_stations = []
        if coordinator and coordinator.data:
            usable_stations = sorted(
                (s for s in coordinator.data.stations if s.usable),
                key=lambda s: s.display_name,
            )
        channel_choices = [
            {"value": s.id, "label": s.display_name} for s in usable_stations
        ]

        current_selection = self.entry.options.get(CONF_SELECTED_CHANNELS)
        if current_selection is None:
            # Same sensible fallback WaipuCoordinator uses when nothing is
            # saved yet (favorites, else the first 25 usable channels) —
            # pre-checking *everything* here made it too easy to accidentally
            # lock in all ~300+ channels just by submitting the form as-is.
            favorites = [s.id for s in usable_stations if s.favorite]
            current_selection = favorites or [s.id for s in usable_stations][:25]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_APPLE_TV_ENTITY,
                    description={
                        "suggested_value": self.entry.options.get(
                            CONF_APPLE_TV_ENTITY
                        )
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player")
                ),
                vol.Optional(
                    CONF_APPLE_TV_REMOTE,
                    description={
                        "suggested_value": self.entry.options.get(
                            CONF_APPLE_TV_REMOTE
                        )
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="remote")
                ),
                vol.Optional(
                    CONF_WAIPU_BUNDLE_ID,
                    default=self.entry.options.get(
                        CONF_WAIPU_BUNDLE_ID, DEFAULT_WAIPU_BUNDLE_ID
                    ),
                ): str,
                vol.Optional(
                    CONF_ANDROID_TV_REMOTE,
                    description={
                        "suggested_value": self.entry.options.get(
                            CONF_ANDROID_TV_REMOTE
                        )
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="remote")
                ),
                vol.Optional(
                    CONF_WAIPU_APP_LINK,
                    default=self.entry.options.get(
                        CONF_WAIPU_APP_LINK, DEFAULT_WAIPU_APP_LINK
                    ),
                ): str,
                vol.Optional(
                    CONF_ANDROID_TV_CHANNEL_VIEW,
                    default=self.entry.options.get(
                        CONF_ANDROID_TV_CHANNEL_VIEW,
                        DEFAULT_ANDROID_TV_CHANNEL_VIEW,
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            ANDROID_TV_CHANNEL_VIEW_ALL,
                            ANDROID_TV_CHANNEL_VIEW_FAVORITES,
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="android_tv_channel_view",
                    )
                ),
                vol.Optional(
                    CONF_ANDROID_TV_LAUNCH_DELAY,
                    default=self.entry.options.get(
                        CONF_ANDROID_TV_LAUNCH_DELAY,
                        DEFAULT_ANDROID_TV_LAUNCH_DELAY_SEC,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=15,
                        step=0.5,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_EPG_CACHE_TTL,
                    default=self.entry.options.get(
                        CONF_EPG_CACHE_TTL, DEFAULT_EPG_CACHE_TTL_MIN
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=180,
                        step=5,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
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
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
