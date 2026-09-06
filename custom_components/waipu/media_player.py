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
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .api import Program, Station
from .const import (
    ANDROID_TV_CHANNEL_VIEW_FAVORITES,
    ANDROID_WAIPU_PACKAGE_ID,
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


def visible_stations(
    entry: ConfigEntry, coordinator: WaipuCoordinator
) -> list[Station]:
    """The channel list respecting Channel-number-basis / Visible channels.

    Shared by the media_player's source_list and the channel select entity
    so the two stay in sync by construction.
    """
    if not coordinator.data:
        return []
    stations = [s for s in coordinator.data.stations if s.usable]
    if (
        entry.options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
        == ANDROID_TV_CHANNEL_VIEW_FAVORITES
    ):
        return [s for s in stations if s.favorite]
    selected: list[str] | None = entry.options.get(CONF_SELECTED_CHANNELS)
    if selected:
        return [s for s in stations if s.id in selected]
    return [s for s in stations if s.favorite]


def target_entity(entry: ConfigEntry) -> str | None:
    """The real TV entity this config targets — Apple TV media_player if
    set, else the Android TV remote. Shared so media_player and select can
    both check/track the same entity's live state."""
    return (
        entry.options.get(CONF_APPLE_TV_ENTITY)
        or entry.options.get(CONF_ANDROID_TV_REMOTE)
        or None
    )


def is_target_off(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Whether the configured TV is off, per its own real reported state.

    Deliberately not tracked as a flag we flip ourselves — that missed the
    TV being turned off some other way (its own remote, another
    automation, ...). Reading the real entity's state here means it's
    always correct, and the state-change listener in WaipuMediaPlayer /
    WaipuChannelSelect just has to trigger a re-render, not track truth.
    """
    target = target_entity(entry)
    if not target:
        return True
    target_state = hass.states.get(target)
    return target_state is None or target_state.state in (
        "off",
        "unavailable",
        "unknown",
    )


def is_waipu_active_on_android(hass: HomeAssistant, android_tv_remote: str) -> bool:
    """Whether waipu is the current foreground app, per androidtv_remote's
    own current_activity attribute (RemoteEntityFeature.ACTIVITY).

    Only tells us waipu is open — not which channel. Used to fix the state
    showing "idle" when waipu was actually started some other way (its own
    remote, another automation, ...), the same live-derivation principle
    as is_target_off.
    """
    state = hass.states.get(android_tv_remote)
    if not state:
        return False
    current_activity = state.attributes.get("current_activity") or ""
    return ANDROID_WAIPU_PACKAGE_ID in current_activity


async def async_launch_waipu(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WaipuCoordinator,
    station_id: str | None,
) -> None:
    """Launch waipu, and switch to `station_id` on Android TV if given.

    Shared by the media_player entity and the channel select entity so
    "launch + optionally switch channel" only has one implementation.
    """
    options = entry.options
    apple_tv_entity = options.get(CONF_APPLE_TV_ENTITY) or None
    if apple_tv_entity:
        bundle_id = options.get(CONF_WAIPU_BUNDLE_ID) or DEFAULT_WAIPU_BUNDLE_ID
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": apple_tv_entity,
                "media_content_type": "app",
                "media_content_id": bundle_id,
            },
            blocking=True,
        )
        return
    android_tv_remote = options.get(CONF_ANDROID_TV_REMOTE) or None
    if android_tv_remote:
        app_link = options.get(CONF_WAIPU_APP_LINK) or DEFAULT_WAIPU_APP_LINK
        await hass.services.async_call(
            "remote",
            "turn_on",
            {"entity_id": android_tv_remote, "activity": app_link},
            blocking=True,
        )
        if station_id:
            # remote.turn_on only confirms the TV's power state, not that
            # the waipu app has finished cold-starting and is ready to
            # accept channel-number input — on a cold start (app/TV was
            # off), digits sent too early get ignored. Give it a moment.
            await asyncio.sleep(2)
            await _switch_android_channel(
                hass, entry, coordinator, android_tv_remote, station_id
            )
        return
    raise HomeAssistantError(
        "Weder Apple TV noch Android TV in den Waipu-Optionen konfiguriert"
    )


async def _switch_android_channel(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WaipuCoordinator,
    android_tv_remote: str,
    station_id: str,
) -> None:
    """Send the channel's on-screen number as number-key presses.

    Experimental — see waipu.switch_channel_on_android_tv / the README
    section on Android TV channel switching for the app-view caveat.
    """
    if not coordinator.data:
        return
    favorites_view = (
        entry.options.get(CONF_ANDROID_TV_CHANNEL_VIEW)
        == ANDROID_TV_CHANNEL_VIEW_FAVORITES
    )
    countable = [
        s
        for s in coordinator.data.stations
        if s.usable and (not favorites_view or s.favorite)
    ]
    try:
        position = next(
            i for i, s in enumerate(countable, start=1) if s.id == station_id
        )
    except StopIteration:
        return
    await hass.services.async_call(
        "remote",
        "send_command",
        {
            "entity_id": android_tv_remote,
            "command": list(str(position)),
            "delay_secs": 0.5,
        },
        blocking=True,
    )


class WaipuMediaPlayer(WaipuEntity, MediaPlayerEntity):
    _attr_name = "Wiedergabe"
    _attr_icon = "mdi:television-play"

    def __init__(
        self, coordinator: WaipuCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.entry.entry_id}_player"
        # Own device instead of the shared per-entry device every channel
        # sensor/button uses — keeps this one entity out of that ~90-entity
        # device card, in its own small box on the integration page.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="waipu Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        target = target_entity(self._entry)
        if target:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [target], self._handle_target_state_event
                )
            )

    @callback
    def _handle_target_state_event(
        self, event: Event[EventStateChangedData]
    ) -> None:
        # Re-render on any change of the real TV's state, so turning it off
        # some other way (its own remote, another automation, ...) is
        # reflected here too — state/​_current_station read live target
        # state directly rather than a flag we'd have to keep in sync.
        if self._android_tv_remote:
            # TEMPORARY debug aid — confirms current_activity actually
            # reflects app switches on this setup. Remove once reviewed.
            new_state = event.data.get("new_state")
            _LOGGER.warning(
                "DEBUG target state change: state=%s current_activity=%r",
                new_state.state if new_state else None,
                new_state.attributes.get("current_activity") if new_state else None,
            )
        self.async_write_ha_state()

    # --- Configuration helpers ----------------------------------------------
    @property
    def _apple_tv_entity(self) -> str | None:
        return self._entry.options.get(CONF_APPLE_TV_ENTITY) or None

    @property
    def _android_tv_remote(self) -> str | None:
        return self._entry.options.get(CONF_ANDROID_TV_REMOTE) or None

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
        return [
            s.display_name for s in visible_stations(self._entry, self.coordinator)
        ]

    @property
    def source(self) -> str | None:
        st = self._current_station()
        return st.display_name if st else None

    # --- Mirror metadata of currently selected channel ----------------------
    def _current_station(self) -> Station | None:
        if is_target_off(self.hass, self._entry) or not self.coordinator.selected_station_id:
            return None
        return self.coordinator.station(self.coordinator.selected_station_id)

    def _current_program(self) -> Program | None:
        st = self._current_station()
        return st.current_program() if st else None

    @property
    def state(self) -> MediaPlayerState:
        if is_target_off(self.hass, self._entry):
            return MediaPlayerState.OFF
        if self.coordinator.selected_station_id:
            return MediaPlayerState.PLAYING
        if self._android_tv_remote and is_waipu_active_on_android(
            self.hass, self._android_tv_remote
        ):
            # waipu was started some other way (its own remote, another
            # automation, ...) — we don't know which channel, but we do
            # know it's not idle.
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_content_type(self) -> str | None:
        return MediaType.TVSHOW if self._current_station() else None

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
        await self._launch_waipu(st.id)

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        st = self.coordinator.station(media_id) or self._find_station_by_name(
            media_id
        )
        if not st:
            raise HomeAssistantError(f"Unknown station: {media_id}")
        await self._launch_waipu(st.id)

    async def async_turn_on(self) -> None:
        # Restores whichever channel was selected before the last turn_off
        # (coordinator.selected_station_id is preserved across turn_off —
        # "off" itself is now derived from the real TV's live state, not a
        # flag) — select_source overrides it as usual if the user picks a
        # different channel instead of just turning on.
        await self._launch_waipu(self.coordinator.selected_station_id)

    async def async_turn_off(self) -> None:
        if self._apple_tv_entity:
            await self.hass.services.async_call(
                "media_player",
                "turn_off",
                {"entity_id": self._apple_tv_entity},
                blocking=True,
            )
        elif self._android_tv_remote:
            await self.hass.services.async_call(
                "remote",
                "turn_off",
                {"entity_id": self._android_tv_remote},
                blocking=True,
            )
        else:
            raise HomeAssistantError(
                "Weder Apple TV noch Android TV in den Waipu-Optionen konfiguriert"
            )
        self.async_write_ha_state()

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

    async def _launch_waipu(self, station_id: str | None) -> None:
        """Launch waipu and (for Android TV) switch to `station_id`.

        Updates the shared coordinator.selected_station_id via
        async_update_listeners() so this entity and the channel select
        entity stay in sync, whichever one triggered the change.
        """
        self.coordinator.selected_station_id = station_id
        self.coordinator.async_update_listeners()
        await async_launch_waipu(self.hass, self._entry, self.coordinator, station_id)
