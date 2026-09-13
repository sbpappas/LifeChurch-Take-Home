# this class talks to YouVersion api and caches the two calls VOTD needs

# 1. this does not log request headers or full request/response objects here
# 2. The app key lives in a header, and according to some research, even accidental logging  of that object would leak it
# 3. Only sanitized, key-free details (method, path, status code) are ever logged

import logging 

import requests # third party lib that makes http requests

from app.errors import UpstreamError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 3 #gotta be quick

class YouVersionClient:
    def __init__(self, config, cache, session=None, timeout=DEFAULT_TIMEOUT_SECONDS):
        self._config = config
        self._cache = cache
        self._session = session or requests.Session() #session obj reueses tcp conn across many requests (efficient)
        self._timeout = timeout

    def get_verse_of_the_day(self, day):
        # return the passage_id for the given day of the year and cache it
        return self._cache.get_or_set(
            ("votd", day),
            lambda: self._fetch_verse_of_the_day(day),
        )

    def get_passage_text(self, version_id, passage_id):
        # return {"reference": ..., "text": ...} for a passage in a version (cached)
        return self._cache.get_or_set(
            ("passage", version_id, passage_id),
            lambda: self._fetch_passage_text(version_id, passage_id),
        )

    def _fetch_verse_of_the_day(self, day):
        # return passage_id for given day of the year (1-366), actually calls upstream api
        data = self._get(f"/v1/verse_of_the_days/{day}")
        try:
            return data["passage_id"]
        except (TypeError, KeyError):
            raise UpstreamError("YouVersion response was missing passage_id")

    def _fetch_passage_text(self, version_id, passage_id):
        #return text in the right format for given passage and ver
        data = self._get(
            f"/v1/bibles/{version_id}/passages/{passage_id}",
            params={"format": "text"},
        )
        try:
            return {"reference": data["reference"], "text": data["content"]}
        except (TypeError, KeyError):
            raise UpstreamError("YouVersion response was missing reference/content")

    def _get(self, path, params=None): # return json from youversion api, makes the https request
        url = f"{self._config.base_url}{path}"
        try:
            response = self._session.get(
                url,
                params=params,
                headers={"x-yvp-app-key": self._config.app_key},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            logger.warning("YouVersion request failed: %s %s (%s)", "GET", path, type(exc).__name__)
            raise UpstreamError("could not reach YouVersion") from exc

        if not response.ok:
            logger.warning(
                "YouVersion returned an error: %s %s -> %s", "GET", path, response.status_code
            )
            raise UpstreamError(f"YouVersion returned status {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:
            logger.warning("YouVersion returned a non-JSON response: %s %s", "GET", path)
            raise UpstreamError("YouVersion returned an unexpected response") from exc

    #extra
    def get_versions(self):
        return self._cache.get_or_set(
            ("versions",),
            lambda: self._fetch_versions(),
        )

    def _fetch_versions(self):
            # return versions for given language (cached)
            data = self._get("/v1/bibles", params={"language_ranges[]": "en*"})  
            # because the instructions say this api call is `GET /v1/bibles?language_ranges[]=en*`          
            try:
                return data["data"]
            except (TypeError, KeyError):
                raise UpstreamError("YouVersion response was missing data (type was not dict or dict did not have 'data' key)")
    