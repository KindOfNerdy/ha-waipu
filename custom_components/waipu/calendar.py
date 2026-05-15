"""Calendar platform: scheduled / running / finished cloud recordings."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Recording
from .const import DOMAIN
from .coordinator import WaipuCoordinator
from .entity import WaipuEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WaipuCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data and coordinator.data.has_dvr:
        async_add_entities([WaipuRecordingsCalendar(coordinator)])


class WaipuRecordingsCalendar(WaipuEntity, CalendarEntity):
    _attr_icon = "mdi:movie-roll"
    _attr_name = "Aufnahmen"

    def __init__(self, coordinator: WaipuCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_recordings"

    @property
    def event(self) -> CalendarEvent | None:
        upcoming = sorted(
            (r for r in self._recordings()
             if r.recording_start_time and r.status in ("SCHEDULED", "RECORDING")),
            key=lambda r: r.recording_start_time,  # type: ignore[arg-type, return-value]
        )
        return _to_event(upcoming[0]) if upcoming else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for rec in self._recordings():
            if not rec.recording_start_time:
                continue
            end = rec.recording_start_time + rec.duration
            if rec.recording_start_time < end_date and end > start_date:
                events.append(_to_event(rec))
        return events

    def _recordings(self) -> list[Recording]:
        if not self.coordinator.data:
            return []
        return list(self.coordinator.data.recordings)


def _to_event(rec: Recording) -> CalendarEvent:
    start = rec.recording_start_time
    end = (start + rec.duration) if start else None
    summary = rec.title or "Aufnahme"
    if rec.episode_title:
        summary = f"{summary} – {rec.episode_title}"
    desc_parts: list[str] = []
    if rec.status:
        desc_parts.append(f"Status: {rec.status}")
    if rec.station_display:
        desc_parts.append(f"Sender: {rec.station_display}")
    if rec.season and rec.episode:
        desc_parts.append(f"S{rec.season}E{rec.episode}")
    if rec.position_percentage:
        desc_parts.append(f"Fortschritt: {rec.position_percentage}%")
    return CalendarEvent(
        start=start,  # type: ignore[arg-type]
        end=end,  # type: ignore[arg-type]
        summary=summary,
        description="\n".join(desc_parts) or None,
        uid=rec.id,
        location=rec.station_display,
    )
