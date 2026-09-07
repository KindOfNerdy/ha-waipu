"""Datetime/slot helpers in api.py — the most reverse-engineering-prone,
least "self-evidently correct" part of the client."""
from datetime import datetime, timedelta, timezone

import pytest

from .helpers import api


class TestParseDt:
    def test_z_suffix(self):
        dt = api._parse_dt("2026-01-15T20:00:00Z")
        assert dt == datetime(2026, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

    def test_colon_offset(self):
        dt = api._parse_dt("2026-01-15T20:00:00+02:00")
        assert dt.utcoffset() == timedelta(hours=2)
        assert dt.astimezone(timezone.utc) == datetime(2026, 1, 15, 18, 0, 0, tzinfo=timezone.utc)

    def test_no_colon_offset(self):
        """waipu's recordings endpoint uses '+0100' without a colon."""
        dt = api._parse_dt("2026-01-15T20:00:00+0100")
        assert dt.utcoffset() == timedelta(hours=1)

    def test_negative_no_colon_offset(self):
        dt = api._parse_dt("2026-01-15T20:00:00-0500")
        assert dt.utcoffset() == timedelta(hours=-5)

    def test_naive_defaults_to_utc(self):
        dt = api._parse_dt("2026-01-15T20:00:00")
        assert dt.tzinfo == timezone.utc

    def test_malformed_raises(self):
        with pytest.raises(api.WaipuApiError):
            api._parse_dt("not-a-date")


class TestParseOptionalDt:
    def test_none(self):
        assert api._parse_optional_dt(None) is None

    def test_empty_string(self):
        assert api._parse_optional_dt("") is None

    def test_valid(self):
        assert api._parse_optional_dt("2026-01-15T20:00:00Z") is not None

    def test_malformed_swallowed(self):
        """Unlike _parse_dt, the optional variant never raises."""
        assert api._parse_optional_dt("garbage") is None


class TestSlotStartFor:
    @pytest.mark.parametrize(
        "hour,expected_hour",
        [(0, 0), (3, 0), (4, 4), (5, 4), (19, 16), (20, 20), (23, 20)],
    )
    def test_rounds_down_to_4h_boundary(self, hour, expected_hour):
        ts = datetime(2026, 1, 15, hour, 37, 12, tzinfo=timezone.utc)
        result = api.slot_start_for(ts)
        assert result == datetime(2026, 1, 15, expected_hour, 0, 0, tzinfo=timezone.utc)

    def test_converts_non_utc_input(self):
        # 01:30 in +02:00 is 23:30 UTC the previous day -> slot 20:00 UTC
        ts = datetime(2026, 1, 16, 1, 30, tzinfo=timezone(timedelta(hours=2)))
        result = api.slot_start_for(ts)
        assert result == datetime(2026, 1, 15, 20, 0, 0, tzinfo=timezone.utc)


class TestSlotsCovering:
    def test_single_slot_fully_inside(self):
        start = datetime(2026, 1, 15, 5, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 15, 7, 0, tzinfo=timezone.utc)
        assert api.slots_covering(start, end) == [datetime(2026, 1, 15, 4, 0, tzinfo=timezone.utc)]

    def test_spans_two_slots(self):
        start = datetime(2026, 1, 15, 3, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 15, 5, 0, tzinfo=timezone.utc)
        assert api.slots_covering(start, end) == [
            datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 15, 4, 0, tzinfo=timezone.utc),
        ]

    def test_exact_boundary_end_is_exclusive(self):
        start = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 15, 4, 0, tzinfo=timezone.utc)
        assert api.slots_covering(start, end) == [datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)]

    def test_crosses_midnight(self):
        start = datetime(2026, 1, 15, 22, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 16, 2, 0, tzinfo=timezone.utc)
        assert api.slots_covering(start, end) == [
            datetime(2026, 1, 15, 20, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 16, 0, 0, tzinfo=timezone.utc),
        ]

    def test_empty_when_end_before_starts_slot(self):
        # Not "end before start" in general — slots_covering only checks
        # `end` against start's *rounded-down* slot boundary, so an `end`
        # inside that same slot still yields it (see the dedicated test
        # below). Genuinely empty requires end before the slot itself.
        start = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)  # slot: 08:00
        end = datetime(2026, 1, 15, 7, 0, tzinfo=timezone.utc)
        assert api.slots_covering(start, end) == []

    def test_end_inside_starts_own_slot_still_yields_it(self):
        start = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)  # slot: 08:00
        end = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        assert api.slots_covering(start, end) == [datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc)]

    def test_realistic_six_hour_lookahead_spans_two_or_three_slots(self):
        """Matches the fixed EPG_LOOKAHEAD window in const.py — sanity
        check that the request-volume assumptions discussed for the EPG
        cache feature actually hold."""
        now = datetime(2026, 1, 15, 9, 12, tzinfo=timezone.utc)
        start = now - timedelta(minutes=30)
        end = now + timedelta(hours=6)
        assert 2 <= len(api.slots_covering(start, end)) <= 3


class TestFormatSlot:
    def test_formats_as_utc_z(self):
        ts = datetime(2026, 1, 15, 4, 0, tzinfo=timezone(timedelta(hours=2)))
        assert api.format_slot(ts) == "2026-01-15T02:00:00Z"


class TestFillImageUrl:
    def test_none_passthrough(self):
        assert api.fill_image_url(None) is None

    def test_replaces_placeholder(self):
        assert api.fill_image_url("https://img/${resolution}/x.jpg", resolution="640x360") == (
            "https://img/640x360/x.jpg"
        )

    def test_default_resolution_used(self):
        result = api.fill_image_url("https://img/${resolution}/x.jpg")
        assert "${resolution}" not in result
