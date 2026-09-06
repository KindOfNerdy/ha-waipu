"""Async client for the (unofficial) waipu.tv API.

Targets the post-2025 API generation:
  * EPG comes from epg-cache.waipu.tv (grid slots, auth-free)
  * Station catalog from web-proxy.waipu.tv/station-config (auth-free)
  * User station settings from user-stations.waipu.tv (auth)
  * Recordings v4 from recording.waipu.tv (auth)

Reverse-engineered from the play.waipu.tv web bundle. Anything marked
``# inferred`` was not directly observable and may need adjustment if
the API talks back.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable
from urllib.parse import urlencode

import aiohttp

_LOGGER = logging.getLogger(__name__)

# --- Endpoints ---------------------------------------------------------------
AUTH_URL = "https://auth.waipu.tv/oauth/token"
STATION_CATALOG_URL = "https://web-proxy.waipu.tv/station-config"
USER_STATIONS_URL = "https://user-stations.waipu.tv/api/stations"
GRID_INFO_URL = "https://epg-cache.waipu.tv/api/grid/info"
GRID_SLOT_URL = "https://epg-cache.waipu.tv/api/grid/{station_id}/{slot}"
PROGRAM_DETAIL_URL = "https://epg-cache.waipu.tv/api/programs/{program_id}"
RECORDINGS_URL = "https://recording.waipu.tv/api/recordings"

CLIENT_BASIC_AUTH = "Basic YW5kcm9pZENsaWVudDpzdXBlclNlY3JldA=="

ACCEPT_RECORDINGS = "application/vnd.waipu.recordings-extended-v4+json"
CONTENT_CREATE_RECORDING = "application/vnd.waipu.recording-create-v4+json"
CONTENT_DELETE_RECORDINGS = "application/vnd.waipu.recording-ids-v4+json"

DEFAULT_USER_AGENT = "ha-waipu/0.2.0"
DEFAULT_LOGO_RESOLUTION = "320x180"
DEFAULT_LOGO_SHAPE = "standard"
DEFAULT_IMAGE_RESOLUTION = "480x270"
SLOT_HOURS = 4


# --- Errors ------------------------------------------------------------------
class WaipuError(Exception):
    pass


class WaipuAuthError(WaipuError):
    pass


class WaipuPermissionError(WaipuError):
    pass


class WaipuApiError(WaipuError):
    pass


# --- Data classes ------------------------------------------------------------
@dataclass(frozen=True)
class Program:
    id: str
    title: str
    start_time: datetime
    stop_time: datetime
    station_id: str
    episode_title: str | None = None
    genre: str | None = None
    preview_image: str | None = None
    series_id: str | None = None
    recording_forbidden: bool = False

    @property
    def duration(self) -> timedelta:
        return self.stop_time - self.start_time

    def is_live_now(self, ref: datetime | None = None) -> bool:
        now = ref or datetime.now(timezone.utc)
        return self.start_time <= now < self.stop_time


@dataclass(frozen=True)
class Station:
    id: str
    display_name: str
    description: str | None
    logo_template_url: str | None
    stream_qualities: tuple[str, ...]
    recording_forbidden: bool
    favorite: bool = False
    visible: bool = True
    locked: bool = False
    omitted: bool = False
    stream_quality: str = "hd"
    programs: tuple[Program, ...] = field(default_factory=tuple)

    @property
    def usable(self) -> bool:
        return self.visible and not self.locked and not self.omitted

    def logo_url(
        self,
        *,
        resolution: str = DEFAULT_LOGO_RESOLUTION,
        shape: str = DEFAULT_LOGO_SHAPE,
        quality: str | None = None,
    ) -> str | None:
        if not self.logo_template_url:
            return None
        q = quality or self.stream_quality
        return (
            self.logo_template_url
            .replace("${streamQuality}", q)
            .replace("${shape}", shape)
            .replace("${resolution}", resolution)
        )

    def current_program(self, ref: datetime | None = None) -> Program | None:
        now = ref or datetime.now(timezone.utc)
        for p in self.programs:
            if p.is_live_now(now):
                return p
        return None

    def next_program(self, ref: datetime | None = None) -> Program | None:
        now = ref or datetime.now(timezone.utc)
        future = sorted(
            (p for p in self.programs if p.start_time > now),
            key=lambda p: p.start_time,
        )
        return future[0] if future else None


@dataclass(frozen=True)
class ProgramDetail:
    """Extra info from the (auth-free) program detail endpoint.

    Not returned by the EPG grid — only fetched on demand for programs
    actually shown as a sensor's current/next value, since it's one
    request per program id.
    """
    id: str
    description: str | None = None
    parental_guidance: str | None = None  # inferred: e.g. "fsk-0", "fsk-16"
    pin_required: bool = False
    rerun: bool = False


@dataclass(frozen=True)
class Recording:
    id: str
    program_id: str | None
    station_id: str
    station_display: str | None
    title: str
    status: str  # SCHEDULED | RECORDING | FINISHED | FAILED
    recording_start_time: datetime | None
    duration_seconds: int
    epg_start_time: datetime | None = None
    genre: str | None = None
    preview_image: str | None = None
    episode_title: str | None = None
    season: str | None = None
    episode: str | None = None
    series_id: str | None = None
    position_percentage: int = 0
    fully_watched: bool = False
    partially_watched: bool = False
    is_new: bool = False
    locked: bool = False
    recording_group: int | None = None
    total_episode_count: int | None = None
    new_episode_count: int | None = None

    @property
    def duration(self) -> timedelta:
        return timedelta(seconds=self.duration_seconds)


TokenPersistCallback = Callable[[str | None, str | None], Awaitable[None]]


# --- JWT helpers -------------------------------------------------------------
def decode_jwt(token: str) -> dict[str, Any]:
    try:
        _, payload, _ = token.split(".")
    except ValueError as err:
        raise WaipuError("Malformed JWT") from err
    payload = payload.replace("_", "/").replace("-", "+")
    padding = "=" * (-len(payload) % 4)
    return json.loads(base64.b64decode(payload + padding))


def jwt_is_valid(token: str | None, threshold_sec: int = 0) -> bool:
    if not token:
        return False
    try:
        exp = float(decode_jwt(token).get("exp", 0))
        return time.time() < (exp - threshold_sec)
    except WaipuError:
        return False


# --- Slot helpers ------------------------------------------------------------
def slot_start_for(ts: datetime, slot_hours: int = SLOT_HOURS) -> datetime:
    """Round a datetime down to the slot boundary (UTC)."""
    utc = ts.astimezone(timezone.utc)
    hour = (utc.hour // slot_hours) * slot_hours
    return utc.replace(hour=hour, minute=0, second=0, microsecond=0)


def slots_covering(start: datetime, end: datetime) -> list[datetime]:
    """All slot start timestamps whose 4h window overlaps [start, end)."""
    first = slot_start_for(start)
    out: list[datetime] = []
    cur = first
    while cur < end:
        out.append(cur)
        cur = cur + timedelta(hours=SLOT_HOURS)
    return out


def format_slot(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Image helpers -----------------------------------------------------------
def fill_image_url(url: str | None, resolution: str = DEFAULT_IMAGE_RESOLUTION) -> str | None:
    if not url:
        return None
    return url.replace("${resolution}", resolution)


# --- Client ------------------------------------------------------------------
class WaipuClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        device_id: str,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        on_token_change: TokenPersistCallback | None = None,
        refresh_threshold_sec: int = 60,
    ) -> None:
        self._session = session
        self._device_id = device_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._user_agent = user_agent
        self._on_token_change = on_token_change
        self._refresh_threshold = refresh_threshold_sec
        self._token_lock = asyncio.Lock()
        self._username: str | None = None
        self._password: str | None = None

    # --- Properties ----------------------------------------------------------
    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    @property
    def account(self) -> dict[str, Any]:
        if not self._access_token:
            raise WaipuAuthError("Not authenticated")
        return decode_jwt(self._access_token)

    @property
    def user_handle(self) -> str:
        return str(self.account.get("userHandle", ""))

    @property
    def subscription(self) -> str:
        return str(
            self.account.get("userAssets", {})
            .get("account", {})
            .get("subscription", "")
        )

    # --- Auth ----------------------------------------------------------------
    def set_credentials(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    async def login(self, username: str, password: str) -> None:
        self.set_credentials(username, password)
        await self._password_grant()

    async def _password_grant(self) -> None:
        if not self._username or not self._password:
            raise WaipuAuthError("No credentials for password grant")
        await self._token_request(
            {
                "username": self._username,
                "password": self._password,
                "grant_type": "password",
                "waipu_device_id": self._device_id,
            }
        )

    async def _refresh_grant(self) -> None:
        if not self._refresh_token:
            raise WaipuAuthError("No refresh token")
        await self._token_request(
            {
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
                "waipu_device_id": self._device_id,
            }
        )

    async def _token_request(self, payload: dict[str, str]) -> None:
        headers = {
            "Authorization": CLIENT_BASIC_AUTH,
            "User-Agent": self._user_agent,
        }
        try:
            async with self._session.post(
                AUTH_URL, data=payload, headers=headers
            ) as resp:
                if resp.status in (400, 401):
                    body = await resp.text()
                    raise WaipuAuthError(f"Auth failed ({resp.status}): {body}")
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise WaipuApiError(f"Auth request failed: {err}") from err

        new_access = data.get("access_token")
        new_refresh = data.get("refresh_token", self._refresh_token)
        if not new_access:
            raise WaipuAuthError("Auth response missing access_token")
        self._access_token = new_access
        self._refresh_token = new_refresh
        if self._on_token_change:
            await self._on_token_change(self._access_token, self._refresh_token)

    async def ensure_token(self) -> str:
        async with self._token_lock:
            if jwt_is_valid(self._access_token, self._refresh_threshold):
                return self._access_token  # type: ignore[return-value]
            if jwt_is_valid(self._refresh_token):
                try:
                    await self._refresh_grant()
                    return self._access_token  # type: ignore[return-value]
                except WaipuAuthError:
                    _LOGGER.warning(
                        "Refresh token rejected, falling back to password grant"
                    )
            await self._password_grant()
            return self._access_token  # type: ignore[return-value]

    # --- Request helpers -----------------------------------------------------
    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        auth: bool,
        accept: str | None = None,
        content_type: str | None = None,
        body: Any = None,
    ) -> Any:
        headers: dict[str, str] = {"User-Agent": self._user_agent}
        if auth:
            token = await self.ensure_token()
            headers["Authorization"] = f"Bearer {token}"
        if accept:
            headers["Accept"] = accept
        if content_type:
            headers["Content-Type"] = content_type

        data = json.dumps(body) if body is not None else None

        try:
            async with self._session.request(
                method, url, data=data, headers=headers
            ) as resp:
                if resp.status == 401:
                    raise WaipuAuthError(f"Unauthorized: {method} {url}")
                if resp.status == 403:
                    raise WaipuPermissionError(f"Forbidden: {method} {url}")
                resp.raise_for_status()
                if resp.status == 204:
                    return None
                # Read body always — waipu uses chunked transfer encoding on
                # most endpoints, so Content-Length is None even with data.
                text = await resp.text()
                if not text:
                    return None
                try:
                    return json.loads(text)
                except json.JSONDecodeError as err:
                    raise WaipuApiError(
                        f"{method} {url} returned non-JSON body: {text[:200]!r}"
                    ) from err
        except aiohttp.ClientError as err:
            raise WaipuApiError(f"{method} {url} failed: {err}") from err

    # --- Station catalog + user settings -------------------------------------
    async def get_station_catalog(self) -> dict[str, dict[str, Any]]:
        """Public catalog: id → {displayName, logoTemplateUrl, restrictions, …}."""
        data = await self._request_json("GET", STATION_CATALOG_URL, auth=False)
        out: dict[str, dict[str, Any]] = {}
        for s in (data or {}).get("stations", []):
            sid = s.get("id")
            if sid:
                out[sid] = s
        return out

    async def get_user_stations(self) -> list[dict[str, Any]]:
        """User-specific station list with userSettings, locked/omitted flags."""
        data = await self._request_json("GET", USER_STATIONS_URL, auth=True)
        return list(data or [])

    async def get_stations(self) -> list[Station]:
        """Merged view: only stations the user actually subscribed to."""
        catalog, user = await asyncio.gather(
            self.get_station_catalog(),
            self.get_user_stations(),
        )
        _LOGGER.info(
            "waipu stations: catalog=%d, user=%d (first user entry keys: %s)",
            len(catalog),
            len(user),
            sorted((user[0] or {}).keys()) if user else "n/a",
        )
        out: list[Station] = []
        for u in user:
            sid = u.get("stationId") or u.get("id")
            if not sid:
                continue
            cat = catalog.get(sid, {})
            settings = u.get("userSettings") or {}
            restrictions = cat.get("restrictions") or {}
            out.append(
                Station(
                    id=sid,
                    display_name=u.get("displayName") or cat.get("displayName") or sid,
                    description=cat.get("description"),
                    logo_template_url=cat.get("logoTemplateUrl"),
                    stream_qualities=tuple(cat.get("streamQualities") or ()),
                    recording_forbidden=bool(restrictions.get("recordingForbidden", False)),
                    favorite=bool(settings.get("favorite", False)),
                    visible=bool(settings.get("visible", True)),
                    locked=bool(u.get("locked", False)),
                    omitted=bool(u.get("omitted", False)),
                    stream_quality=str(u.get("streamQuality", "hd")),
                )
            )
        return out

    # --- EPG -----------------------------------------------------------------
    async def get_grid_slot(
        self, station_id: str, slot_start: datetime
    ) -> list[Program]:
        url = GRID_SLOT_URL.format(
            station_id=station_id.lower(),
            slot=format_slot(slot_start),
        )
        try:
            data = await self._request_json("GET", url, auth=False)
        except WaipuApiError as err:
            _LOGGER.debug("Grid slot fetch failed for %s: %s", station_id, err)
            return []
        return [_program_from_grid(p, station_id) for p in (data or []) if p.get("id")]

    async def get_programs_in_window(
        self,
        station_ids: list[str],
        start: datetime,
        end: datetime,
        *,
        max_concurrent: int = 8,
    ) -> dict[str, list[Program]]:
        """Fetch EPG for the given stations covering [start, end)."""
        slots = slots_covering(start, end)
        semaphore = asyncio.Semaphore(max_concurrent)
        out: dict[str, list[Program]] = {sid: [] for sid in station_ids}

        async def _fetch(sid: str, slot: datetime) -> tuple[str, list[Program]]:
            async with semaphore:
                programs = await self.get_grid_slot(sid, slot)
            return sid, programs

        tasks = [
            asyncio.create_task(_fetch(sid, slot))
            for sid in station_ids
            for slot in slots
        ]
        for fut in asyncio.as_completed(tasks):
            sid, programs = await fut
            out[sid].extend(programs)

        # Deduplicate + sort per station
        for sid, programs in out.items():
            seen: dict[str, Program] = {}
            for p in programs:
                seen[p.id] = p
            out[sid] = sorted(seen.values(), key=lambda p: p.start_time)
        return out

    async def get_program_detail(self, program_id: str) -> ProgramDetail | None:
        url = PROGRAM_DETAIL_URL.format(program_id=program_id)
        try:
            data = await self._request_json("GET", url, auth=False)
        except WaipuApiError as err:
            _LOGGER.debug("Program detail fetch failed for %s: %s", program_id, err)
            return None
        if not data:
            return None
        return _program_detail_from_dict(data)

    async def get_program_details(
        self, program_ids: list[str], *, max_concurrent: int = 8
    ) -> dict[str, ProgramDetail]:
        """Fetch detail for several program ids concurrently.

        Ids that fail or return nothing are simply omitted from the result —
        detail is a nice-to-have, never worth failing the whole refresh over.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _fetch(pid: str) -> tuple[str, ProgramDetail | None]:
            async with semaphore:
                detail = await self.get_program_detail(pid)
            return pid, detail

        out: dict[str, ProgramDetail] = {}
        tasks = [asyncio.create_task(_fetch(pid)) for pid in program_ids]
        for fut in asyncio.as_completed(tasks):
            pid, detail = await fut
            if detail:
                out[pid] = detail
        return out

    # --- Recordings ----------------------------------------------------------
    async def get_recordings(self) -> list[Recording]:
        try:
            data = await self._request_json(
                "GET", RECORDINGS_URL, auth=True, accept=ACCEPT_RECORDINGS
            )
        except WaipuPermissionError:
            return []
        return [_recording_from_dict(r) for r in (data or []) if r.get("id")]

    async def create_recording(self, program_id: str, station_id: str) -> None:
        await self._request_json(
            "POST",
            RECORDINGS_URL,
            auth=True,
            content_type=CONTENT_CREATE_RECORDING,
            body={"programId": program_id, "stationId": station_id},
        )

    async def delete_recordings(self, recording_ids: list[str]) -> None:
        if not recording_ids:
            return
        await self._request_json(
            "DELETE",
            RECORDINGS_URL,
            auth=True,
            content_type=CONTENT_DELETE_RECORDINGS,
            accept=ACCEPT_RECORDINGS,
            body={"recordingIds": recording_ids},
        )


# --- Parsing helpers ---------------------------------------------------------
def _program_from_grid(data: dict[str, Any], station_id: str) -> Program:
    return Program(
        id=str(data["id"]),
        title=str(data.get("title", "")),
        start_time=_parse_dt(data["startTime"]),
        stop_time=_parse_dt(data["stopTime"]),
        station_id=station_id,
        episode_title=data.get("episodeTitle"),
        genre=data.get("genreDisplayName") or data.get("genre"),
        preview_image=fill_image_url(data.get("previewImage")),
        series_id=_as_str(data.get("seriesId")),
        recording_forbidden=bool(data.get("recordingForbidden", False)),
    )


def _program_detail_from_dict(data: dict[str, Any]) -> ProgramDetail:
    text = data.get("textContent") or {}
    rating = data.get("ageRating") or {}
    return ProgramDetail(
        id=str(data["id"]),
        description=_as_str(text.get("descLong")) or _as_str(text.get("descShort")),
        parental_guidance=_as_str(rating.get("parentalGuidance")),
        pin_required=bool(rating.get("pinRequired", False)),
        rerun=bool(data.get("rerun", False)),
    )


def _recording_from_dict(data: dict[str, Any]) -> Recording:
    return Recording(
        id=str(data["id"]),
        program_id=_as_str(data.get("programId")),
        station_id=str(data.get("stationId", "")),
        station_display=_as_str(data.get("stationDisplay")),
        title=str(data.get("title", "")),
        status=str(data.get("status", "")),
        recording_start_time=_parse_optional_dt(data.get("recordingStartTime")),
        epg_start_time=_parse_optional_dt(data.get("epgStartTime")),
        duration_seconds=int(data.get("durationSeconds", 0)),
        genre=_as_str(data.get("genreDisplayName")),
        preview_image=fill_image_url(data.get("previewImage")),
        episode_title=_as_str(data.get("episodeTitle")),
        season=_as_str(data.get("season")),
        episode=_as_str(data.get("episode")),
        series_id=_as_str(data.get("seriesId")),
        position_percentage=int(data.get("positionPercentage", 0)),
        fully_watched=bool(data.get("fullyWatched", False)),
        partially_watched=bool(data.get("partiallyWatched", False)),
        is_new=bool(data.get("isNew", False)),
        locked=bool(data.get("locked", False)),
        recording_group=data.get("recordingGroup"),
        total_episode_count=data.get("totalEpisodeCount"),
        new_episode_count=data.get("newEpisodeCount"),
    )


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _parse_dt(value: str) -> datetime:
    s = value.replace("Z", "+00:00")
    # waipu uses "+0100" without colon for recordings, "+02:00" / "Z" for grid
    if len(s) >= 5 and s[-5] in ("+", "-") and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as err:
        raise WaipuApiError(f"Cannot parse datetime: {value}") from err
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_optional_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return _parse_dt(str(value))
    except WaipuApiError:
        return None


# encoded for the auth_url helper export; kept for backwards compat with
# code that might still import it
__all__ = [
    "WaipuClient",
    "WaipuError",
    "WaipuAuthError",
    "WaipuApiError",
    "WaipuPermissionError",
    "Station",
    "Program",
    "ProgramDetail",
    "Recording",
    "decode_jwt",
    "jwt_is_valid",
]
