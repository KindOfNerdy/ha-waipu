"""Program/Station live-selection logic — what sensor.py's 'jetzt'/'danach'
sensors and the boundary-timer feature (v1.4.7) both build on top of."""
from datetime import datetime, timedelta, timezone

from .helpers import api


def _program(id_, start, stop, **kw):
    return api.Program(
        id=id_,
        title=kw.pop("title", id_),
        start_time=start,
        stop_time=stop,
        station_id=kw.pop("station_id", "ard"),
        **kw,
    )


def _station(programs):
    return api.Station(
        id="ard",
        display_name="ARD",
        description=None,
        logo_template_url=None,
        stream_qualities=(),
        recording_forbidden=False,
        programs=tuple(programs),
    )


T0 = datetime(2026, 1, 15, 20, 0, tzinfo=timezone.utc)


class TestProgramLiveNow:
    def test_is_live_now_at_start(self):
        p = _program("p1", T0, T0 + timedelta(minutes=15))
        assert p.is_live_now(T0) is True

    def test_is_live_now_just_before_stop(self):
        p = _program("p1", T0, T0 + timedelta(minutes=15))
        assert p.is_live_now(T0 + timedelta(minutes=14, seconds=59)) is True

    def test_not_live_at_stop_boundary(self):
        """stop_time is exclusive — the program ends exactly then."""
        p = _program("p1", T0, T0 + timedelta(minutes=15))
        assert p.is_live_now(T0 + timedelta(minutes=15)) is False

    def test_not_live_before_start(self):
        p = _program("p1", T0, T0 + timedelta(minutes=15))
        assert p.is_live_now(T0 - timedelta(seconds=1)) is False

    def test_duration(self):
        p = _program("p1", T0, T0 + timedelta(minutes=15))
        assert p.duration == timedelta(minutes=15)


class TestStationCurrentProgram:
    def test_returns_the_airing_program(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        p2 = _program("p2", T0 + timedelta(minutes=15), T0 + timedelta(minutes=30))
        st = _station([p1, p2])
        assert st.current_program(T0 + timedelta(minutes=5)).id == "p1"
        assert st.current_program(T0 + timedelta(minutes=20)).id == "p2"

    def test_none_in_a_gap(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        p2 = _program("p2", T0 + timedelta(minutes=20), T0 + timedelta(minutes=30))
        st = _station([p1, p2])
        assert st.current_program(T0 + timedelta(minutes=17)) is None

    def test_none_with_no_programs(self):
        assert _station([]).current_program(T0) is None


class TestStationNextProgram:
    def test_returns_soonest_future_program(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        p2 = _program("p2", T0 + timedelta(minutes=15), T0 + timedelta(minutes=30))
        p3 = _program("p3", T0 + timedelta(minutes=30), T0 + timedelta(minutes=45))
        # Deliberately out of order — next_program must sort, not assume order.
        st = _station([p3, p1, p2])
        assert st.next_program(T0 + timedelta(minutes=5)).id == "p2"

    def test_none_when_nothing_upcoming(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        st = _station([p1])
        assert st.next_program(T0 + timedelta(minutes=20)) is None

    def test_currently_airing_program_is_not_next(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        st = _station([p1])
        assert st.next_program(T0 + timedelta(minutes=5)) is None


class TestStationUpcomingPrograms:
    def test_excludes_the_immediate_next(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        p2 = _program("p2", T0 + timedelta(minutes=15), T0 + timedelta(minutes=30))
        p3 = _program("p3", T0 + timedelta(minutes=30), T0 + timedelta(minutes=45))
        st = _station([p1, p2, p3])
        upcoming = st.upcoming_programs(T0 + timedelta(minutes=5))
        assert [p.id for p in upcoming] == ["p3"]

    def test_empty_when_only_one_future_program(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        p2 = _program("p2", T0 + timedelta(minutes=15), T0 + timedelta(minutes=30))
        st = _station([p1, p2])
        assert st.upcoming_programs(T0 + timedelta(minutes=5)) == ()

    def test_sorted_by_start_time_regardless_of_input_order(self):
        p1 = _program("p1", T0, T0 + timedelta(minutes=15))
        p2 = _program("p2", T0 + timedelta(minutes=15), T0 + timedelta(minutes=30))
        p3 = _program("p3", T0 + timedelta(minutes=30), T0 + timedelta(minutes=45))
        p4 = _program("p4", T0 + timedelta(minutes=45), T0 + timedelta(minutes=60))
        st = _station([p4, p1, p3, p2])
        upcoming = st.upcoming_programs(T0 + timedelta(minutes=5))
        assert [p.id for p in upcoming] == ["p3", "p4"]


def _named_station(station_id, programs):
    return api.Station(
        id=station_id,
        display_name=station_id.upper(),
        description=None,
        logo_template_url=None,
        stream_qualities=(),
        recording_forbidden=False,
        programs=tuple(programs),
    )


class TestMatchStationByTitle:
    """What the Cast follower (cast_follow.py) uses to turn the TV's
    program title back into a channel."""

    def _stations(self):
        return [
            _named_station("prosieben", [
                _program("a", T0, T0 + timedelta(hours=2), title="Wer stiehlt mir die Show?"),
            ]),
            _named_station("ndr_hh", [
                _program("b", T0, T0 + timedelta(minutes=30), title="Hallo Niedersachsen"),
            ]),
            _named_station("ndr_nds", [
                _program("c", T0, T0 + timedelta(minutes=30), title="Hallo Niedersachsen"),
            ]),
            _named_station("ard", [
                _program("d", T0 - timedelta(hours=1), T0, title="Tagesschau"),
                _program("e", T0, T0 + timedelta(minutes=90), title="Tatort"),
            ]),
        ]

    def test_unique_title_matches(self):
        assert api.match_station_by_title(
            self._stations(), "Wer stiehlt mir die Show?", ref=T0 + timedelta(minutes=5)
        ) == "prosieben"

    def test_case_and_whitespace_insensitive(self):
        assert api.match_station_by_title(
            self._stations(), "  wer STIEHLT mir  die show? ", ref=T0 + timedelta(minutes=5)
        ) == "prosieben"

    def test_unknown_title_is_none(self):
        assert api.match_station_by_title(
            self._stations(), "Watzmann ermittelt", ref=T0 + timedelta(minutes=5)
        ) is None

    def test_empty_title_is_none(self):
        assert api.match_station_by_title(self._stations(), None) is None
        assert api.match_station_by_title(self._stations(), "   ") is None

    def test_ambiguous_title_without_preferred_is_none(self):
        assert api.match_station_by_title(
            self._stations(), "Hallo Niedersachsen", ref=T0 + timedelta(minutes=5)
        ) is None

    def test_ambiguous_title_keeps_preferred(self):
        assert api.match_station_by_title(
            self._stations(),
            "Hallo Niedersachsen",
            preferred="ndr_nds",
            ref=T0 + timedelta(minutes=5),
        ) == "ndr_nds"

    def test_preferred_ignored_when_not_among_hits(self):
        assert api.match_station_by_title(
            self._stations(),
            "Wer stiehlt mir die Show?",
            preferred="ard",
            ref=T0 + timedelta(minutes=5),
        ) == "prosieben"

    def test_program_far_from_now_does_not_match(self):
        # "Tagesschau" ended at T0; an hour later it no longer counts.
        assert api.match_station_by_title(
            self._stations(), "Tagesschau", ref=T0 + timedelta(hours=1)
        ) is None

    def test_tolerance_around_program_change(self):
        # The TV may flip to the next title a little before the EPG does.
        just_before = T0 - timedelta(minutes=1)
        assert api.match_station_by_title(self._stations(), "Tatort", ref=just_before) == "ard"
        just_after = T0 + timedelta(minutes=1)
        assert api.match_station_by_title(self._stations(), "Tagesschau", ref=just_after) == "ard"
