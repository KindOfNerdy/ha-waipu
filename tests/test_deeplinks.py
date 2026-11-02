"""waipu deep-link builders (const.py) — the exact link shapes verified live
on an Android TV on 2026-11-02; a wrong parameter name (e.g. `id` instead
of `recordingId`) silently degrades to "open the recordings overview"."""
import pytest

from .helpers import const


def test_station_link():
    assert const.waipu_station_link("swr_bw") == "waipu://tv?id=swr_bw"


def test_station_link_escapes():
    assert const.waipu_station_link("a&b") == "waipu://tv?id=a%26b"


def test_recording_link_resume_is_default():
    assert (
        const.waipu_recording_link("2115976245")
        == "waipu://recordings?recordingId=2115976245&autoplay=true"
    )


def test_recording_link_beginning_forces_position_zero():
    assert (
        const.waipu_recording_link("1", const.RECORDING_START_BEGINNING)
        == "waipu://recordings?recordingId=1&autoplay=true&position=0"
    )


def test_recording_link_details_has_no_autoplay():
    assert (
        const.waipu_recording_link("1", const.RECORDING_START_DETAILS)
        == "waipu://recordings?recordingId=1"
    )


def test_recording_link_position_wins_over_mode():
    assert (
        const.waipu_recording_link("1", const.RECORDING_START_DETAILS, 600)
        == "waipu://recordings?recordingId=1&autoplay=true&position=600"
    )


def test_recording_link_unknown_mode():
    with pytest.raises(ValueError):
        const.waipu_recording_link("1", "bogus")


def test_program_link_details():
    assert (
        const.waipu_program_link("zdf", "ad83-75c7")
        == "waipu://epgdetails?channelId=zdf&programId=ad83-75c7"
    )


def test_program_link_autoplay():
    assert (
        const.waipu_program_link("zdf", "ad83-75c7", autoplay=True)
        == "waipu://epgdetails?channelId=zdf&programId=ad83-75c7&autoplay=true"
    )
