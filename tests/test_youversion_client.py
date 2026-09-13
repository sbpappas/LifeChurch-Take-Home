from __future__ import annotations

import logging

import pytest
import requests

from app.cache import SimpleCache
from app.config import Config
from app.errors import UpstreamError
from app.youversion_client import YouVersionClient
from tests.conftest import FakeResponse, FakeSession, TEST_APP_KEY

def test_sends_app_key_header_and_parses_passage_id(config: Config) -> None:
    session = FakeSession(response=FakeResponse(200, {"day": 195, "passage_id": "REV.3.20"}))
    client = YouVersionClient(config, SimpleCache(), session=session)

    passage_id = client.get_verse_of_the_day(195)

    assert passage_id == "REV.3.20"
    assert session.calls[0]["headers"] == {"x-yvp-app-key": TEST_APP_KEY}


def test_get_passage_text_parses_reference_and_content(config: Config) -> None:
    session = FakeSession(
        response=FakeResponse(200, {"id": "REV.3.20", "reference": "Revelation 3:20", "content": "Behold..."})
    )
    client = YouVersionClient(config, SimpleCache(), session=session)

    passage = client.get_passage_text(206, "REV.3.20")

    assert passage == {"reference": "Revelation 3:20", "text": "Behold..."}


def test_repeat_lookup_hits_cache_not_the_network(config: Config) -> None:
    session = FakeSession(response=FakeResponse(200, {"day": 195, "passage_id": "REV.3.20"}))
    client = YouVersionClient(config, SimpleCache(), session=session)

    client.get_verse_of_the_day(195)
    client.get_verse_of_the_day(195)

    assert len(session.calls) == 1 # this is a neat function that I learned about (thanks flask)


def test_connection_failure_raises_upstream_error(config: Config) -> None:
    session = FakeSession(exc=requests.ConnectionError("boom"))
    client = YouVersionClient(config, SimpleCache(), session=session)

    with pytest.raises(UpstreamError) as exc_info:
        client.get_verse_of_the_day(195)

    assert TEST_APP_KEY not in str(exc_info.value)


def test_timeout_raises_upstream_error(config: Config) -> None:
    session = FakeSession(exc=requests.Timeout("too slow"))
    client = YouVersionClient(config, SimpleCache(), session=session)

    with pytest.raises(UpstreamError):
        client.get_verse_of_the_day(195)


def test_upstream_5xx_raises_upstream_error(config: Config) -> None:
    session = FakeSession(response=FakeResponse(500))
    client = YouVersionClient(config, SimpleCache(), session=session)

    with pytest.raises(UpstreamError):
        client.get_verse_of_the_day(195)


def test_upstream_403_raises_upstream_error(config: Config) -> None:
    # e.g. a licensed version like NIV -- collapsed to the same 502/UPSTREAM_ERROR
    # as any other non-2xx, per the documented Decisions & Assumptions.
    session = FakeSession(response=FakeResponse(403))
    client = YouVersionClient(config, SimpleCache(), session=session)

    with pytest.raises(UpstreamError):
        client.get_verse_of_the_day(195)


def test_app_key_never_appears_in_logs(config: Config, caplog: pytest.LogCaptureFixture) -> None:
    session = FakeSession(exc=requests.ConnectionError("boom"))
    client = YouVersionClient(config, SimpleCache(), session=session)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UpstreamError):
            client.get_verse_of_the_day(195)

    assert TEST_APP_KEY not in caplog.text
