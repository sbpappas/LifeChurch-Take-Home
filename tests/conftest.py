from __future__ import annotations

from typing import Any, Optional

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.config import Config

TEST_APP_KEY = "test-app-key-should-never-leak"

class FakeYouVersionClient:
    # test double for youversionclient for using flask routes without going to real youversion APIs

    def __init__(
        self,
        passage_ids: Optional[dict[int, str]] = None,
        passages: Optional[dict[tuple[int, str], dict[str, str]]] = None,
        votd_error: Optional[Exception] = None,
        passage_error: Optional[Exception] = None,
    ) -> None:
        self.passage_ids = passage_ids or {}
        self.passages = passages or {}
        self.votd_error = votd_error
        self.passage_error = passage_error
        self.votd_calls: list[int] = []
        self.passage_calls: list[tuple[int, str]] = []

    def get_verse_of_the_day(self, day: int) -> str:
        self.votd_calls.append(day)
        if self.votd_error:
            raise self.votd_error
        return self.passage_ids[day]

    def get_passage_text(self, version_id: int, passage_id: str) -> dict[str, str]:
        self.passage_calls.append((version_id, passage_id))
        if self.passage_error:
            raise self.passage_error
        return self.passages[(version_id, passage_id)]


class FakeResponse:
    # stand-in for requests.Response, for exercising YouVersionClient directly

    def __init__(self, status_code: int, json_data: Any = None) -> None:
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._json_data = json_data

    def json(self) -> Any:
        return self._json_data

class FakeSession:
    # stand-in for requests.Session

    def __init__(self, response: Optional[FakeResponse] = None, exc: Optional[Exception] = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        if self.exc:
            raise self.exc
        assert self.response is not None
        return self.response


@pytest.fixture
def fake_client() -> FakeYouVersionClient:
    return FakeYouVersionClient(
        passage_ids={195: "REV.3.20"},
        passages={
            (206, "REV.3.20"): {
                "reference": "Revelation 3:20",
                "text": (
                    "Behold, I stand at the door and knock: if any man hear my voice "
                    "and open the door, I will come in to him, and will sup with him, "
                    "and he with me."
                ),
            }
        },
    )


@pytest.fixture
def app(fake_client: FakeYouVersionClient) -> Flask:
    return create_app(client=fake_client)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def config() -> Config:
    return Config(app_key=TEST_APP_KEY, base_url="https://fake.example.com")
