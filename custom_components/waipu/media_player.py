"""Media player that proxies playback to a configured Apple TV or Android TV.

waipu.tv streams are Widevine-DRM-protected, so Home Assistant cannot
play them directly. This entity therefore acts as a *control surface*:

* ``source_list`` exposes the user's selected channel list
* ``select_source(channel)`` launches the Waipu app on the configured
  Apple TV media_player, or the configured Android TV remote if no Apple TV
  is set (channel-specific deep linking is not supported by the waipu
  client on either platform today; the launch only opens the app)
* media metadata mirrors the currently selected channel's running program
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Program, Station
from .const import (
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    CONF_ANDROID_TV_CHANNEL_VIEW,
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_SELECTED_CHANNELS,
    CONF_WAIPU_APP_LINK,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_WAIPU_APP_LINK,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
)
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WaipuMediaPlayer(coordinator, entry)])


class WaipuMediaPlayer(WaipuEntity, MediaPlayerEntity):
    _attr_name = "Wiedergabe"
    _attr_icon = "mdi:television-play"

    def __init__(
        self, coordinator: WaipuCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.entry.entry_id}_player"
        self._selected_station_id: str | None = None
        # Own device instead of the shared per-entry device every channel
        # sensor/button uses — keeps this one entity out of that ~90-entity
        # device card, in its own small box on the integration page.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    # --- Configuration helpers ----------------------------------------------
    @property
    def _apple_tv_entity(self) -> str | None:
        return self._entry.options.get(CONF_APPLE_TV_ENTITY) or None

    @property
    def _bundle_id(self) -> str:
        return (
            self._entry.options.get(CONF_WAIPU_BUNDLE_ID)
            or DEFAULT_WAIPU_BUNDLE_ID
        )

    @property
    def _android_tv_remote(self) -> str | None:
        return self._entry.options.get(CONF_ANDROID_TV_REMOTE) or None

    @property
    def _app_link(self) -> str:
        return (
            self._entry.options.get(CONF_WAIPU_APP_LINK)
            or DEFAULT_WAIPU_APP_LINK
        )

    # --- Feature/volume mirroring --------------------------------------------
    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = (
            MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
        )
        if self._apple_tv_entity:
            # Apple TV is itself a media_player — full volume control,
            # including an absolute level, can be forwarded to it.
            features |= (
                MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_MUTE
            )
        elif self._android_tv_remote:
            # androidtv_remote only exposes discrete volume up/down/mute
            # keycodes — no absolute level to set or read back.
            features |= (
                MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_MUTE
            )
        return features

    @property
    def volume_level(self) -> float | None:
        if not self._apple_tv_entity:
            return None
        target_state = self.hass.states.get(self._apple_tv_entity)
        return target_state.attributes.get("volume_level") if target_state else None

    @property
    def is_volume_muted(self) -> bool | None:
        if not self._apple_tv_entity:
            return None
        target_state = self.hass.states.get(self._apple_tv_entity)
        return target_state.attributes.get("is_volume_muted") if target_state else None

    # --- Source list --------------------------------------------------------
    @property
    def source_list(self) -> list[str] | None:
        if not self.coordinator.data:
            return None
        stations = [s for s in self.coordinator.data.stations if s.usable]
        if (
            self._entry.options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
            == ANDROID_TV_CHANNEL_VIEW_FAVORITES
        ):
            # Favorites-view mode: follow waipu's own favorite flag live,
            # ignoring any manually saved channel selection.
            stations = [s for s in stations if s.favorite]
        else:
            selected: list[str] | None = self._entry.options.get(
                CONF_SELECTED_CHANNELS
            )
            if selected:
                stations = [s for s in stations if s.id in selected]
            else:
                stations = [s for s in stations if s.favorite]
        return [s.display_name for s in stations]

    @property
    def source(self) -> str | None:
        st = self._current_station()
        return st.display_name if st else None

    # --- Mirror metadata of currently selected channel ----------------------
    def _current_station(self) -> Station | None:
        if not self._selected_station_id:
            return None
        return self.coordinator.station(self._selected_station_id)

    def _current_program(self) -> Program | None:
        st = self._current_station()
        return st.current_program() if st else None

    @property
    def state(self) -> MediaPlayerState:
        if not self._apple_tv_entity and not self._android_tv_remote:
            return MediaPlayerState.OFF
        if self._selected_station_id:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_content_type(self) -> str | None:
        return MediaType.TVSHOW if self._selected_station_id else None

    @property
    def media_title(self) -> str | None:
        program = self._current_program()
        return program.title if program else None

    @property
    def media_series_title(self) -> str | None:
        st = self._current_station()
        return st.display_name if st else None

    @property
    def media_image_url(self) -> str | None:
        program = self._current_program()
        if program and program.preview_image:
            return program.preview_image
        st = self._current_station()
        return st.logo_url(resolution="640x360") if st else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        st = self._current_station()
        program = self._current_program()
        attrs: dict[str, Any] = {}
        if st:
            attrs["station_id"] = st.id
        if program:
            attrs["program_id"] = program.id
            attrs["start_time"] = program.start_time.isoformat()
            attrs["stop_time"] = program.stop_time.isoformat()
            attrs["episode_title"] = program.episode_title
        if self._apple_tv_entity:
            attrs["target_apple_tv"] = self._apple_tv_entity
        if self._android_tv_remote:
            attrs["target_android_tv"] = self._android_tv_remote
        return attrs

    # --- Actions ------------------------------------------------------------
    async def async_select_source(self, source: str) -> None:
        st = self._find_station_by_name(source)
        if not st:
            raise HomeAssistantError(f"Unknown station: {source}")
        self._selected_station_id = st.id
        await self._launch_waipu()
        self.async_write_ha_state()

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        st = self.coordinator.station(media_id) or self._find_station_by_name(
            media_id
        )
        if not st:
            raise HomeAssistantError(f"Unknown station: {media_id}")
        self._selected_station_id = st.id
        await self._launch_waipu()
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self._launch_waipu()

    async def async_turn_off(self) -> None:
        if self._apple_tv_entity:
            await self.hass.services.async_call(
                "media_player",
                "turn_off",
                {"entity_id": self._apple_tv_entity},
                blocking=True,
            )
            return
        if self._android_tv_remote:
            await self.hass.services.async_call(
                "remote",
                "turn_off",
                {"entity_id": self._android_tv_remote},
                blocking=True,
            )
            return
        raise HomeAssistantError(
            "Weder Apple TV noch Android TV in den Waipu-Optionen konfiguriert"
        )

    async def async_volume_up(self) -> None:
        await self._send_volume_key("volume_up", "VOLUME_UP")

    async def async_volume_down(self) -> None:
        await self._send_volume_key("volume_down", "VOLUME_DOWN")

    async def async_mute_volume(self, mute: bool) -> None:
        if self._apple_tv_entity:
            await self.hass.services.async_call(
                "media_player",
                "volume_mute",
                {"entity_id": self._apple_tv_entity, "is_volume_muted": mute},
                blocking=True,
            )
            return
        if self._android_tv_remote:
            # Basic remote key toggles mute — there's no separate on/off
            # keycode, so `mute` is ignored and every call just toggles it.
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {"entity_id": self._android_tv_remote, "command": ["MUTE"]},
                blocking=True,
            )

    async def async_set_volume_level(self, volume: float) -> None:
        if self._apple_tv_entity:
            await self.hass.services.async_call(
                "media_player",
                "volume_set",
                {"entity_id": self._apple_tv_entity, "volume_level": volume},
                blocking=True,
            )
        # Android TV has no absolute-level keycode — VOLUME_SET isn't
        # advertised in supported_features for that backend, so this
        # shouldn't be called in the first place.

    async def _send_volume_key(self, apple_service: str, android_keycode: str) -> None:
        if self._apple_tv_entity:
            await self.hass.services.async_call(
                "media_player",
                apple_service,
                {"entity_id": self._apple_tv_entity},
                blocking=True,
            )
            return
        if self._android_tv_remote:
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {"entity_id": self._android_tv_remote, "command": [android_keycode]},
                blocking=True,
            )

    # --- Helpers ------------------------------------------------------------
    def _find_station_by_name(self, name: str) -> Station | None:
        if not self.coordinator.data:
            return None
        for s in self.coordinator.data.stations:
            if s.display_name == name:
                return s
        return None

    async def _launch_waipu(self) -> None:
        if self._apple_tv_entity:
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": self._apple_tv_entity,
                    "media_content_type": "app",
                    "media_content_id": self._bundle_id,
                },
                blocking=True,
            )
            return
        if self._android_tv_remote:
            await self.hass.services.async_call(
                "remote",
                "turn_on",
                {
                    "entity_id": self._android_tv_remote,
                    "activity": self._app_link,
                },
                blocking=True,
            )
            if self._selected_station_id:
                # remote.turn_on only confirms the TV's power state, not that
                # the waipu app has finished cold-starting and is ready to
                # accept channel-number input — on a cold start (app/TV was
                # off), digits sent too early get ignored and it just settles
                # on whatever channel it last remembered. Give it a moment.
                await asyncio.sleep(2)
                await self._switch_android_channel(self._selected_station_id)
            return
        raise HomeAssistantError(
            "Weder Apple TV noch Android TV in den Waipu-Optionen konfiguriert"
        )

    async def _switch_android_channel(self, station_id: str) -> None:
        """Follow up the app launch with the channel's on-screen number.

        Experimental — see waipu.switch_channel_on_android_tv / the README
        section on Android TV channel switching for the app-view caveat.
        """
        if not self.coordinator.data:
            return
        favorites_view = (
            self._entry.options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
            == ANDROID_TV_CHANNEL_VIEW_FAVORITES
        )
        countable = [
            s
            for s in self.coordinator.data.stations
            if s.usable and (not favorites_view or s.favorite)
        ]
        try:
            position = next(
                i for i, s in enumerate(countable, start=1) if s.id == station_id
            )
        except StopIteration:
            return
        await self.hass.services.async_call(
            "remote",
            "send_command",
            {
                "entity_id": self._android_tv_remote,
                "command": list(str(position)),
                "delay_secs": 0.5,
            },
            blocking=True,
        )
