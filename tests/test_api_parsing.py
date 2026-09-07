"""Payload-to-dataclass parsing — the core of the reverse-engineered API
surface. Field names below (startTime, seriesId, ...) come straight from
observed waipu responses; a rename on their side would show up here."""
from .helpers import api


class TestProgramFromGrid:
    def _payload(self, **overrides):
        base = {
            "id": "prog-1",
            "title": "Tagesschau",
            "startTime": "2026-01-15T20:00:00Z",
            "stopTime": "2026-01-15T20:15:00Z",
            "episodeTitle": "Folge 42",
            "genreDisplayName": "Nachrichten",
            "previewImage": "https://img/${resolution}/x.jpg",
            "seriesId": 12345,
            "recordingForbidden": True,
        }
        base.update(overrides)
        return base

    def test_full_payload(self):
        p = api._program_from_grid(self._payload(), "ard")
        assert p.id == "prog-1"
        assert p.title == "Tagesschau"
        assert p.station_id == "ard"
        assert p.episode_title == "Folge 42"
        assert p.genre == "Nachrichten"
        assert p.preview_image == "https://img/480x270/x.jpg"  # DEFAULT_IMAGE_RESOLUTION
        assert p.series_id == "12345"  # int coerced to str
        assert p.recording_forbidden is True

    def test_minimal_payload_defaults(self):
        p = api._program_from_grid(
            {"id": 1, "startTime": "2026-01-15T20:00:00Z", "stopTime": "2026-01-15T20:15:00Z"},
            "zdf",
        )
        assert p.id == "1"
        assert p.title == ""
        assert p.episode_title is None
        assert p.series_id is None
        assert p.recording_forbidden is False

    def test_genre_falls_back_to_raw_genre(self):
        p = api._program_from_grid(self._payload(genre="raw-genre", genreDisplayName=None), "ard")
        assert p.genre == "raw-genre"


class TestProgramDetailFromDict:
    def test_prefers_long_description(self):
        d = api._program_detail_from_dict(
            {
                "id": "p1",
                "textContent": {"descLong": "long text", "descShort": "short text"},
                "ageRating": {"parentalGuidance": "fsk-16", "pinRequired": True},
                "rerun": True,
            }
        )
        assert d.description == "long text"
        assert d.parental_guidance == "fsk-16"
        assert d.pin_required is True
        assert d.rerun is True

    def test_falls_back_to_short_description(self):
        d = api._program_detail_from_dict(
            {"id": "p1", "textContent": {"descShort": "short text"}}
        )
        assert d.description == "short text"

    def test_missing_nested_objects(self):
        d = api._program_detail_from_dict({"id": "p1"})
        assert d.description is None
        assert d.parental_guidance is None
        assert d.pin_required is False
        assert d.rerun is False


class TestRecordingFromDict:
    def _payload(self, **overrides):
        base = {
            "id": "rec-1",
            "programId": "prog-1",
            "stationId": "ard",
            "title": "Tatort",
            "status": "FINISHED",
            "recordingStartTime": "2026-01-15T20:15:00Z",
            "durationSeconds": 5400,
            "seriesId": "104121",
            "isNew": True,
            "fullyWatched": False,
            "partiallyWatched": True,
            "positionPercentage": 42,
        }
        base.update(overrides)
        return base

    def test_full_payload(self):
        r = api._recording_from_dict(self._payload())
        assert r.id == "rec-1"
        assert r.program_id == "prog-1"
        assert r.status == "FINISHED"
        assert r.duration_seconds == 5400
        assert r.series_id == "104121"
        assert r.is_new is True
        assert r.fully_watched is False
        assert r.partially_watched is True
        assert r.position_percentage == 42

    def test_minimal_payload_defaults(self):
        r = api._recording_from_dict({"id": "rec-2"})
        assert r.program_id is None
        assert r.station_id == ""
        assert r.status == ""
        assert r.duration_seconds == 0
        assert r.is_new is False
        assert r.recording_group is None


class TestSerialRecordingFromDict:
    def test_full_payload(self):
        s = api._serial_recording_from_dict(
            {"id": "serial-1", "channel": "ard", "title": "Tatort", "seriesId": 104121}
        )
        assert s.id == "serial-1"
        assert s.channel == "ard"
        assert s.series_id == "104121"

    def test_minimal_payload(self):
        s = api._serial_recording_from_dict({"id": "serial-2"})
        assert s.channel is None
        assert s.title is None
        assert s.series_id is None


class TestAsStr:
    def test_none(self):
        assert api._as_str(None) is None

    def test_int_coerced(self):
        assert api._as_str(104121) == "104121"

    def test_blank_string_becomes_none(self):
        assert api._as_str("   ") is None

    def test_strips_whitespace(self):
        assert api._as_str("  ard  ") == "ard"
