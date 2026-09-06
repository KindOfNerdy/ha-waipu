"""Calendar platform: scheduled / running / finished cloud recordings."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
        # Grouped with the media_player device ("waipu Steuerung"), not the
        # shared per-channel "Senderübersicht" device — managing recordings
        # is a control surface, and this sits next to the "Aufnahmen öffnen
        # (Android TV)" shortcut button rather than in the ~90-entity
        # per-channel device card.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_player")},
            name="waipu Steuerung",
            manufacturer="Exaring AG",
            model="waipu.tv",
            configuration_url="https://www.waipu.tv/",
        )

    @property
    def event(self) -> CalendarEvent | None:
        rec = self._next_recording()
        return _to_event(rec, self.coordinator) if rec else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Structured fields for the same recording `event` describes —
        one clean attribute per fact, instead of only the freetext
        `description` HA derives from CalendarEvent for the popup."""
        rec = self._next_recording()
        if not rec:
            return {}
        attrs: dict[str, Any] = {
            "recording_id": rec.id,
            "program_id": rec.program_id,
            "station_id": rec.station_id,
            "station_display": rec.station_display,
            "status": rec.status,
            "episode_title": rec.episode_title,
            "season": rec.season,
            "episode": rec.episode,
            "genre": rec.genre,
            "position_percentage": rec.position_percentage,
            "fully_watched": rec.fully_watched,
            "partially_watched": rec.partially_watched,
            "is_new": rec.is_new,
        }
        if rec.program_id:
            detail = self.coordinator.program_detail(rec.program_id)
            if detail:
                attrs["description"] = detail.description
                attrs["parental_guidance"] = detail.parental_guidance
                attrs["rerun"] = detail.rerun
        return attrs

    def _next_recording(self) -> Recording | None:
        upcoming = sorted(
            (r for r in self._recordings()
             if r.recording_start_time and r.status in ("SCHEDULED", "RECORDING")),
            key=lambda r: r.recording_start_time,  # type: ignore[arg-type, return-value]
        )
        return upcoming[0] if upcoming else None

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
                events.append(_to_event(rec, self.coordinator))
        return events

    def _recordings(self) -> list[Recording]:
        if not self.coordinator.data:
            return []
        return list(self.coordinator.data.recordings)


def _to_event(rec: Recording, coordinator: WaipuCoordinator) -> CalendarEvent:
    start = rec.recording_start_time
    end = (start + rec.duration) if start else None
    summary = rec.title or "Aufnahme"
    if rec.episode_title:
        summary = f"{summary} – {rec.episode_title}"
    desc_parts: list[str] = []
    if rec.episode_title:
        desc_parts.append(rec.episode_title)
    if rec.program_id:
        detail = coordinator.program_detail(rec.program_id)
        if detail and detail.description:
            desc_parts.append(detail.description)
    if rec.status:
        desc_parts.append(f"Status: {rec.status}")
    if rec.station_display:
        desc_parts.append(f"Sender: {rec.station_display}")
    if rec.season and rec.episode:
        desc_parts.append(f"S{rec.season}E{rec.episode}")
    if rec.position_percentage:
        desc_parts.append(f"Fortschritt: {rec.position_percentage}%")
    if rec.fully_watched:
        desc_parts.append("Angesehen")
    elif rec.partially_watched:
        desc_parts.append("Teilweise angesehen")
    elif rec.is_new:
        desc_parts.append("Neu")
    return CalendarEvent(
        start=start,  # type: ignore[arg-type]
        end=end,  # type: ignore[arg-type]
        summary=summary,
        description="\n".join(desc_parts) or None,
        uid=rec.id,
        location=rec.station_display,
    )
