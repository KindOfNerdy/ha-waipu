"""Constants for the waipu.tv integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "waipu"

# --- Config / Options entry keys ---------------------------------------------
# Username/password live under homeassistant.const; only Waipu-specific keys here.
CONF_DEVICE_ID: Final = "device_id"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_SELECTED_CHANNELS: Final = "selected_channels"
CONF_APPLE_TV_ENTITY: Final = "apple_tv_entity"
CONF_APPLE_TV_REMOTE: Final = "apple_tv_remote"
CONF_WAIPU_BUNDLE_ID: Final = "waipu_bundle_id"
CONF_ANDROID_TV_REMOTE: Final = "android_tv_remote"
CONF_WAIPU_APP_LINK: Final = "waipu_app_link"
CONF_ANDROID_TV_CHANNEL_VIEW: Final = "android_tv_channel_view"

# --- Defaults ----------------------------------------------------------------
DEFAULT_WAIPU_BUNDLE_ID: Final = "de.exaring.waipu.tvos"
# Launching by bare package id is unreliable on Android TV since a Play Store
# change (see the androidtv_remote integration docs) — a deep link works
# reliably instead. waipu://tv opens the app's live-TV view (app launch only,
# no per-channel deep link — same scope as the Apple TV path).
DEFAULT_WAIPU_APP_LINK: Final = "waipu://tv"
# Other known section-level deep links (community-verified), used by the
# dedicated EPG/recordings shortcut buttons below.
WAIPU_EPG_LINK: Final = "waipu://epg"
WAIPU_RECORDINGS_LINK: Final = "waipu://recordings"
# "all" = channel numbers count every visible channel; "favorites" = only
# favorited ones. This MUST match whichever list the waipu Android TV app
# is currently displaying its own channel numbers for — that's a
# client-side app setting we have no way to read or change from HA.
ANDROID_TV_CHANNEL_VIEW_ALL: Final = "all"
ANDROID_TV_CHANNEL_VIEW_FAVORITES: Final = "favorites"
# Defaults to favorites: WaipuCoordinator's own fallback (no explicit
# selected_channels saved yet) already limits freshly created HA entities
# to favorites, so this stays consistent with that out of the box.
DEFAULT_ANDROID_TV_CHANNEL_VIEW: Final = ANDROID_TV_CHANNEL_VIEW_FAVORITES
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)
EPG_LOOKAHEAD: Final = timedelta(hours=6)
EPG_LOOKBEHIND: Final = timedelta(minutes=30)
TOKEN_REFRESH_THRESHOLD_SEC: Final = 60  # refresh access_token 60s before exp

# --- Subscription substrings that imply cloud DVR ----------------------------
# Match by substring (case-insensitive) — waipu appends bundle suffixes like
# "Perfect Plus mit WOW Filme & Serien Jahrespaket".
SUBSCRIPTION_DVR_MARKERS: Final = (
    "perfect",  # covers "Perfect", "Perfect Plus", and any bundle variant
    "o2 tv l",  # covers "O2 TV L" and "O2 TV XL"
)


def subscription_has_dvr(subscription: str) -> bool:
    s = (subscription or "").lower()
    return any(marker in s for marker in SUBSCRIPTION_DVR_MARKERS)

# --- Service names -----------------------------------------------------------
SERVICE_CREATE_RECORDING: Final = "create_recording"
SERVICE_DELETE_RECORDING: Final = "delete_recording"
SERVICE_LAUNCH_ON_APPLE_TV: Final = "launch_on_apple_tv"
SERVICE_LAUNCH_ON_ANDROID_TV: Final = "launch_on_android_tv"
SERVICE_SWITCH_CHANNEL_ON_ANDROID_TV: Final = "switch_channel_on_android_tv"

ATTR_PROGRAM_ID: Final = "program_id"
ATTR_STATION_ID: Final = "station_id"
ATTR_RECORDING_ID: Final = "recording_id"
