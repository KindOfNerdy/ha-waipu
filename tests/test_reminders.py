"""Reminders: a push before something starts and switching the TV at its start."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.waipu.const import DOMAIN

from .test_android_tv import ZDF_PROGRAMS, _activities, _setup, remote_calls, waipu_api  # noqa: F401 - fixtures

NEXT = ZDF_PROGRAMS[1]  # "Krimi", series s9, starts in 30 minutes
NOTIFY = "mobile_app_phone"


@pytest.fixture
def pushes(hass):
    sent: list[dict] = []

    async def _notify(call):
        sent.append(dict(call.data))

    hass.services.async_register("notify", NOTIFY, _notify)
    return sent


def _sensor(hass):
    entity_id = next(
        e.entity_id
        for e in er.async_get(hass).entities.values()
        if e.platform == DOMAIN and e.translation_key == "reminders"
    )
    return hass.states.get(entity_id)


async def _add(hass, **data):
    result = await hass.services.async_call(
        DOMAIN, "add_reminder", data, blocking=True, return_response=True
    )
    return result["reminder"]


async def _tick_at(hass, coordinator, when):
    with patch.object(dt_util, "utcnow", return_value=when):
        await coordinator.reminders._async_tick()
        await hass.async_block_till_done()


async def test_program_reminder_pushes_then_switches(hass, waipu_api, remote_calls, pushes):
    _, coordinator = await _setup(hass, {"reminder_notify": [NOTIFY], "reminder_lead_minutes": 5})
    events = []
    hass.bus.async_listen("waipu_reminder", lambda e: events.append(e.data))
    reminder = await _add(hass, station_id="zdf", program_id=NEXT.id)
    assert reminder["kind"] == "program" and reminder["title"] == "Krimi"
    state = _sensor(hass)
    assert dt_util.parse_datetime(state.state) == NEXT.start_time.replace(microsecond=0)
    assert state.attributes["upcoming"][0]["station"] == "ZDF"

    await _tick_at(hass, coordinator, NEXT.start_time - timedelta(minutes=4, seconds=50))
    assert len(pushes) == 1
    assert pushes[0]["message"] == "In 5 minutes the TV switches to ZDF: Krimi"
    assert [a["title"] for a in pushes[0]["data"]["actions"]] == ["Don't switch"]
    assert events[-1]["phase"] == "upcoming"

    await _tick_at(hass, coordinator, NEXT.start_time + timedelta(seconds=10))
    assert _activities(remote_calls) == ["waipu://tv?id=zdf"]
    assert events[-1]["phase"] == "start"
    # A program reminder is done after its start.
    assert coordinator.reminders.reminders == []
    assert len(pushes) == 1


async def test_dont_switch_from_the_push(hass, waipu_api, remote_calls, pushes):
    _, coordinator = await _setup(hass, {"reminder_notify": [NOTIFY]})
    await _add(hass, station_id="zdf", program_id=NEXT.id)
    await _tick_at(hass, coordinator, NEXT.start_time - timedelta(minutes=4))
    skip = pushes[0]["data"]["actions"][0]["action"]
    hass.bus.async_fire("mobile_app_notification_action", {"action": skip})
    await hass.async_block_till_done()
    await _tick_at(hass, coordinator, NEXT.start_time + timedelta(seconds=10))
    assert remote_calls == []
    assert coordinator.reminders.reminders == []


async def test_only_remind_never_switches(hass, waipu_api, remote_calls, pushes):
    _, coordinator = await _setup(hass, {"reminder_notify": [NOTIFY]})
    await _add(hass, station_id="zdf", program_id=NEXT.id, switch=False)
    await _tick_at(hass, coordinator, NEXT.start_time - timedelta(minutes=4, seconds=50))
    assert pushes[0]["message"] == "In 5 minutes on ZDF: Krimi"
    assert "data" not in pushes[0]  # one-off without switching: nothing to tap
    await _tick_at(hass, coordinator, NEXT.start_time + timedelta(seconds=10))
    assert remote_calls == []


async def test_series_reminder_and_stop_from_the_push(hass, waipu_api, remote_calls, pushes):
    _, coordinator = await _setup(hass, {"reminder_notify": [NOTIFY]})
    reminder = await _add(hass, station_id="zdf", program_id=NEXT.id, series=True)
    assert reminder["kind"] == "series" and reminder["series_id"] == "s9"
    # Adding it again doesn't make a second one.
    await _add(hass, station_id="zdf", program_id=NEXT.id, series=True)
    assert len(coordinator.reminders.reminders) == 1
    await _tick_at(hass, coordinator, NEXT.start_time - timedelta(minutes=4))
    titles = [a["title"] for a in pushes[0]["data"]["actions"]]
    assert titles == ["Don't switch", "Stop reminding"]
    hass.bus.async_fire("mobile_app_notification_action", {"action": pushes[0]["data"]["actions"][1]["action"]})
    await hass.async_block_till_done()
    assert coordinator.reminders.reminders[0]["enabled"] is False
    await _tick_at(hass, coordinator, NEXT.start_time + timedelta(seconds=10))
    assert remote_calls == []


async def test_schedule_once_switches_then_turns_off(hass, waipu_api, remote_calls, pushes):
    _, coordinator = await _setup(hass)
    start = dt_util.as_local(dt_util.utcnow() + timedelta(hours=2)).replace(second=0, microsecond=0)
    day = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][start.weekday()]
    reminder = await _add(hass, station_id="ard", time=start.strftime("%H:%M:00"), days=[day], once=True)
    assert reminder["kind"] == "schedule" and reminder["days"] == [day]
    nxt = coordinator.reminders.upcoming()[0]
    assert nxt.start == dt_util.as_utc(start)
    await _tick_at(hass, coordinator, nxt.start + timedelta(seconds=5))
    assert _activities(remote_calls) == ["waipu://tv?id=ard"]
    assert pushes == []  # no push target configured
    assert coordinator.reminders.reminders[0]["enabled"] is False


async def test_skip_next_and_remove(hass, waipu_api, remote_calls):
    _, coordinator = await _setup(hass)
    reminder = await _add(hass, station_id="zdf", program_id=NEXT.id, series=True)
    await hass.services.async_call(
        DOMAIN, "update_reminder", {"reminder_id": reminder["id"], "skip_next": True}, blocking=True
    )
    assert _sensor(hass).attributes["upcoming"][0]["skipped"] is True
    await _tick_at(hass, coordinator, NEXT.start_time + timedelta(seconds=10))
    assert remote_calls == []
    await hass.services.async_call(DOMAIN, "remove_reminder", {"reminder_id": reminder["id"]}, blocking=True)
    assert _sensor(hass).attributes["reminders"] == []


async def test_reminders_survive_a_reload(hass, waipu_api, remote_calls):
    entry, _ = await _setup(hass)
    await _add(hass, station_id="ard", time="20:15:00", days=["mon", "fri"])
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    reminders = entry.runtime_data.reminders.reminders
    assert [(r["time"], r["days"]) for r in reminders] == [("20:15", ["mon", "fri"])]


async def test_program_that_already_runs_is_refused(hass, waipu_api, remote_calls):
    from homeassistant.exceptions import ServiceValidationError

    await _setup(hass)
    with pytest.raises(ServiceValidationError):
        await _add(hass, station_id="zdf", program_id=ZDF_PROGRAMS[0].id)
