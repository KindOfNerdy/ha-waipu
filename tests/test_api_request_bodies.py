"""Exact wire-format regression tests for every write call in api.py —
verified 2026-09-07 against the current waipu web bundle (play.waipu.tv).
Caught two real bugs this way: delete_recordings sent 'recordingIds'
instead of the required 'ids' (causing every waipu.delete_recording call
to 404), and create_recording sent a bogus 'stationId' field the real
API never uses (harmless, but wrong)."""
import asyncio
from unittest.mock import AsyncMock

from .helpers import api


def _client() -> "api.WaipuClient":
    # Session is never touched — _request_json is mocked out below, so a
    # placeholder is fine.
    return api.WaipuClient(session=object(), device_id="device-1")


def _call_kwargs(mock: AsyncMock) -> dict:
    _, kwargs = mock.call_args
    return kwargs


class TestDeleteRecordingsBody:
    def test_body_uses_ids_key(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(client.delete_recordings(["123", "456"]))
        kwargs = _call_kwargs(client._request_json)
        assert kwargs["body"] == {"ids": ["123", "456"]}

    def test_empty_list_short_circuits_without_a_request(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(client.delete_recordings([]))
        client._request_json.assert_not_awaited()

    def test_method_and_url(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(client.delete_recordings(["123"]))
        args, _ = client._request_json.call_args
        assert args[0] == "DELETE"
        assert args[1] == api.RECORDINGS_URL


class TestCreateRecordingBody:
    def test_body_has_only_program_id(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(client.create_recording("prog-1", "ard"))
        kwargs = _call_kwargs(client._request_json)
        assert kwargs["body"] == {"programId": "prog-1"}


class TestStopRecordingRequest:
    def test_no_body_posts_to_stop_url(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(client.stop_recording("rec-1"))
        args, kwargs = client._request_json.call_args
        assert args[0] == "POST"
        assert args[1] == "https://recording.waipu.tv/api/recordings/rec-1/stop"
        assert "body" not in kwargs or kwargs["body"] is None


class TestCreateSerialRecordingBody:
    def test_body_shape(self):
        client = _client()
        client._request_json = AsyncMock(return_value={"id": "serial-1"})
        asyncio.run(client.create_serial_recording("ard", "Tatort", "104121"))
        kwargs = _call_kwargs(client._request_json)
        assert kwargs["body"] == {"channel": "ARD", "title": "Tatort", "seriesId": "104121"}
        assert kwargs["content_type"] == api.CONTENT_CREATE_SERIAL
        assert kwargs["accept"] == api.ACCEPT_SERIAL


class TestDeleteSerialRecordingBody:
    def test_body_shape_defaults(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(client.delete_serial_recording("serial-1"))
        kwargs = _call_kwargs(client._request_json)
        assert kwargs["body"] == {
            "serialRecordings": [
                {
                    "id": "serial-1",
                    "deleteFutureRecordings": True,
                    "deleteFinishedRecordings": False,
                    "deleteRunningRecordings": False,
                }
            ]
        }

    def test_body_shape_with_toggles(self):
        client = _client()
        client._request_json = AsyncMock(return_value=None)
        asyncio.run(
            client.delete_serial_recording(
                "serial-1", delete_finished_recordings=True, delete_running_recordings=True
            )
        )
        kwargs = _call_kwargs(client._request_json)
        rule = kwargs["body"]["serialRecordings"][0]
        assert rule["deleteFinishedRecordings"] is True
        assert rule["deleteRunningRecordings"] is True
        assert rule["deleteFutureRecordings"] is True  # always true, no toggle for it
