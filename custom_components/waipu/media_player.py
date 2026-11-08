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
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.media_player import (
    BrowseError,
    BrowseMedia,
    MediaClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .api import Program, Recording, Station, WaipuApiError, WaipuPermissionError
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
    RECORDING_START_BEGINNING,
    RECORDING_START_RESUME,
    RECORDING_WATCHABLE_STATUSES,
    WAIPU_EPG_LINK,
    WAIPU_RECORDINGS_LINK,
    waipu_program_link,
    waipu_recording_link,
    waipu_station_link,
)
from .coordinator import WaipuCoordinator
from .entity import WaipuProgramEntity

_LOGGER = logging.getLogger(__name__)

# Media browser: content ids/types. Recordings get their own type so
# play_media can tell a recording id from a station id.
MEDIA_TYPE_RECORDING = "waipu_recording"
# EPG program from the "Programm" folder; content id "<station_id>/<program_id>".
MEDIA_TYPE_PROGRAM = "waipu_program"
# Action on an upcoming program; content id "<action>/<station_id>/<program_id>".
MEDIA_TYPE_PROGRAM_ACTION = "waipu_program_action"
PROGRAM_ACTION_DETAILS = "details"
PROGRAM_ACTION_RECORD = "record"
PROGRAM_ACTION_RECORD_SERIES = "record_series"
PROGRAM_ACTION_DELETE = "delete"
PROGRAM_ACTION_END_SERIES = "end_series"
# An upcoming program's action folder: "program:<station_id>/<program_id>".
BROWSE_PROGRAM_PREFIX = "program:"
# Icons for the program actions (Material Design Icons, see browse_icons/),
# served to the media browser through HA's browse-image proxy.
MEDIA_TYPE_ICON = "waipu_icon"
_ICON_DIR = Path(__file__).parent / "browse_icons"
# Recording statuses that mean "this program is already being recorded".
_PLANNED_STATUSES = ("SCHEDULED", "RECORDING")
_PROGRAM_LABELS = {
    "de": {
        "now": "Jetzt",
        "planned": "⏺ geplant",
        PROGRAM_ACTION_DETAILS: "Details am TV",
        PROGRAM_ACTION_RECORD: "Folge aufnehmen",
        PROGRAM_ACTION_RECORD_SERIES: "Serie aufnehmen",
        PROGRAM_ACTION_DELETE: "Aufnahme abbrechen",
        PROGRAM_ACTION_END_SERIES: "Serien-Aufnahme beenden",
    },
    "en": {
        "now": "Now",
        "planned": "⏺ scheduled",
        PROGRAM_ACTION_DETAILS: "Details on the TV",
        PROGRAM_ACTION_RECORD: "Record episode",
        PROGRAM_ACTION_RECORD_SERIES: "Record series",
        PROGRAM_ACTION_DELETE: "Cancel recording",
        PROGRAM_ACTION_END_SERIES: "Stop series recording",
    },
}
BROWSE_ROOT = "waipu"
BROWSE_RECORDINGS = "recordings"
BROWSE_CHANNELS = "channels"
BROWSE_GUIDE = "guide"
# Prefix for one channel's program list: "guide:<station_id>".
BROWSE_GUIDE_PREFIX = "guide:"
# Prefix for a series folder's content id: "series:<series_id>".
BROWSE_SERIES_PREFIX = "series:"
# Sources = sections of the waipu app (channels live in the media browser).
SOURCE_LIVE = "live"
SOURCE_RECORDINGS = "recordings"
SOURCE_EPG = "epg"
_SOURCE_LABELS = {
    "de": {SOURCE_LIVE: "Live-TV", SOURCE_RECORDINGS: "Aufnahmen", SOURCE_EPG: "EPG"},
    "en": {SOURCE_LIVE: "Live TV", SOURCE_RECORDINGS: "Recordings", SOURCE_EPG: "EPG"},
}
_BROWSE_TITLES = {
    "de": {
        BROWSE_ROOT: "waipu.tv",
        BROWSE_RECORDINGS: "Aufnahmen",
        BROWSE_CHANNELS: "Sender",
        BROWSE_GUIDE: "Programm",
    },
    "en": {
        BROWSE_ROOT: "waipu.tv",
        BROWSE_RECORDINGS: "Recordings",
        BROWSE_CHANNELS: "Channels",
        BROWSE_GUIDE: "TV guide",
    },
}


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


async def async_play_recording(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WaipuCoordinator,
    recording_id: str,
    mode: str = RECORDING_START_RESUME,
    position: int | None = None,
) -> None:
    """Open/play a cloud recording on the Android TV via deep link.

    Shared by waipu.play_recording_on_android_tv and the media browser.
    """
    android_tv_remote = entry.options.get(CONF_ANDROID_TV_REMOTE) or None
    if not android_tv_remote:
        raise HomeAssistantError(
            "Kein Android TV in den Waipu-Optionen konfiguriert"
        )
    if hass.states.get(android_tv_remote) is None:
        raise HomeAssistantError(
            f"Android-TV-Remote-Entity nicht gefunden: {android_tv_remote}"
        )
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
    await async_open_android_link(
        hass,
        android_tv_remote,
        waipu_recording_link(recording_id, mode, position),
    )


async def async_open_program(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WaipuCoordinator,
    station_id: str,
    program_id: str | None = None,
    autoplay: bool = False,
) -> None:
    """Open an EPG program on the Android TV: its detail page, or with
    autoplay play it (live, for a running program). Without a program id,
    the station's running program is used.

    Shared by waipu.open_program_on_android_tv and the media browser.
    """
    android_tv_remote = entry.options.get(CONF_ANDROID_TV_REMOTE) or None
    if not android_tv_remote:
        raise HomeAssistantError(
            "Kein Android TV in den Waipu-Optionen konfiguriert"
        )
    if hass.states.get(android_tv_remote) is None:
        raise HomeAssistantError(
            f"Android-TV-Remote-Entity nicht gefunden: {android_tv_remote}"
        )
    station = coordinator.station(station_id)
    if station is None:
        raise ServiceValidationError(f"Sender unbekannt: {station_id}")
    if not program_id:
        current = station.current_program()
        if current is None:
            raise ServiceValidationError(
                f"Keine laufende Sendung auf '{station_id}' im geladenen EPG"
            )
        program_id = current.id
    if autoplay:
        coordinator.selected_station_id = station_id
        coordinator.async_update_listeners()
    await async_open_android_link(
        hass, android_tv_remote, waipu_program_link(station_id, program_id, autoplay)
    )


def playable_recordings(coordinator: WaipuCoordinator) -> list[Recording]:
    """Every recording that can be watched right now (finished or still
    recording), watched or not, newest first."""
    if not coordinator.data:
        return []
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(
        (
            r
            for r in coordinator.data.recordings
            if r.status in RECORDING_WATCHABLE_STATUSES
        ),
        key=lambda r: r.recording_start_time or oldest,
        reverse=True,
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


class WaipuMediaPlayer(WaipuProgramEntity, MediaPlayerEntity):
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
        # The shown station may have changed with it (TV on/off, waipu
        # left), so the program-end timer follows.
        self._schedule_boundary_update()
        self.async_write_ha_state()

    def _boundary_station(self) -> Station | None:
        return self._current_station()

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
            | MediaPlayerEntityFeature.BROWSE_MEDIA
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
    def _source_labels(self) -> dict[str, str]:
        lang = "de" if (self.hass.config.language or "").startswith("de") else "en"
        return _SOURCE_LABELS[lang]

    @property
    def source_list(self) -> list[str]:
        """Sections of the waipu app; channels are in the media browser."""
        labels = self._source_labels()
        if not self._android_tv_remote:
            # Apple TV can only open the app — one entry, no sections.
            return [labels[SOURCE_LIVE]]
        return [labels[SOURCE_LIVE], labels[SOURCE_RECORDINGS], labels[SOURCE_EPG]]

    @property
    def source(self) -> str | None:
        # Only live TV is tracked (via the tuned channel); which app section
        # is open otherwise isn't observable.
        return self._source_labels()[SOURCE_LIVE] if self._current_station() else None

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
        section = next(
            (
                key
                for labels in _SOURCE_LABELS.values()
                for key, label in labels.items()
                if label == source
            ),
            None,
        )
        if section is None:
            # Channel names were the sources up to 1.7 — keep automations
            # that still send one working.
            st = self._find_station_by_name(source)
            if not st:
                raise HomeAssistantError(f"Unbekannte Quelle: {source}")
            await self._launch_waipu(st.id)
            return
        if not self._android_tv_remote:
            # Apple TV can only open the app.
            await self._launch_waipu(self.coordinator.selected_station_id)
            return
        if section == SOURCE_LIVE:
            # Always send the link (also while waipu is open, e.g. in the
            # EPG) — waipu://tv returns to live TV on the last channel.
            link = self._entry.options.get(CONF_WAIPU_APP_LINK) or DEFAULT_WAIPU_APP_LINK
        else:
            self.coordinator.selected_station_id = None
            self.coordinator.async_update_listeners()
            link = WAIPU_RECORDINGS_LINK if section == SOURCE_RECORDINGS else WAIPU_EPG_LINK
        await async_open_android_link(self.hass, self._android_tv_remote, link)

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        if media_type == MEDIA_TYPE_RECORDING:
            # Resume where waipu left off — except after watching to the end,
            # where the resume point would sit in the credits: start over.
            rec = next(
                (
                    r
                    for r in (self.coordinator.data.recordings if self.coordinator.data else ())
                    if r.id == media_id
                ),
                None,
            )
            mode = (
                RECORDING_START_BEGINNING
                if rec and rec.fully_watched
                else RECORDING_START_RESUME
            )
            await async_play_recording(
                self.hass, self._entry, self.coordinator, media_id, mode
            )
            return
        if media_type == MEDIA_TYPE_PROGRAM_ACTION:
            action, _, rest = media_id.partition("/")
            station_id, _, program_id = rest.partition("/")
            await self._run_program_action(action, station_id, program_id)
            return
        if media_type == MEDIA_TYPE_PROGRAM:
            station_id, _, program_id = media_id.partition("/")
            station = self.coordinator.station(station_id)
            program = next(
                (p for p in (station.programs if station else ()) if p.id == program_id),
                None,
            )
            # Running program: play it (live); otherwise the detail page.
            await async_open_program(
                self.hass,
                self._entry,
                self.coordinator,
                station_id,
                program_id,
                autoplay=bool(program and program.is_live_now()),
            )
            return
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
    # --- Media browser ------------------------------------------------------
    @property
    def _recordings_browsable(self) -> bool:
        """Recordings can only be opened on Android TV (deep link), and only
        exist with a DVR subscription."""
        return bool(
            self._android_tv_remote
            and self.coordinator.data
            and self.coordinator.data.has_dvr
        )

    def _browse_title(self, key: str) -> str:
        lang = "de" if (self.hass.config.language or "").startswith("de") else "en"
        return _BROWSE_TITLES[lang][key]

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        if media_content_id in (None, "", BROWSE_ROOT):
            children = [self._browse_channels(expand=False)]
            if self._android_tv_remote:
                children.append(self._browse_guide())
            if self._recordings_browsable:
                children.insert(0, self._browse_recordings(expand=False))
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_id=BROWSE_ROOT,
                media_content_type=BROWSE_ROOT,
                title=self._browse_title(BROWSE_ROOT),
                can_play=False,
                can_expand=True,
                children=children,
                children_media_class=MediaClass.DIRECTORY,
            )
        if media_content_id == BROWSE_RECORDINGS and self._recordings_browsable:
            return self._browse_recordings(expand=True)
        if (
            media_content_id
            and media_content_id.startswith(BROWSE_SERIES_PREFIX)
            and self._recordings_browsable
        ):
            series_id = media_content_id.removeprefix(BROWSE_SERIES_PREFIX)
            episodes = [
                r
                for r in playable_recordings(self.coordinator)
                if r.series_id == series_id
            ]
            if episodes:
                return self._series_folder(series_id, episodes, expand=True)
        if media_content_id == BROWSE_CHANNELS:
            return self._browse_channels(expand=True)
        if self._android_tv_remote and media_content_id == BROWSE_GUIDE:
            return self._browse_guide(expand=True)
        if (
            self._android_tv_remote
            and media_content_id
            and media_content_id.startswith(BROWSE_PROGRAM_PREFIX)
        ):
            station_id, _, program_id = media_content_id.removeprefix(
                BROWSE_PROGRAM_PREFIX
            ).partition("/")
            station = self.coordinator.station(station_id)
            program = self._find_program(station, program_id)
            if station and program:
                return self._program_actions_folder(
                    station,
                    program,
                    expand=True,
                    series_active=await self._series_active(program),
                )
        if (
            self._android_tv_remote
            and media_content_id
            and media_content_id.startswith(BROWSE_GUIDE_PREFIX)
        ):
            station = self.coordinator.station(
                media_content_id.removeprefix(BROWSE_GUIDE_PREFIX)
            )
            if station:
                return self._guide_station(station, expand=True)
        raise BrowseError(f"Unbekannter Medienpfad: {media_content_id}")

    def _browse_recordings(self, *, expand: bool) -> BrowseMedia:
        return BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id=BROWSE_RECORDINGS,
            media_content_type=BROWSE_RECORDINGS,
            title=self._browse_title(BROWSE_RECORDINGS),
            can_play=False,
            can_expand=True,
            children=self._recordings_children() if expand else None,
            children_media_class=MediaClass.EPISODE,
        )

    def _recordings_children(self) -> list[BrowseMedia]:
        """Series with two or more recorded episodes as folders on top,
        sorted by title; below them the single recordings, newest first."""
        recordings = playable_recordings(self.coordinator)
        by_series: dict[str, list[Recording]] = {}
        for rec in recordings:
            if rec.series_id:
                by_series.setdefault(rec.series_id, []).append(rec)
        series = {sid: eps for sid, eps in by_series.items() if len(eps) >= 2}
        folders = [
            self._series_folder(sid, eps, expand=False)
            for sid, eps in sorted(
                series.items(), key=lambda item: item[1][0].title.casefold()
            )
        ]
        singles = [
            self._recording_item(rec)
            for rec in recordings
            if rec.series_id not in series
        ]
        return folders + singles

    def _series_folder(
        self, series_id: str, episodes: list[Recording], *, expand: bool
    ) -> BrowseMedia:
        newest = episodes[0]
        lang = "de" if (self.hass.config.language or "").startswith("de") else "en"
        count = f"{len(episodes)} Folgen" if lang == "de" else f"{len(episodes)} episodes"
        return BrowseMedia(
            media_class=MediaClass.TV_SHOW,
            media_content_id=f"{BROWSE_SERIES_PREFIX}{series_id}",
            media_content_type=BROWSE_RECORDINGS,
            title=f"{newest.title} ({count})",
            can_play=False,
            can_expand=True,
            thumbnail=newest.preview_image,
            children=(
                [self._recording_item(r, in_series=True) for r in episodes]
                if expand
                else None
            ),
            children_media_class=MediaClass.EPISODE,
        )

    def _browse_guide(self, *, expand: bool = False) -> BrowseMedia:
        """One folder per channel with its running and upcoming programs
        (the EPG window the integration already loads)."""
        return BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id=BROWSE_GUIDE,
            media_content_type=BROWSE_GUIDE,
            title=self._browse_title(BROWSE_GUIDE),
            can_play=False,
            can_expand=True,
            children=(
                [
                    self._guide_station(st, expand=False)
                    for st in visible_stations(self._entry, self.coordinator)
                ]
                if expand
                else None
            ),
            children_media_class=MediaClass.CHANNEL,
        )

    def _guide_station(self, station: Station, *, expand: bool) -> BrowseMedia:
        now = dt_util.utcnow()
        current = station.current_program(now)
        title = station.display_name
        if current:
            title = f"{title} · {current.title}"
        programs = sorted(
            (p for p in station.programs if p.stop_time > now),
            key=lambda p: p.start_time,
        )
        return BrowseMedia(
            media_class=MediaClass.CHANNEL,
            media_content_id=f"{BROWSE_GUIDE_PREFIX}{station.id}",
            media_content_type=BROWSE_GUIDE,
            title=title,
            can_play=False,
            can_expand=True,
            thumbnail=station.logo_url(resolution="640x360"),
            children=(
                [self._program_item(station, p, now) for p in programs]
                if expand
                else None
            ),
            children_media_class=MediaClass.EPISODE,
        )

    def _labels(self) -> dict[str, str]:
        lang = "de" if (self.hass.config.language or "").startswith("de") else "en"
        return _PROGRAM_LABELS[lang]

    @staticmethod
    def _find_program(station: Station | None, program_id: str) -> Program | None:
        if station is None:
            return None
        return next((p for p in station.programs if p.id == program_id), None)

    def _planned_recording(self, program: Program) -> Recording | None:
        """The scheduled/ongoing recording of this program, if any."""
        if not self.coordinator.data:
            return None
        return next(
            (
                r
                for r in self.coordinator.data.recordings
                if r.program_id == program.id and r.status in _PLANNED_STATUSES
            ),
            None,
        )

    def _can_record(self, station: Station, program: Program) -> bool:
        data = self.coordinator.data
        return bool(
            data
            and data.has_dvr
            and not station.recording_forbidden
            and not program.recording_forbidden
        )

    def _program_actions(
        self, station: Station, program: Program, series_active: bool = False
    ) -> list[str]:
        """What an upcoming program offers. Recording options only where
        recording is allowed; a planned recording can be cancelled instead,
        a running series recording stopped instead of started."""
        actions = [PROGRAM_ACTION_DETAILS]
        if not self._can_record(station, program):
            return actions
        if self._planned_recording(program):
            actions.append(PROGRAM_ACTION_DELETE)
        else:
            actions.append(PROGRAM_ACTION_RECORD)
        if program.series_id:
            actions.append(
                PROGRAM_ACTION_END_SERIES if series_active else PROGRAM_ACTION_RECORD_SERIES
            )
        return actions

    async def _series_active(self, program: Program) -> bool:
        """Whether waipu has a series recording for this program's series
        (one lookup, only when a single program's actions are shown)."""
        if not program.series_id:
            return False
        try:
            rule = await self.coordinator.client.get_serial_recording(program.series_id)
        except WaipuApiError:
            return False
        return rule is not None

    def _program_title(self, program: Program, now: datetime) -> str:
        labels = self._labels()
        if program.is_live_now(now):
            prefix = labels["now"]
        else:
            prefix = f"{dt_util.as_local(program.start_time):%H:%M}"
        title = f"{prefix} · {program.title}"
        if program.episode_title:
            title = f"{title} – {program.episode_title}"
        if self._planned_recording(program):
            title = f"{title}  {labels['planned']}"
        return title

    def _program_item(self, station: Station, program: Program, now: datetime) -> BrowseMedia:
        """Running program: plays live. Upcoming program: a folder of
        actions — or, if only the detail page is on offer, opens it directly."""
        live = program.is_live_now(now)
        if live or self._program_actions(station, program) == [PROGRAM_ACTION_DETAILS]:
            return BrowseMedia(
                media_class=MediaClass.EPISODE,
                media_content_id=f"{station.id}/{program.id}",
                media_content_type=MEDIA_TYPE_PROGRAM,
                title=self._program_title(program, now),
                can_play=True,
                can_expand=False,
                thumbnail=program.preview_image,
            )
        return self._program_actions_folder(station, program, expand=False)

    def _program_actions_folder(
        self,
        station: Station,
        program: Program,
        *,
        expand: bool,
        series_active: bool = False,
    ) -> BrowseMedia:
        labels = self._labels()
        return BrowseMedia(
            media_class=MediaClass.EPISODE,
            media_content_id=f"{BROWSE_PROGRAM_PREFIX}{station.id}/{program.id}",
            media_content_type=BROWSE_GUIDE,
            title=self._program_title(program, dt_util.utcnow()),
            can_play=False,
            can_expand=True,
            thumbnail=program.preview_image,
            children=(
                [
                    BrowseMedia(
                        media_class=MediaClass.APP,
                        media_content_id=f"{action}/{station.id}/{program.id}",
                        media_content_type=MEDIA_TYPE_PROGRAM_ACTION,
                        title=labels[action],
                        can_play=True,
                        can_expand=False,
                        thumbnail=self.get_browse_image_url(MEDIA_TYPE_ICON, action),
                    )
                    for action in self._program_actions(station, program, series_active)
                ]
                if expand
                else None
            ),
            children_media_class=MediaClass.APP,
        )

    async def async_get_browse_image(
        self,
        media_content_type: str,
        media_content_id: str,
        media_image_id: str | None = None,
    ) -> tuple[bytes | None, str | None]:
        """Serve the program-action icons (the only images this entity
        generates itself; everything else is an absolute URL)."""
        if media_content_type != MEDIA_TYPE_ICON or not media_content_id.isidentifier():
            return None, None
        path = _ICON_DIR / f"{media_content_id}.svg"
        if not path.is_file():
            return None, None
        data = await self.hass.async_add_executor_job(path.read_bytes)
        return data, "image/svg+xml"

    async def _run_program_action(
        self, action: str, station_id: str, program_id: str
    ) -> None:
        station = self.coordinator.station(station_id)
        program = self._find_program(station, program_id)
        if station is None or program is None:
            raise HomeAssistantError(
                f"Sendung nicht (mehr) im geladenen EPG: {station_id}/{program_id}"
            )
        if action == PROGRAM_ACTION_DETAILS:
            await async_open_program(
                self.hass, self._entry, self.coordinator, station_id, program_id
            )
            return
        series_actions = (PROGRAM_ACTION_RECORD_SERIES, PROGRAM_ACTION_END_SERIES)
        offered = self._program_actions(station, program) + list(series_actions)
        if action not in offered or (
            action in series_actions
            and not (program.series_id and self._can_record(station, program))
        ):
            raise HomeAssistantError(f"Aktion nicht verfügbar: {action}")
        client = self.coordinator.client
        try:
            if action == PROGRAM_ACTION_RECORD:
                await client.create_recording(program_id, station_id)
            elif action == PROGRAM_ACTION_RECORD_SERIES:
                await client.create_serial_recording(
                    station_id, program.title, program.series_id
                )
            elif action == PROGRAM_ACTION_END_SERIES:
                rule = await client.get_serial_recording(program.series_id)
                if rule is None:
                    raise HomeAssistantError(
                        f"Keine Serien-Aufnahme für '{program.title}' aktiv"
                    )
                # Keep what's already recorded or recording, like the
                # delete_serial_recording service does by default.
                await client.delete_serial_recording(rule.id)
            elif action == PROGRAM_ACTION_DELETE:
                planned = self._planned_recording(program)
                if planned:
                    await client.delete_recordings([planned.id])
        except WaipuPermissionError as err:
            raise HomeAssistantError("Aufnehmen nicht erlaubt (Abo prüfen)") from err
        except WaipuApiError as err:
            raise HomeAssistantError(f"waipu API-Fehler: {err}") from err
        await self.coordinator.async_request_refresh()

    def _browse_channels(self, *, expand: bool) -> BrowseMedia:
        return BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id=BROWSE_CHANNELS,
            media_content_type=BROWSE_CHANNELS,
            title=self._browse_title(BROWSE_CHANNELS),
            can_play=False,
            can_expand=True,
            children=(
                [
                    BrowseMedia(
                        media_class=MediaClass.CHANNEL,
                        media_content_id=st.id,
                        media_content_type=MediaType.CHANNEL,
                        title=st.display_name,
                        can_play=True,
                        can_expand=False,
                        thumbnail=st.logo_url(resolution="640x360"),
                    )
                    for st in visible_stations(self._entry, self.coordinator)
                ]
                if expand
                else None
            ),
            children_media_class=MediaClass.CHANNEL,
        )

    @staticmethod
    def _recording_item(rec: Recording, *, in_series: bool = False) -> BrowseMedia:
        # Inside a series folder the series title is already the folder's.
        if in_series and rec.episode_title:
            title = rec.episode_title
        elif rec.episode_title:
            title = f"{rec.title} – {rec.episode_title}"
        else:
            title = rec.title
        if rec.recording_start_time:
            title = f"{title} ({dt_util.as_local(rec.recording_start_time):%d.%m. %H:%M})"
        return BrowseMedia(
            media_class=MediaClass.EPISODE,
            media_content_id=rec.id,
            media_content_type=MEDIA_TYPE_RECORDING,
            title=title,
            can_play=True,
            can_expand=False,
            thumbnail=rec.preview_image,
        )

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
