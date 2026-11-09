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


def _rec(rec_id, title, *, episode_title=None, status="FINISHED", days_ago=1,
         partially_watched=False, fully_watched=False, image=None):
    return api.Recording(
        id=rec_id,
        program_id=None,
        station_id="prosieben",
        station_display="ProSieben",
        title=title,
        status=status,
        recording_start_time=T0 - timedelta(days=days_ago),
        duration_seconds=7200,
        episode_title=episode_title,
        partially_watched=partially_watched,
        fully_watched=fully_watched,
        preview_image=image,
    )


# Image URLs as Cast reported them on 2026-11-09.
EPG_IMAGE = "https://images.wpstr.tv/image/fetch/s-xyz=//https%3A%2F%2Fcdn.images.simply.tv%2F1?res=640x360"
VOD_IMAGE = "https://images.wpstr.tv/vod/78/987e_0_MOVIE.png?res=640x360"


class TestClassifyCastPlayback:
    """Live channel vs. recording vs. waiputhek, from what the TV's Cast
    entity reports (values as seen live on 2026-11-09)."""

    def _stations(self):
        return TestMatchStationByTitle()._stations()

    def _recordings(self):
        return [
            _rec("r-jenke", "JENKE"),
            _rec("r-tatort", "Tatort"),
            _rec("r-sched", "Otto - Der Film", status="SCHEDULED"),
        ]

    def _classify(self, cast, now=T0 + timedelta(minutes=5), **kw):
        return api.classify_cast_playback(
            self._stations(), self._recordings(), cast, now=now, **kw
        )

    def test_live_position_is_timestamp_and_matches_epg(self):
        now = T0 + timedelta(minutes=5)
        cast = api.CastPlayback("Wer stiehlt mir die Show?", position=now.timestamp(),
                                position_updated_at=now)
        assert self._classify(cast, now) == api.LivePlayback("prosieben")

    def test_restart_matches_program_at_watched_time(self):
        # Watching "Tagesschau" (ended at T0) 20 minutes behind live.
        now = T0 + timedelta(minutes=10)
        watched = T0 - timedelta(minutes=10)
        cast = api.CastPlayback("Tagesschau", position=watched.timestamp(),
                                position_updated_at=now)
        result = self._classify(cast, now)
        assert result == api.LivePlayback("ard", timeshift=timedelta(minutes=20))

    def test_watched_time_advances_while_playing(self):
        now = T0 + timedelta(minutes=10)
        cast = api.CastPlayback("x", position=(T0 - timedelta(minutes=10)).timestamp(),
                                position_updated_at=T0, playing=True)
        assert cast.watched_time(now) == T0
        paused = api.CastPlayback("x", position=(T0 - timedelta(minutes=10)).timestamp(),
                                  position_updated_at=T0, playing=False)
        assert paused.watched_time(now) == T0 - timedelta(minutes=10)

    def test_stream_latency_is_not_timeshift(self):
        now = T0 + timedelta(minutes=5)
        cast = api.CastPlayback("Wer stiehlt mir die Show?",
                                position=(now - timedelta(seconds=20)).timestamp(),
                                position_updated_at=now)
        assert self._classify(cast, now) == api.LivePlayback("prosieben")

    def test_resumed_recording_with_trailing_dot(self):
        # "JENKE." resumed at 625 s of 7361 s.
        cast = api.CastPlayback("JENKE.", position=625.7, duration=7361.7, image=EPG_IMAGE)
        result = self._classify(cast)
        assert isinstance(result, api.OnDemandPlayback)
        assert result.kind == api.PLAYBACK_RECORDING
        assert result.recording.id == "r-jenke"
        assert result.image == EPG_IMAGE  # recording has none of its own

    def test_recording_wins_over_live_program_of_same_title(self):
        # "Tatort" airs live on ARD right now, but Cast says on demand.
        cast = api.CastPlayback("Tatort", position=10.0, duration=5400.0, image=EPG_IMAGE)
        result = self._classify(cast)
        assert result.kind == api.PLAYBACK_RECORDING
        assert result.recording.id == "r-tatort"

    def test_waiputhek_by_vod_image(self):
        cast = api.CastPlayback("Otto - Der Film", position=7.8, duration=4977.2,
                                image=VOD_IMAGE)
        result = self._classify(cast)
        # The scheduled recording of the same name is not playable — VOD.
        assert result == api.OnDemandPlayback(api.PLAYBACK_VOD, "Otto - Der Film",
                                              image=VOD_IMAGE)

    def test_on_demand_without_any_match_is_tentative_vod(self):
        cast = api.CastPlayback("Ganz neue Aufnahme", position=3.0, duration=1800.0,
                                image=EPG_IMAGE)
        result = self._classify(cast)
        assert result.kind == api.PLAYBACK_VOD
        assert result.tentative

    def test_live_title_not_in_epg_yet_is_none(self):
        now = T0 + timedelta(minutes=5)
        cast = api.CastPlayback("Sondersendung", position=now.timestamp())
        assert self._classify(cast, now) is None

    def test_without_position_info_falls_back_to_epg_then_recordings(self):
        assert self._classify(api.CastPlayback("Wer stiehlt mir die Show?")) == \
            api.LivePlayback("prosieben")
        assert self._classify(api.CastPlayback("JENKE")).kind == api.PLAYBACK_RECORDING
        assert self._classify(api.CastPlayback("Watzmann ermittelt")) is None


class TestMatchRecordingByTitle:
    def test_episode_title_matches_too(self):
        recs = [_rec("a", "Tatort", episode_title="Der Fluch des Geldes")]
        assert api.match_recording_by_title(recs, "Der Fluch des Geldes").id == "a"

    def test_several_episodes_prefer_started_then_newest(self):
        recs = [
            _rec("old", "Akte X", days_ago=9),
            _rec("new", "Akte X", days_ago=1),
            _rec("started", "Akte X", days_ago=5, partially_watched=True),
        ]
        assert api.match_recording_by_title(recs, "Akte X").id == "started"
        assert api.match_recording_by_title(recs[:2], "Akte X").id == "new"

    def test_scheduled_is_ignored(self):
        assert api.match_recording_by_title([_rec("s", "X", status="SCHEDULED")], "X") is None
