from unittest import mock

import pytest
import requests

from setup_runs.wrf.fetch_fnl import download_file

URL = "https://example.com/gdas1.fnl0p25.2022110100.f00.grib2"


def mock_session(chunks: list[bytes], headers: dict) -> mock.Mock:
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.headers = headers
    response.iter_content.return_value = iter(chunks)

    session = mock.Mock()
    session.get.return_value = response
    return session


def test_download_file(tmp_path):
    session = mock_session([b"GRIB", b"7777"], {"Content-Length": "8"})

    result = download_file(session, tmp_path, URL)

    assert result == tmp_path / "gdas1.fnl0p25.2022110100.f00.grib2"
    assert result.read_bytes() == b"GRIB7777"

    # files has been stored in the expected location
    assert list(tmp_path.iterdir()) == [result]


def test_download_file_incomplete(tmp_path):
    session = mock_session([b"GRIB"], {"Content-Length": "8"})

    with pytest.raises(RuntimeError, match="Incomplete download"):
        download_file(session, tmp_path, URL)

    # no files have appeared in the target path
    assert list(tmp_path.iterdir()) == []


def test_download_file_interrupted(tmp_path):
    def interrupted():
        yield b"GRIB"
        raise requests.exceptions.ChunkedEncodingError("connection reset")

    session = mock_session([], {"Content-Length": "8"})
    session.get.return_value.iter_content.return_value = interrupted()

    with pytest.raises(RuntimeError, match="Error downloading"):
        download_file(session, tmp_path, URL)

    # no files have appeared in the target path
    assert list(tmp_path.iterdir()) == []


def test_download_file_killed(tmp_path):
    # non-RequestException errors, like a KeyboardInterrupt or a joblib
    # worker being terminated, must also not leave a partial file behind
    def killed():
        yield b"GRIB"
        raise KeyboardInterrupt()

    session = mock_session([], {"Content-Length": "8"})
    session.get.return_value.iter_content.return_value = killed()

    with pytest.raises(KeyboardInterrupt):
        download_file(session, tmp_path, URL)

    # no files have appeared in the target path
    assert list(tmp_path.iterdir()) == []
