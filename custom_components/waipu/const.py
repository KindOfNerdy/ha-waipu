"""Constants for the waipu.tv integration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final
from urllib.parse import urlencode

DOMAIN: Final = "waipu"

# --- Config / Options entry keys ---------------------------------------------
# Username/password live under homeassistant.const; only Waipu-specific keys here.
CONF_DEVICE_ID: Final = "device_id"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_SELECTED_CHANNELS: Final = "selected_channels"
CONF_APPLE_TV_ENTITY: Final = "apple_tv_entity"
CONF_WAIPU_BUNDLE_ID: Final = "waipu_bundle_id"
CONF_ANDROID_TV_REMOTE: Final = "android_tv_remote"
CONF_WAIPU_APP_LINK: Final = "waipu_app_link"
# Optional media_player of HA's "Android Debug Bridge" integration for the
# same TV. Android's media session, read over ADB, is the only place HA sees
# what waipu actually plays (androidtv_remote reports just the foreground
# app), so a channel switched on the TV itself can be followed by matching
# the reported program title against the EPG.
CONF_ADB_ENTITY: Final = "adb_entity"
# How often the TV is asked while waipu is in front.
TV_POLL_INTERVAL: Final = timedelta(seconds=10)
# Which channels get HA entities: waipu's own favorites (followed live) or
# all channels, narrowed by CONF_SELECTED_CHANNELS. The stored key keeps its
# historic name — it used to double as the Android TV channel-number basis
# for digit-key switching, which deep links made obsolete.
CONF_CHANNEL_SOURCE: Final = "android_tv_channel_view"
# Options from earlier versions that nothing reads anymore; dropped from the
# config entry on setup (see __init__.async_setup_entry).
OBSOLETE_OPTIONS: Final = (
    "android_tv_launch_delay",
    "apple_tv_remote",  # removed in 2.0.0, was never used
    "cast_entity",  # removed in 3.0.0, replaced by CONF_ADB_ENTITY
    "epg_cache_ttl_minutes",  # removed in 2.0.0, now fixed (EPG_CACHE_TTL_MIN)
)

# --- Defaults ----------------------------------------------------------------
DEFAULT_WAIPU_BUNDLE_ID: Final = "de.exaring.waipu.tvos"
# Launching by bare package id is unreliable on Android TV since a Play Store
# change (see the androidtv_remote integration docs) — a deep link works
# reliably instead. waipu://tv opens the app's live-TV view; used whenever
# no specific channel is requested (see waipu_station_link for that).
DEFAULT_WAIPU_APP_LINK: Final = "waipu://tv"
# Other known section-level deep links (community-verified), used by the
# dedicated EPG/recordings shortcut buttons below.
WAIPU_RECORDINGS_LINK: Final = "waipu://recordings"
WAIPU_WAIPUTHEK_LINK: Final = "waipu://waiputhek"


def waipu_epg_link(station_id: str | None = None) -> str:
    """Deep link to the TV guide, on `station_id` if given."""
    return f"waipu://epg?{urlencode({'id': station_id})}" if station_id else "waipu://epg"

# --- Android TV deep links ----------------------------------------------------
# Found in the waipu Android TV app (2026.21.0, re-checked against 2026.22.1):
# its manifest, its deep-link parser and the links it writes into the Android
# TV launcher itself. Tested live on 2026-11-02 and 2026-11-20 (Philips
# Android TV 12). Every parameter needs `=value` — a bare flag makes waipu
# drop the whole link — and `position` must be a whole number.
#   waipu://tv?id=<stationId>         switches channel — from a cold start,
#                                     while waipu is already running and
#                                     while a recording plays
#       &position=<Unix ms>           plays from that moment (timeshift) —
#                                     the program's start = "from the start"
#   waipu://epg?id=<stationId>        the TV guide, on that channel
#   waipu://waiputhek                 the waiputhek (Mediathek) start page
#   waipu://recordings?recordingId=<id>
#       (no autoplay)                 opens the recording's detail page
#       &autoplay=true                plays it, resuming where waipu left off
#       &autoplay=true&position=<s>   plays from <s> seconds; 0 = from the
#                                     start, overriding the resume point
#   waipu://epgdetails?channelId=<stationId>&programId=<id>
#       (no autoplay)                 opens the program's detail page (live
#                                     TV / restart / record / reminder)
#       &autoplay=true                plays it — for a running program that
#                                     is live TV (start over: tv + position)
# `id` is ignored by the recordings link — it must be `recordingId`. The
# programId is the EPG id from epg-cache's grid (the same the sensors show).
# Unknown whether the tvOS app supports any of this; Apple TV stays launch-only.
RECORDING_START_RESUME: Final = "resume"
RECORDING_START_BEGINNING: Final = "beginning"
RECORDING_START_DETAILS: Final = "details"
RECORDING_START_MODES: Final = (
    RECORDING_START_RESUME,
    RECORDING_START_BEGINNING,
    RECORDING_START_DETAILS,
)


def waipu_station_link(station_id: str, start: datetime | None = None) -> str:
    """Deep link that opens waipu live TV on `station_id` — from `start`
    (a moment still in waipu's timeshift buffer, e.g. the program's start)
    instead of live. waipu reads `position` as Unix milliseconds; seconds
    land somewhere else (live-checked 2026-11-20, app 2026.22.1)."""
    params = {"id": station_id}
    if start is not None:
        params["position"] = str(int(start.timestamp() * 1000))
    return f"waipu://tv?{urlencode(params)}"


def waipu_program_link(station_id: str, program_id: str, autoplay: bool = False) -> str:
    """Deep link to an EPG program: its detail page, or playback with autoplay."""
    params = {"channelId": station_id, "programId": program_id}
    if autoplay:
        params["autoplay"] = "true"
    return f"waipu://epgdetails?{urlencode(params)}"


def waipu_recording_link(
    recording_id: str,
    mode: str = RECORDING_START_RESUME,
    position: int | None = None,
) -> str:
    """Deep link that opens/plays a recording.

    `position` (seconds) wins over `mode` and always plays.
    """
    params: dict[str, str] = {"recordingId": recording_id}
    if position is not None:
        params["autoplay"] = "true"
        params["position"] = str(int(position))
    elif mode == RECORDING_START_BEGINNING:
        params["autoplay"] = "true"
        params["position"] = "0"
    elif mode == RECORDING_START_RESUME:
        params["autoplay"] = "true"
    elif mode != RECORDING_START_DETAILS:
        raise ValueError(f"unknown recording start mode: {mode}")
    return f"waipu://recordings?{urlencode(params)}"
# For *detecting* whether waipu is the foreground app via the Android TV
# remote's current_activity attribute — not for launching (see
# CONF_WAIPU_APP_LINK/DEFAULT_WAIPU_APP_LINK for that). current_activity
# always reports the actual package/component, regardless of which deep
# link was used to open it.
ANDROID_WAIPU_PACKAGE_ID: Final = "de.exaring.waipu"
# Which TV the integration controls. Not stored itself — derived from which
# platform-specific options are set (see config_flow.tv_platform_of), so
# existing entries need no migration. The form field only picks the page.
CONF_TV_PLATFORM: Final = "tv_platform"
TV_PLATFORM_ANDROID: Final = "android_tv"
TV_PLATFORM_APPLE: Final = "apple_tv"
TV_PLATFORM_NONE: Final = "none"
TV_PLATFORMS: Final = (TV_PLATFORM_ANDROID, TV_PLATFORM_APPLE, TV_PLATFORM_NONE)
# CONF_CHANNEL_SOURCE values. "favorites" follows waipu's own favorite flag
# live and ignores CONF_SELECTED_CHANNELS; "all" offers every channel,
# narrowed by CONF_SELECTED_CHANNELS (favorites while nothing is saved).
CHANNEL_SOURCE_ALL: Final = "all"
CHANNEL_SOURCE_FAVORITES: Final = "favorites"
# Defaults to favorites: WaipuCoordinator's own fallback (no explicit
# selected_channels saved yet) already limits freshly created HA entities
# to favorites, so this stays consistent with that out of the box.
DEFAULT_CHANNEL_SOURCE: Final = CHANNEL_SOURCE_FAVORITES
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)
EPG_LOOKAHEAD: Final = timedelta(hours=6)
EPG_LOOKBEHIND: Final = timedelta(minutes=30)
# How long a fetched EPG grid slot (see WaipuClient.get_grid_slot) is
# served from cache before being refetched. Grid slots are keyed by
# (station_id, slot_start) and rarely change once published, so this
# cuts repeat requests across coordinator polls (DEFAULT_SCAN_INTERVAL)
# substantially. Doesn't affect "jetzt"/"danach" correctness —
# Station.current_program()/next_program() always compare the (possibly
# cached) start/stop times against the live wall-clock time on every
# call, not just when a slot was last fetched. The only real tradeoff: a
# late schedule correction (e.g. a live sports broadcast overrunning)
# can take up to this long to show up locally.
EPG_CACHE_TTL_MIN: Final = 60
TOKEN_REFRESH_THRESHOLD_SEC: Final = 60  # refresh access_token 60s before exp

# --- Subscription substrings that imply cloud DVR ----------------------------
# Match by substring (case-insensitive) — waipu appends bundle suffixes like
# "Perfect Plus mit WOW Filme & Serien Jahrespaket".
SUBSCRIPTION_DVR_MARKERS: Final = (
    "perfect",  # covers "Perfect", "Perfect Plus", and any bundle variant
    "o2 tv l",  # covers "O2 TV L" — NOT "O2 TV XL", the "X" breaks the
    # substring match ("o2 tv " + "x" + "l" != "o2 tv " + "l"), hence the
    # separate marker below (caught by tests/test_const.py).
    "o2 tv xl",
)


def subscription_has_dvr(subscription: str) -> bool:
    s = (subscription or "").lower()
    return any(marker in s for marker in SUBSCRIPTION_DVR_MARKERS)

# --- Service names -----------------------------------------------------------
SERVICE_CREATE_RECORDING: Final = "create_recording"
SERVICE_STOP_RECORDING: Final = "stop_recording"
SERVICE_DELETE_RECORDING: Final = "delete_recording"
SERVICE_CREATE_SERIAL_RECORDING: Final = "create_serial_recording"
SERVICE_DELETE_SERIAL_RECORDING: Final = "delete_serial_recording"
SERVICE_PLAY_RECORDING_ON_ANDROID_TV: Final = "play_recording_on_android_tv"
SERVICE_OPEN_PROGRAM_ON_ANDROID_TV: Final = "open_program_on_android_tv"
SERVICE_RESTART_PROGRAM: Final = "restart_program"

ATTR_PROGRAM_ID: Final = "program_id"
ATTR_STATION_ID: Final = "station_id"
ATTR_RECORDING_ID: Final = "recording_id"
ATTR_SERIES_ID: Final = "series_id"
ATTR_MODE: Final = "mode"
ATTR_POSITION: Final = "position"
ATTR_AUTOPLAY: Final = "autoplay"

# --- Recording statuses that count as "new" ---------------------------------
# waipu sets isNew on SCHEDULED recordings too — only count ones you can
# already watch (finished or currently recording).
RECORDING_WATCHABLE_STATUSES: Final = ("RECORDING", "FINISHED")

# --- Reminders ("erinnern und umschalten") ---------------------------------
CONF_REMINDER_NOTIFY: Final = "reminder_notify"  # notify services, e.g. ["mobile_app_phone"]
CONF_REMINDER_LEAD: Final = "reminder_lead_minutes"
DEFAULT_REMINDER_LEAD: Final = 5
REMINDER_KIND_PROGRAM: Final = "program"  # one program, once
REMINDER_KIND_SERIES: Final = "series"  # every episode of a series on one channel
REMINDER_KIND_SCHEDULE: Final = "schedule"  # a time on given weekdays, on one channel
EVENT_REMINDER: Final = "waipu_reminder"
SERVICE_ADD_REMINDER: Final = "add_reminder"
SERVICE_UPDATE_REMINDER: Final = "update_reminder"
SERVICE_REMOVE_REMINDER: Final = "remove_reminder"
ATTR_REMINDER_ID: Final = "reminder_id"
