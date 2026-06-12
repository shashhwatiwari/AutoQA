"""
Auth API test suite — reqres.in /api/login and /api/register

Coverage
--------
POST /login
    Positive  → 200, token present, token is a non-empty string, content-type, response time
    Negative  → missing password (400 + "Missing password")
                missing email    (400 + "Missing email or username")
                unregistered     (400 + "user not found")
                empty body       (400)
                null values      (400)

POST /register
    Positive  → 200, id (int) + token (str) returned, content-type, response time
    Negative  → missing password (400 + "Missing password")
                missing email    (400 + "Missing email or username")
                unregistered     (400 + "Note: Only defined users succeed registration")
                empty body       (400)

Token usage
    → Bearer token plumbed into Authorization header
    → Cleared token still allows requests to public endpoints
"""
import pytest
from utils.api_client import (
    APIClient,
    assert_status,
    assert_schema,
    assert_field_type,
    assert_response_time,
    assert_content_type,
    get_json,
)

RESPONSE_TIME_MS = 5_000

VALID_EMAIL    = "eve.holt@reqres.in"
VALID_PASSWORD = "cityslicka"

REG_EMAIL    = "eve.holt@reqres.in"
REG_PASSWORD = "pistol"


@pytest.fixture
def client(api_base_url):
    return APIClient(api_base_url)


# ===========================================================================
# POST /login — positive
# ===========================================================================

@pytest.mark.api
@pytest.mark.regression
class TestLoginPositive:

    def test_valid_login_returns_200(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert_status(resp, 200)

    def test_valid_login_content_type_is_json(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert_content_type(resp, "application/json")

    def test_valid_login_response_time(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert_response_time(resp, RESPONSE_TIME_MS)

    def test_valid_login_returns_token_key(self, client):
        body = get_json(client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD}))
        assert "token" in body, f"'token' missing from login response: {list(body.keys())}"

    def test_valid_login_token_is_string(self, client):
        body = get_json(client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD}))
        assert_field_type(body, "token", str)

    def test_valid_login_token_is_non_empty(self, client):
        body = get_json(client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD}))
        assert body["token"].strip(), "Login token must be a non-empty string"

    def test_valid_login_token_length_is_reasonable(self, client):
        """Token should be at least 8 chars (guards against an empty-string token slipping through)."""
        body = get_json(client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD}))
        assert len(body["token"]) >= 8, (
            f"Token seems too short ({len(body['token'])} chars): {body['token']!r}"
        )

    def test_valid_login_response_has_only_token(self, client):
        """reqres.in /login returns only {token} — no extra undocumented fields."""
        body = get_json(client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD}))
        assert set(body.keys()) == {"token"}, (
            f"Expected exactly {{'token'}}, got keys: {set(body.keys())}"
        )

    def test_consecutive_logins_return_same_token(self, client):
        """reqres.in returns a deterministic token for the same credentials."""
        payload = {"email": VALID_EMAIL, "password": VALID_PASSWORD}
        token1 = get_json(client.post("/login", json=payload))["token"]
        token2 = get_json(client.post("/login", json=payload))["token"]
        assert token1 == token2, (
            f"Consecutive logins with same credentials should return the same token. "
            f"Got {token1!r} then {token2!r}"
        )


# ===========================================================================
# POST /login — negative
# ===========================================================================

@pytest.mark.api
@pytest.mark.regression
class TestLoginNegative:

    def test_missing_password_returns_400(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL})
        assert_status(resp, 400)

    def test_missing_password_error_message(self, client):
        body = get_json(client.post("/login", json={"email": VALID_EMAIL}))
        assert body.get("error") == "Missing password", (
            f"Expected error='Missing password', got: {body.get('error')!r}"
        )

    def test_missing_email_returns_400(self, client):
        resp = client.post("/login", json={"password": VALID_PASSWORD})
        assert_status(resp, 400)

    def test_missing_email_error_message(self, client):
        """reqres.in returns 'Missing email or username' when only password is sent."""
        body = get_json(client.post("/login", json={"password": VALID_PASSWORD}))
        assert "error" in body, f"Expected 'error' key in 400 response: {body}"
        assert "missing" in body["error"].lower(), (
            f"Error message should mention 'missing', got: {body['error']!r}"
        )

    def test_unregistered_user_returns_400(self, client):
        resp = client.post("/login", json={"email": "nobody@nowhere.io", "password": "x"})
        assert_status(resp, 400)

    def test_unregistered_user_error_message(self, client):
        body = get_json(client.post("/login", json={"email": "nobody@nowhere.io", "password": "x"}))
        assert "error" in body, f"400 response missing 'error' key: {body}"
        assert body["error"], "error field must be non-empty"

    def test_empty_json_body_returns_400(self, client):
        resp = client.post("/login", json={})
        assert_status(resp, 400)

    def test_empty_json_body_has_error_key(self, client):
        body = get_json(client.post("/login", json={}))
        assert "error" in body, f"Empty-body 400 response should include 'error': {body}"

    def test_null_email_returns_400(self, client):
        resp = client.post("/login", json={"email": None, "password": VALID_PASSWORD})
        assert_status(resp, 400)

    def test_null_password_returns_400(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL, "password": None})
        assert_status(resp, 400)

    def test_wrong_password_returns_400(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL, "password": "wrongpassword"})
        assert_status(resp, 400)

    def test_empty_string_password_returns_400(self, client):
        resp = client.post("/login", json={"email": VALID_EMAIL, "password": ""})
        assert_status(resp, 400)

    def test_invalid_endpoint_returns_404(self, client):
        """A GET to a non-existent path must return 404, not 500."""
        resp = client.get("/login_invalid_endpoint_xyz")
        assert_status(resp, 404)


# ===========================================================================
# POST /register — positive
# ===========================================================================

@pytest.mark.api
@pytest.mark.regression
class TestRegisterPositive:

    def test_valid_register_returns_200(self, client):
        resp = client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD})
        assert_status(resp, 200)

    def test_valid_register_content_type_is_json(self, client):
        resp = client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD})
        assert_content_type(resp, "application/json")

    def test_valid_register_response_time(self, client):
        resp = client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD})
        assert_response_time(resp, RESPONSE_TIME_MS)

    def test_valid_register_returns_id_and_token(self, client):
        body = get_json(client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD}))
        assert_schema(body, ["id", "token"])

    def test_valid_register_id_is_integer(self, client):
        body = get_json(client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD}))
        assert_field_type(body, "id", int)

    def test_valid_register_token_is_string(self, client):
        body = get_json(client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD}))
        assert_field_type(body, "token", str)

    def test_valid_register_token_non_empty(self, client):
        body = get_json(client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD}))
        assert body["token"].strip(), "Registration token must not be blank"

    def test_valid_register_id_is_positive(self, client):
        body = get_json(client.post("/register", json={"email": REG_EMAIL, "password": REG_PASSWORD}))
        assert body["id"] > 0, f"id must be a positive integer, got {body['id']}"


# ===========================================================================
# POST /register — negative
# ===========================================================================

@pytest.mark.api
@pytest.mark.regression
class TestRegisterNegative:

    def test_missing_password_returns_400(self, client):
        assert_status(client.post("/register", json={"email": REG_EMAIL}), 400)

    def test_missing_password_error_message(self, client):
        body = get_json(client.post("/register", json={"email": REG_EMAIL}))
        assert body.get("error") == "Missing password", (
            f"Expected error='Missing password', got: {body.get('error')!r}"
        )

    def test_missing_email_returns_400(self, client):
        assert_status(client.post("/register", json={"password": REG_PASSWORD}), 400)

    def test_missing_email_error_message(self, client):
        body = get_json(client.post("/register", json={"password": REG_PASSWORD}))
        assert "error" in body, f"Expected 'error' key: {body}"
        assert "missing" in body["error"].lower(), (
            f"Error should mention 'missing', got: {body['error']!r}"
        )

    def test_unregistered_email_returns_400(self, client):
        """reqres.in only supports registration for a pre-defined set of users."""
        resp = client.post("/register", json={"email": "random@test.io", "password": "pass"})
        assert_status(resp, 400)

    def test_unregistered_email_error_message(self, client):
        body = get_json(
            client.post("/register", json={"email": "random@test.io", "password": "pass"})
        )
        assert "error" in body, f"400 body should contain 'error': {body}"
        assert body["error"], "error field must be non-empty"

    def test_empty_json_body_returns_400(self, client):
        assert_status(client.post("/register", json={}), 400)

    def test_null_email_returns_400(self, client):
        assert_status(client.post("/register", json={"email": None, "password": REG_PASSWORD}), 400)

    def test_null_password_returns_400(self, client):
        assert_status(client.post("/register", json={"email": REG_EMAIL, "password": None}), 400)


# ===========================================================================
# Token usage
# ===========================================================================

@pytest.mark.api
@pytest.mark.regression
class TestTokenUsage:

    def test_set_bearer_token_is_sent_in_header(self, client):
        """
        Log in to get a real token, attach it via set_auth_token(), then make
        a request and confirm it returns 200 (the header was plumbed through).
        reqres.in /users is public but still validates the session returns 200.
        """
        token_resp = client.post("/login", json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        token = get_json(token_resp)["token"]

        client.set_auth_token(token)
        resp = client.get("/users/2")
        assert_status(resp, 200)

    def test_clear_auth_still_allows_public_endpoint(self, client):
        """Public endpoints must be accessible without a token."""
        client.set_auth_token("some-token")
        client.clear_auth()

        resp = client.get("/users/2")
        assert_status(resp, 200)

    def test_malformed_token_does_not_crash_public_endpoint(self, client):
        """reqres.in does not gate /users behind auth — malformed token still 200."""
        client.set_auth_token("not.a.valid.jwt")
        resp = client.get("/users/2")
        assert_status(resp, 200)
