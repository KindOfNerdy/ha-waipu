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
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WaipuAuthError, WaipuClient
from .const import (
    CHANNEL_SOURCE_ALL,
    CHANNEL_SOURCE_FAVORITES,
    CONF_ACCESS_TOKEN,
    CONF_CHANNEL_SOURCE,
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_APPLE_TV_REMOTE,
    CONF_CAST_ENTITY,
    CONF_DEVICE_ID,
    CONF_EPG_CACHE_TTL,
    CONF_REFRESH_TOKEN,
    CONF_SELECTED_CHANNELS,
    CONF_WAIPU_APP_LINK,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_CHANNEL_SOURCE,
    DEFAULT_EPG_CACHE_TTL_MIN,
    DEFAULT_WAIPU_APP_LINK,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
    CONF_TV_PLATFORM,
    TV_PLATFORM_ANDROID,
    TV_PLATFORM_APPLE,
    TV_PLATFORM_NONE,
    TV_PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

# Options each TV platform owns; picking a platform drops the other's keys.
PLATFORM_OPTIONS: dict[str, tuple[str, ...]] = {
    TV_PLATFORM_ANDROID: (CONF_ANDROID_TV_REMOTE, CONF_WAIPU_APP_LINK, CONF_CAST_ENTITY),
    TV_PLATFORM_APPLE: (CONF_APPLE_TV_ENTITY, CONF_APPLE_TV_REMOTE, CONF_WAIPU_BUNDLE_ID),
}


def tv_platform_of(options: dict[str, Any]) -> str:
    """The configured TV platform, derived from the options that are set.

    Apple TV wins if (from older versions) both are set, matching how the
    media_player has always picked its target.
    """
    if options.get(CONF_APPLE_TV_ENTITY):
        return TV_PLATFORM_APPLE
    if options.get(CONF_ANDROID_TV_REMOTE):
        return TV_PLATFORM_ANDROID
    return TV_PLATFORM_NONE


def _tv_platform_field(default: str) -> dict:
    return {
        vol.Required(CONF_TV_PLATFORM, default=default): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(TV_PLATFORMS),
                mode=selector.SelectSelectorMode.LIST,
                translation_key="tv_platform",
            )
        )
    }


def _android_tv_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_ANDROID_TV_REMOTE,
                description={"suggested_value": options.get(CONF_ANDROID_TV_REMOTE)},
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="remote")),
            vol.Optional(
                CONF_WAIPU_APP_LINK,
                default=options.get(CONF_WAIPU_APP_LINK, DEFAULT_WAIPU_APP_LINK),
            ): str,
            vol.Optional(
                CONF_CAST_ENTITY,
                description={"suggested_value": options.get(CONF_CAST_ENTITY)},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", integration="cast")
            ),
        }
    )


def _apple_tv_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_APPLE_TV_ENTITY,
                description={"suggested_value": options.get(CONF_APPLE_TV_ENTITY)},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Optional(
                CONF_APPLE_TV_REMOTE,
                description={"suggested_value": options.get(CONF_APPLE_TV_REMOTE)},
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="remote")),
            vol.Optional(
                CONF_WAIPU_BUNDLE_ID,
                default=options.get(CONF_WAIPU_BUNDLE_ID, DEFAULT_WAIPU_BUNDLE_ID),
            ): str,
        }
    )


def _clean(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if v not in (None, "")}


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
        """Which TV to control, offered right after login; its own fields
        follow on the next page. Everything can be changed later under
        "Configure"."""
        if user_input is not None:
            platform = user_input[CONF_TV_PLATFORM]
            if platform == TV_PLATFORM_ANDROID:
                return await self.async_step_android_tv()
            if platform == TV_PLATFORM_APPLE:
                return await self.async_step_apple_tv()
            return self._create({})

        return self.async_show_form(
            step_id="tv_setup",
            data_schema=vol.Schema(_tv_platform_field(TV_PLATFORM_ANDROID)),
        )

    async def async_step_android_tv(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self._create(_clean(user_input))
        return self.async_show_form(
            step_id="android_tv", data_schema=_android_tv_schema({})
        )

    async def async_step_apple_tv(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self._create(_clean(user_input))
        return self.async_show_form(
            step_id="apple_tv", data_schema=_apple_tv_schema({})
        )

    def _create(self, options: dict[str, Any]) -> ConfigFlowResult:
        return self.async_create_entry(
            title="waipu.tv", data=self._entry_data, options=options
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
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlowWithReload:
        return WaipuOptionsFlow(entry)


class WaipuOptionsFlow(OptionsFlowWithReload):
    """Options flow, one page per concern: TV platform + channel source +
    EPG cache, then the chosen TV's own fields, then (for "all channels")
    the visible-channel picker."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry
        self._options: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            platform = user_input.pop(CONF_TV_PLATFORM)
            # Start from the stored options minus every platform's keys;
            # the chosen platform's page adds its own back.
            self._options = {
                k: v
                for k, v in self.entry.options.items()
                if not any(k in keys for keys in PLATFORM_OPTIONS.values())
            }
            self._options.update(user_input)
            if platform == TV_PLATFORM_ANDROID:
                return await self.async_step_android_tv()
            if platform == TV_PLATFORM_APPLE:
                return await self.async_step_apple_tv()
            return await self._async_after_tv()

        options = self.entry.options
        schema = vol.Schema(
            {
                **_tv_platform_field(tv_platform_of(options)),
                vol.Optional(
                    CONF_CHANNEL_SOURCE,
                    default=options.get(CONF_CHANNEL_SOURCE, DEFAULT_CHANNEL_SOURCE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[CHANNEL_SOURCE_FAVORITES, CHANNEL_SOURCE_ALL],
                        mode=selector.SelectSelectorMode.LIST,
                        translation_key="channel_source",
                    )
                ),
                vol.Optional(
                    CONF_EPG_CACHE_TTL,
                    default=options.get(CONF_EPG_CACHE_TTL, DEFAULT_EPG_CACHE_TTL_MIN),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=180,
                        step=5,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_android_tv(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options.update(_clean(user_input))
            return await self._async_after_tv()
        return self.async_show_form(
            step_id="android_tv", data_schema=_android_tv_schema(self.entry.options)
        )

    async def async_step_apple_tv(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options.update(_clean(user_input))
            return await self._async_after_tv()
        return self.async_show_form(
            step_id="apple_tv", data_schema=_apple_tv_schema(self.entry.options)
        )

    async def _async_after_tv(self) -> ConfigFlowResult:
        if self._options.get(CONF_CHANNEL_SOURCE) == CHANNEL_SOURCE_ALL:
            return await self.async_step_channels()
        # Favorites mode ignores the manual selection; it stays in the
        # options (carried over above) so switching back restores it.
        return self.async_create_entry(title="", data=self._options)

    async def async_step_channels(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="", data={**self._options, **user_input}
            )

        coordinator = getattr(self.entry, "runtime_data", None)
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
        return self.async_show_form(step_id="channels", data_schema=schema)
