"""Media player that proxies playback to a configured Apple TV or Android TV.

waipu.tv streams are Widevine-DRM-protected, so Home Assistant cannot
play them directly. This entity therefore acts as a *control surface*:

* ``source_list`` exposes the user's selected channel list
* ``select_source(channel)`` tunes the configured Android TV straight to
  the channel via waipu's ``waipu://tv?id=<station>`` deep link, or — if an
  Apple TV is configured instead — only launches the waipu app there (no
  known tvOS deep links)
* media metadata mirrors the currently selected channel's running program
"""
from __future__ import annotations

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
    ANDROID_WAIPU_PACKAGE_ID,
    CHANNEL_SOURCE_FAVORITES,
    CONF_ANDROID_TV_REMOTE,
    CONF_APPLE_TV_ENTITY,
    CONF_CHANNEL_SOURCE,
    CONF_SELECTED_CHANNELS,
    CONF_WAIPU_APP_LINK,
    CONF_WAIPU_BUNDLE_ID,
    DEFAULT_WAIPU_APP_LINK,
    DEFAULT_WAIPU_BUNDLE_ID,
    DOMAIN,
    waipu_station_link,
)
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = entry.runtime_data
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
        entry.options.get(CONF_CHANNEL_SOURCE)
        == CHANNEL_SOURCE_FAVORITES
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


def current_selected_station_id(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: WaipuCoordinator
) -> str | None:
    """The station id waipu is presumed to currently show, or None.

    None whenever the TV is off, nothing's been selected yet, or — Android
    TV only, since current_activity is the only external signal we have —
    a different app (Netflix, ...) has since taken over. Checking
    current_activity here (not just as a fallback for the "nothing
    selected yet" case) is what makes switching *away* from waipu clear
    the shown channel, not just switching *to* it.
    """
    if is_target_off(hass, entry):
        return None
    station_id = coordinator.selected_station_id
    if not station_id:
        return None
    android_tv_remote = entry.options.get(CONF_ANDROID_TV_REMOTE) or None
    if android_tv_remote and not is_waipu_active_on_android(hass, android_tv_remote):
        return None
    return station_id


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


async def async_open_android_link(
    hass: HomeAssistant, android_tv_remote: str, link: str
) -> None:
    """Open a waipu deep link on the Android TV (androidtv_remote).

    remote.turn_on with an activity both wakes the TV and opens the link;
    waipu handles it on a cold start and while already running alike.
    """
    await hass.services.async_call(
        "remote",
        "turn_on",
        {"entity_id": android_tv_remote, "activity": link},
        blocking=True,
    )


async def async_launch_waipu(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WaipuCoordinator,
    station_id: str | None,
) -> None:
    """Launch waipu, tuned to `station_id` on Android TV if given.

    Shared by the media_player entity and the channel select entity so
    "launch + optionally switch channel" only has one implementation.
    Apple TV only opens the app (no known tvOS deep links).
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
        if station_id:
            await async_open_android_link(
                hass, android_tv_remote, waipu_station_link(station_id)
            )
            return
        if is_waipu_active_on_android(hass, android_tv_remote):
            # Already in the foreground and no channel asked for —
            # re-opening the app link would only reset its view.
            return
        app_link = options.get(CONF_WAIPU_APP_LINK) or DEFAULT_WAIPU_APP_LINK
        await async_open_android_link(hass, android_tv_remote, app_link)
        return
    raise HomeAssistantError(
        "Weder Apple TV noch Android TV in den Waipu-Optionen konfiguriert"
    )


def neighbor_station_id(
    stations: list[Station], current_id: str | None, direction: int
) -> str | None:
    """The station `direction` steps away from `current_id`, wrapping around.

    With no (or an unknown) current station, "next" starts at the first
    and "previous" at the last one.
    """
    if not stations:
        return None
    ids = [s.id for s in stations]
    if current_id not in ids:
        return ids[0] if direction > 0 else ids[-1]
    return ids[(ids.index(current_id) + direction) % len(ids)]


class WaipuMediaPlayer(WaipuEntity, MediaPlayerEntity):
    # None, not "Wiedergabe" — this entity *is* the "waipu Wiedergabe"
    # device's main feature, so its own name would otherwise double up
    # with the device name (has_entity_name displays "<device> <name>").
    _attr_name = None
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
            translation_key="player",
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
                # "next/previous track" are HA's generic step primitives —
                # mapped to the neighboring channel in source_list, tuned
                # via deep link. Android TV only: tvOS has no known deep
                # links, so Apple TV can't switch channels at all.
                | MediaPlayerEntityFeature.NEXT_TRACK
                | MediaPlayerEntityFeature.PREVIOUS_TRACK
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
        station_id = current_selected_station_id(self.hass, self._entry, self.coordinator)
        return self.coordinator.station(station_id) if station_id else None

    def _current_program(self) -> Program | None:
        st = self._current_station()
        return st.current_program() if st else None

    @property
    def state(self) -> MediaPlayerState:
        if is_target_off(self.hass, self._entry):
            return MediaPlayerState.OFF
        if current_selected_station_id(self.hass, self._entry, self.coordinator):
            return MediaPlayerState.PLAYING
        if self._android_tv_remote and is_waipu_active_on_android(
            self.hass, self._android_tv_remote
        ):
            # waipu is open (started some other way — its own remote,
            # another automation, ...) but we don't know which channel.
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

    async def async_media_next_track(self) -> None:
        await self._step_channel(1)

    async def async_media_previous_track(self) -> None:
        await self._step_channel(-1)

    async def _step_channel(self, direction: int) -> None:
        """Tune to the neighboring channel in source_list (wrapping around)."""
        if not self._android_tv_remote:
            return
        station_id = neighbor_station_id(
            visible_stations(self._entry, self.coordinator),
            self.coordinator.selected_station_id,
            direction,
        )
        if station_id:
            await self._launch_waipu(station_id)

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
