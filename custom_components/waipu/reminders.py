"""Reminders: a push a few minutes before something starts, and switching
the TV to it when it starts ("erinnern und umschalten").

Three kinds, stored with the config entry (they survive restarts):
- program: one program, once
- series: every episode of a series on one channel (as far as the guide reaches)
- schedule: a time on given weekdays on one channel, once or every week
"""
from __future__ import annotations

import logging
import math
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import WEEKDAYS
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_REMINDER_LEAD,
    CONF_REMINDER_NOTIFY,
    DEFAULT_REMINDER_LEAD,
    DOMAIN,
    EVENT_REMINDER,
    REMINDER_KIND_PROGRAM,
    REMINDER_KIND_SCHEDULE,
    REMINDER_KIND_SERIES,
)

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1
TICK = timedelta(seconds=20)
# How long after its start a missed switch still happens (HA busy, restart).
START_GRACE = timedelta(minutes=2)
SCHEDULE_HORIZON_DAYS = 8
ACTION_SKIP = "WAIPU_REMINDER_SKIP"
ACTION_STOP = "WAIPU_REMINDER_STOP"

TEXTS = {
    "de": {
        "title": "waipu.tv",
        "switch": "In {min} Minuten schaltet der Fernseher auf {station}{program}",
        "remind": "In {min} Minuten auf {station}{program}",
        "now_switch": "Der Fernseher schaltet jetzt auf {station}{program}",
        "now_remind": "Jetzt auf {station}{program}",
        "skip": "Nicht umschalten",
        "stop": "Nicht mehr erinnern",
    },
    "en": {
        "title": "waipu.tv",
        "switch": "In {min} minutes the TV switches to {station}{program}",
        "remind": "In {min} minutes on {station}{program}",
        "now_switch": "The TV switches to {station}{program} now",
        "now_remind": "Now on {station}{program}",
        "skip": "Don't switch",
        "stop": "Stop reminding",
    },
}


@dataclass(frozen=True)
class Occurrence:
    """One coming start of a reminder."""

    reminder: dict[str, Any]
    start: datetime
    title: str | None
    program_id: str | None

    @property
    def key(self) -> str:
        return f"{self.reminder['id']}:{int(self.start.timestamp())}"


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


class ReminderManager:
    """Keeps the reminders, works out when each one comes up next and acts
    on it. One per config entry, reachable as ``coordinator.reminders``."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: Any) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._store: Store[dict[str, Any]] = Store(
            hass, STORE_VERSION, f"{DOMAIN}.reminders.{entry.entry_id}"
        )
        self.reminders: list[dict[str, Any]] = []
        self._skipped: set[str] = set()
        self._warned: set[str] = set()
        self._started: set[str] = set()
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[Callable[[], None]] = []
        self._signature: Any = None

    # --- lifecycle ---------------------------------------------------------
    async def async_start(self) -> None:
        data = await self._store.async_load() or {}
        self.reminders = list(data.get("reminders", []))
        self._skipped = set(data.get("skipped", []))
        self._unsubs.append(async_track_time_interval(self.hass, self._async_tick, TICK))
        self._unsubs.append(
            self.hass.bus.async_listen("mobile_app_notification_action", self._async_push_action)
        )
        self._unsubs.append(self.coordinator.async_add_listener(self._changed))

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        # Write now rather than after the save delay (reload, unload).
        await self._store.async_save(self._stored())

    @callback
    def async_add_listener(self, update: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update)
        return lambda: self._listeners.remove(update)

    @callback
    def _changed(self, force: bool = False) -> None:
        """Tell the sensor — only when what it shows actually moved."""
        sig = (repr(self.reminders), [o.key for o in self.upcoming(limit=10)], sorted(self._skipped))
        if not force and sig == self._signature:
            return
        self._signature = sig
        for update in list(self._listeners):
            update()

    def _stored(self) -> dict[str, Any]:
        return {"reminders": self.reminders, "skipped": sorted(self._skipped)}

    def _save(self) -> None:
        self._store.async_delay_save(self._stored, 1)
        self._changed(force=True)

    # --- editing -----------------------------------------------------------
    def get(self, reminder_id: str) -> dict[str, Any]:
        for r in self.reminders:
            if r["id"] == reminder_id:
                return r
        raise ServiceValidationError(f"Unbekannte Erinnerung: {reminder_id}")

    @callback
    def async_add(
        self,
        station_id: str,
        *,
        program_id: str | None = None,
        series: bool = False,
        at: time | None = None,
        days: list[str] | None = None,
        once: bool = False,
        switch: bool = True,
    ) -> dict[str, Any]:
        station = self.coordinator.station(station_id)
        if not station:
            raise ServiceValidationError(f"Sender unbekannt: {station_id}")
        base = {"station_id": station_id, "switch": switch, "enabled": True}
        if program_id:
            program = next((p for p in station.programs if p.id == program_id), None)
            if not program:
                raise ServiceValidationError(f"Sendung nicht im Programm: {program_id}")
            if series:
                if not program.series_id:
                    raise ServiceValidationError(f"{program.title} ist keine Serie")
                reminder = {**base, "kind": REMINDER_KIND_SERIES,
                            "series_id": program.series_id, "title": program.title}
            else:
                if program.start_time <= dt_util.utcnow():
                    raise ServiceValidationError(f"{program.title} läuft schon")
                reminder = {**base, "kind": REMINDER_KIND_PROGRAM, "program_id": program.id,
                            "title": program.title, "start": program.start_time.isoformat()}
        elif at is not None:
            reminder = {**base, "kind": REMINDER_KIND_SCHEDULE,
                        "time": at.strftime("%H:%M"), "days": list(days or WEEKDAYS), "once": once}
        else:
            raise ServiceValidationError("Entweder program_id oder time angeben")
        same = self._same(reminder)
        if same:
            same.update(switch=switch, enabled=True)
            self._save()
            return same
        reminder["id"] = uuid.uuid4().hex[:8]
        self.reminders.append(reminder)
        self._save()
        return reminder

    def _same(self, new: dict[str, Any]) -> dict[str, Any] | None:
        keys = {
            REMINDER_KIND_PROGRAM: ("program_id",),
            REMINDER_KIND_SERIES: ("series_id",),
            REMINDER_KIND_SCHEDULE: ("time", "days"),
        }[new["kind"]]
        return next(
            (
                r for r in self.reminders
                if r["kind"] == new["kind"] and r["station_id"] == new["station_id"]
                and all(r.get(k) == new.get(k) for k in keys)
            ),
            None,
        )

    @callback
    def async_update(
        self,
        reminder_id: str,
        *,
        enabled: bool | None = None,
        switch: bool | None = None,
        skip_next: bool | None = None,
    ) -> dict[str, Any]:
        reminder = self.get(reminder_id)
        if enabled is not None:
            reminder["enabled"] = enabled
        if switch is not None:
            reminder["switch"] = switch
        if skip_next is not None:
            nxt = next((o for o in self.upcoming() if o.reminder["id"] == reminder_id), None)
            if nxt:
                (self._skipped.add if skip_next else self._skipped.discard)(nxt.key)
        self._save()
        return reminder

    @callback
    def async_remove(self, reminder_id: str) -> None:
        reminder = self.get(reminder_id)
        self.reminders.remove(reminder)
        self._skipped = {k for k in self._skipped if not k.startswith(f"{reminder_id}:")}
        self._save()

    # --- when --------------------------------------------------------------
    def occurrences(self, reminder: dict[str, Any], since: datetime) -> list[Occurrence]:
        """Coming starts of one reminder, from `since` on."""
        if not reminder.get("enabled", True):
            return []
        station = self.coordinator.station(reminder["station_id"])
        programs = station.programs if station else []
        kind = reminder["kind"]
        if kind == REMINDER_KIND_PROGRAM:
            program = next((p for p in programs if p.id == reminder["program_id"]), None)
            start = program.start_time if program else dt_util.parse_datetime(reminder["start"])
            if start and start >= since:
                return [Occurrence(reminder, start, reminder.get("title"), reminder["program_id"])]
            return []
        if kind == REMINDER_KIND_SERIES:
            return [
                Occurrence(reminder, p.start_time, p.title, p.id)
                for p in programs
                if p.series_id == reminder["series_id"] and p.start_time >= since
            ]
        # Schedule: the given time on the given weekdays, local time.
        at = _parse_time(reminder["time"])
        days = {WEEKDAYS.index(d) for d in reminder.get("days") or WEEKDAYS}
        local = dt_util.as_local(since)
        found = []
        for offset in range(SCHEDULE_HORIZON_DAYS):
            day = (local + timedelta(days=offset)).date()
            if day.weekday() not in days:
                continue
            start = datetime.combine(day, at, tzinfo=local.tzinfo)
            start = dt_util.as_utc(start)
            if start < since:
                continue
            program = next((p for p in programs if p.start_time <= start < p.stop_time), None)
            found.append(Occurrence(reminder, start, program.title if program else None,
                                    program.id if program else None))
            if reminder.get("once"):
                break
        return found

    def upcoming(self, limit: int | None = None, since: datetime | None = None) -> list[Occurrence]:
        since = since or dt_util.utcnow()
        found = sorted(
            (o for r in self.reminders for o in self.occurrences(r, since)),
            key=lambda o: o.start,
        )
        return found[:limit] if limit else found

    def is_skipped(self, occ: Occurrence) -> bool:
        return occ.key in self._skipped

    # --- acting ------------------------------------------------------------
    @property
    def lead(self) -> timedelta:
        return timedelta(minutes=self.entry.options.get(CONF_REMINDER_LEAD, DEFAULT_REMINDER_LEAD))

    async def _async_tick(self, now: datetime | None = None) -> None:
        now = dt_util.utcnow()
        lead = self.lead
        for occ in self.upcoming(since=now - START_GRACE):
            if occ.key in self._skipped:
                # Skipped: no push, no switch; done once its start has passed.
                if occ.start <= now:
                    self._finish(occ)
                continue
            if occ.start - lead <= now < occ.start and occ.key not in self._warned:
                self._warned.add(occ.key)
                await self._async_announce(occ, starting=False)
            elif occ.start <= now and occ.key not in self._started:
                self._started.add(occ.key)
                if occ.key not in self._warned:
                    # No lead time, or the heads-up was missed: say it now.
                    await self._async_announce(occ, starting=True)
                self._warned.add(occ.key)
                await self._async_start(occ)
        self._changed()

    async def _async_start(self, occ: Occurrence) -> None:
        reminder = occ.reminder
        self._fire(occ, "start")
        if reminder.get("switch", True):
            from .media_player import async_tune  # import cycle

            try:
                await async_tune(self.hass, self.entry, self.coordinator, reminder["station_id"])
            except Exception as err:  # noqa: BLE001 — a reminder must not crash the tick
                _LOGGER.warning("Umschalten für Erinnerung %s fehlgeschlagen: %s", reminder["id"], err)
        self._finish(occ)

    @callback
    def _finish(self, occ: Occurrence) -> None:
        """After its start: one-offs end, the skip mark is used up."""
        reminder = occ.reminder
        self._skipped.discard(occ.key)
        if reminder["kind"] == REMINDER_KIND_PROGRAM and reminder in self.reminders:
            self.reminders.remove(reminder)
        elif reminder.get("once"):
            reminder["enabled"] = False
        # Keep the in-memory marks small.
        cutoff = int((dt_util.utcnow() - timedelta(hours=1)).timestamp())
        self._warned = {k for k in self._warned if int(k.rsplit(":", 1)[1]) > cutoff}
        self._started = {k for k in self._started if int(k.rsplit(":", 1)[1]) > cutoff}
        self._save()

    def _station_name(self, occ: Occurrence) -> str:
        station = self.coordinator.station(occ.reminder["station_id"])
        return station.display_name if station else occ.reminder["station_id"]

    def _fire(self, occ: Occurrence, phase: str) -> None:
        self.hass.bus.async_fire(
            EVENT_REMINDER,
            {
                "phase": phase,  # "upcoming" or "start"
                "reminder_id": occ.reminder["id"],
                "kind": occ.reminder["kind"],
                "station_id": occ.reminder["station_id"],
                "station": self._station_name(occ),
                "title": occ.title,
                "program_id": occ.program_id,
                "start": occ.start.isoformat(),
                "switch": occ.reminder.get("switch", True) and occ.key not in self._skipped,
            },
        )

    async def _async_announce(self, occ: Occurrence, starting: bool) -> None:
        if not starting:
            self._fire(occ, "upcoming")
        targets = self.entry.options.get(CONF_REMINDER_NOTIFY) or []
        if not targets:
            return
        text = TEXTS["de" if (self.hass.config.language or "").startswith("de") else "en"]
        switch = occ.reminder.get("switch", True)
        program = f": {occ.title}" if occ.title else ""
        key = ("now_switch" if switch else "now_remind") if starting else ("switch" if switch else "remind")
        message = text[key].format(
            min=max(math.ceil((occ.start - dt_util.utcnow()).total_seconds() / 60), 1),
            station=self._station_name(occ),
            program=program,
        )
        actions = []
        if switch and not starting:
            actions.append({"action": f"{ACTION_SKIP}:{occ.key}", "title": text["skip"]})
        one_off = occ.reminder["kind"] == REMINDER_KIND_PROGRAM or occ.reminder.get("once")
        if not one_off:
            actions.append({"action": f"{ACTION_STOP}:{occ.reminder['id']}", "title": text["stop"]})
        data: dict[str, Any] = {"title": text["title"], "message": message}
        if actions:
            data["data"] = {"actions": actions, "tag": f"waipu-reminder-{occ.reminder['id']}"}
        for target in targets:
            service = target.removeprefix("notify.")
            try:
                await self.hass.services.async_call("notify", service, data, blocking=False)
            except Exception as err:  # noqa: BLE001 — one bad target must not stop the rest
                _LOGGER.warning("Erinnerung an %s nicht gesendet: %s", target, err)

    async def _async_push_action(self, event: Event) -> None:
        action = str(event.data.get("action") or "")
        if action.startswith(f"{ACTION_SKIP}:"):
            self._skipped.add(action.split(":", 1)[1])
            self._save()
        elif action.startswith(f"{ACTION_STOP}:"):
            reminder_id = action.split(":", 1)[1]
            if any(r["id"] == reminder_id for r in self.reminders):
                self.async_update(reminder_id, enabled=False)

    # --- for the sensor ------------------------------------------------------
    def as_attributes(self) -> dict[str, Any]:
        nxt: dict[str, str] = {}
        upcoming = self.upcoming()
        for occ in upcoming:
            nxt.setdefault(occ.reminder["id"], occ.start.isoformat())
        reminders = []
        for r in self.reminders:
            station = self.coordinator.station(r["station_id"])
            reminders.append({**r, "station": station.display_name if station else r["station_id"],
                              "next": nxt.get(r["id"])})
        return {
            "reminders": reminders,
            "upcoming": [
                {
                    "reminder_id": o.reminder["id"],
                    "kind": o.reminder["kind"],
                    "station_id": o.reminder["station_id"],
                    "station": self._station_name(o),
                    "title": o.title,
                    "program_id": o.program_id,
                    "start": o.start.isoformat(),
                    "switch": o.reminder.get("switch", True),
                    "skipped": o.key in self._skipped,
                }
                for o in upcoming[:20]
            ],
        }

    @property
    def next_start(self) -> datetime | None:
        nxt = next((o for o in self.upcoming() if o.key not in self._skipped), None)
        return nxt.start if nxt else None
