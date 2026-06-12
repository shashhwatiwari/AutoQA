"""
Thin requests wrapper and assertion helpers for API tests.

Design contract
---------------
APIClient     — one instance per test (or session); wraps requests.Session
                so headers, auth tokens, and timeouts are set once.

assert_*      — standalone functions that raise AssertionError with a
                message that includes the actual value so failures are
                self-explanatory without re-running with -v.
"""
from __future__ import annotations

import os
import re
import requests


# ===========================================================================
# Client
# ===========================================================================

class APIClient:
    DEFAULT_TIMEOUT = 10  # seconds

    def __init__(self, base_url: str, default_headers: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["Content-Type"] = "application/json"
        # reqres.in requires x-api-key for all /api/* endpoints.
        # Key is read from REQRES_API_KEY env var (set locally via .env or
        # passed as a GitHub Actions secret).
        api_key = os.environ.get("REQRES_API_KEY", "")
        if api_key:
            self.session.headers["x-api-key"] = api_key
        if default_headers:
            self.session.headers.update(default_headers)

    # ------------------------------------------------------------------
    # HTTP verbs
    # ------------------------------------------------------------------

    def get(self, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return self.session.get(self._url(path), **kwargs)

    def head(self, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return self.session.head(self._url(path), **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return self.session.post(self._url(path), **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return self.session.put(self._url(path), **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return self.session.patch(self._url(path), **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        return self.session.delete(self._url(path), **kwargs)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def set_auth_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_auth(self):
        self.session.headers.pop("Authorization", None)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"


# ===========================================================================
# Assertion helpers
# ===========================================================================

def get_json(response: requests.Response) -> dict | list:
    """Parse JSON, raising AssertionError with the raw body on failure."""
    if response.status_code == 429:
        import pytest
        try:
            resets = response.json().get("current_usage", {}).get("resets_at", "midnight UTC")
        except Exception:
            resets = "midnight UTC"
        pytest.skip(
            f"reqres.in free-tier rate limit exceeded (250 req/day). "
            f"Resets at {resets}. Re-run tomorrow or upgrade the API key."
        )
    try:
        return response.json()
    except Exception as exc:
        raise AssertionError(
            f"Response body is not valid JSON. Status {response.status_code}. "
            f"Body: {response.text[:500]!r}"
        ) from exc


def assert_status(response: requests.Response, expected: int) -> None:
    if response.status_code == 429 and expected != 429:
        import pytest
        resets = response.json().get("current_usage", {}).get("resets_at", "midnight UTC")
        pytest.skip(
            f"reqres.in free-tier rate limit exceeded (250 req/day). "
            f"Resets at {resets}. Re-run tomorrow or upgrade the API key."
        )
    assert response.status_code == expected, (
        f"Expected HTTP {expected}, got {response.status_code}. "
        f"Body: {response.text[:500]}"
    )


def assert_schema(data: dict, required_keys: list[str]) -> None:
    """All required_keys must be present at the top level of data."""
    missing = [k for k in required_keys if k not in data]
    assert not missing, f"Missing keys in response: {missing}. Got keys: {list(data.keys())}"


def assert_field_type(data: dict, field: str, expected_type: type) -> None:
    """data[field] must be an instance of expected_type."""
    assert field in data, f"Field '{field}' not present in response: {list(data.keys())}"
    actual = data[field]
    assert isinstance(actual, expected_type), (
        f"Field '{field}' expected type {expected_type.__name__}, "
        f"got {type(actual).__name__} with value {actual!r}"
    )


def assert_json_value(response: requests.Response, key_path: str, expected) -> None:
    """
    Navigate a dot-separated key_path into the response JSON and assert
    the leaf value equals `expected`.
    Example: assert_json_value(resp, "data.email", "janet.weaver@reqres.in")
    """
    data = get_json(response)
    current = data
    for key in key_path.split("."):
        assert isinstance(current, dict) and key in current, (
            f"Key '{key}' not found while traversing '{key_path}'. "
            f"Current node: {current!r}"
        )
        current = current[key]
    assert current == expected, (
        f"Expected {key_path}={expected!r}, got {current!r}"
    )


def assert_response_time(response: requests.Response, max_ms: int) -> None:
    """The round-trip time must be within max_ms milliseconds."""
    elapsed_ms = response.elapsed.total_seconds() * 1000
    assert elapsed_ms <= max_ms, (
        f"Response took {elapsed_ms:.0f} ms, which exceeds the {max_ms} ms limit"
    )


def assert_content_type(response: requests.Response, expected_mime: str = "application/json") -> None:
    """Content-Type header must contain expected_mime (case-insensitive)."""
    actual = response.headers.get("Content-Type", "")
    assert expected_mime.lower() in actual.lower(), (
        f"Expected Content-Type containing '{expected_mime}', got '{actual}'"
    )


def assert_email_format(value: str) -> None:
    """Value must look like a valid e-mail address."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    assert re.match(pattern, value), (
        f"Value does not look like an e-mail address: {value!r}"
    )


def assert_url_format(value: str) -> None:
    """Value must start with http:// or https://."""
    assert value.startswith(("http://", "https://")), (
        f"Value does not look like a URL: {value!r}"
    )


def assert_body_is_empty(response: requests.Response) -> None:
    """Response body must be empty (e.g. 204 No Content)."""
    if response.status_code == 429:
        import pytest
        try:
            resets = response.json().get("current_usage", {}).get("resets_at", "midnight UTC")
        except Exception:
            resets = "midnight UTC"
        pytest.skip(
            f"reqres.in free-tier rate limit exceeded (250 req/day). "
            f"Resets at {resets}. Re-run tomorrow or upgrade the API key."
        )
    assert response.text.strip() == "", (
        f"Expected an empty response body, got: {response.text[:200]!r}"
    )


def assert_echoed_fields(response: requests.Response, payload: dict) -> None:
    """Every key-value pair in payload must appear in the response JSON."""
    body = get_json(response)
    for key, expected_val in payload.items():
        assert key in body, f"Echoed field '{key}' missing from response: {list(body.keys())}"
        assert body[key] == expected_val, (
            f"Echoed field '{key}': expected {expected_val!r}, got {body[key]!r}"
        )
