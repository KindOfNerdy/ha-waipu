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
CONF_WAIPU_PACKAGE_ID: Final = "waipu_package_id"

# --- Defaults ----------------------------------------------------------------
DEFAULT_WAIPU_BUNDLE_ID: Final = "de.exaring.waipu.tvos"
DEFAULT_WAIPU_PACKAGE_ID: Final = "de.exaring.waipu"
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

ATTR_PROGRAM_ID: Final = "program_id"
ATTR_STATION_ID: Final = "station_id"
ATTR_RECORDING_ID: Final = "recording_id"
