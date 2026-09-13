from __future__ import annotations

from datetime import datetime, timezone

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.cache import SimpleCache
from app.errors import UpstreamError
from app.youversion_client import YouVersionClient
from tests.conftest import FakeResponse, FakeSession, FakeYouVersionClient


def test_happy_path(client: FlaskClient) -> None:
    response = client.get("/votd?day=195&version=206")

    assert response.status_code == 200
    assert response.get_json() == {
        "day": 195,
        "reference": "Revelation 3:20",
        "text": (
            "Behold, I stand at the door and knock: if any man hear my voice "
            "and open the door, I will come in to him, and will sup with him, "
            "and he with me."
        ),
        "version_id": 206,
    }


@pytest.mark.parametrize("bad_day", ["0", "367", "abc", "-5"])
def test_invalid_day_returns_400(client: FlaskClient, bad_day: str) -> None:
    response = client.get(f"/votd?day={bad_day}&version=206")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_DAY"


def test_missing_day_defaults_to_todays_utc_day_of_year(
    client: FlaskClient, fake_client: FakeYouVersionClient
) -> None:
    today = datetime.now(timezone.utc).timetuple().tm_yday
    fake_client.passage_ids[today] = "REV.3.20"

    response = client.get("/votd?version=206")

    assert response.status_code == 200
    assert response.get_json()["day"] == today


def test_upstream_failure_on_votd_lookup_returns_502(app: Flask, fake_client: FakeYouVersionClient) -> None:
    fake_client.votd_error = UpstreamError("could not reach YouVersion")
    test_client = app.test_client()

    response = test_client.get("/votd?day=195&version=206")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "UPSTREAM_ERROR"


def test_upstream_failure_on_passage_lookup_returns_502(app: Flask, fake_client: FakeYouVersionClient) -> None:
    fake_client.passage_error = UpstreamError("could not reach YouVersion")
    test_client = app.test_client()

    response = test_client.get("/votd?day=195&version=206")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "UPSTREAM_ERROR"


def test_repeat_request_does_not_call_youversion_twice(config) -> None:
    """Integration-style check of requirement 4, through the real client + cache."""
    session = FakeSession()
    responses = iter(
        [
            FakeResponse(200, {"day": 195, "passage_id": "REV.3.20"}),
            FakeResponse(200, {"id": "REV.3.20", "reference": "Revelation 3:20", "content": "Behold..."}),
        ]
    )

    def fake_get(url, params=None, headers=None, timeout=None):
        session.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return next(responses)

    session.get = fake_get  # type: ignore[method-assign]

    real_client = YouVersionClient(config, SimpleCache(), session=session)
    app = create_app(client=real_client)
    test_client = app.test_client()

    first = test_client.get("/votd?day=195&version=206")
    second = test_client.get("/votd?day=195&version=206")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json() == second.get_json()
    assert len(session.calls) == 2  # one calendar call + one passage call, never repeated
