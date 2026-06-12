"""
Users API test suite — reqres.in /api/users

Coverage
--------
GET    /users          list, pagination metadata types, per_page param, disjoint pages
GET    /users/{id}     schema, field types, email format, avatar URL, support block
GET    /users/9999     → 404 with empty body
GET    /users?delay=1  → 200, response time within generous threshold
POST   /users          → 201, echoed fields, id & createdAt present and typed
PUT    /users/{id}     → 200, all sent fields echoed back, updatedAt present
PATCH  /users/{id}     → 200, only changed field echoed, updatedAt present
DELETE /users/{id}     → 204, body is empty
Negative cases         → non-integer ID, page=0, unknown query params
"""
import re
import pytest
from utils.api_client import (
    APIClient,
    assert_status,
    assert_schema,
    assert_field_type,
    assert_json_value,
    assert_response_time,
    assert_content_type,
    assert_email_format,
    assert_url_format,
    assert_body_is_empty,
    assert_echoed_fields,
    get_json,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIST_SCHEMA     = ["page", "per_page", "total", "total_pages", "data"]
USER_SCHEMA     = ["id", "email", "first_name", "last_name", "avatar"]
RESPONSE_TIME_MS = 5_000  # reqres.in is a public sandbox — generous threshold


@pytest.fixture
def client(api_base_url):
    return APIClient(api_base_url)


# ===========================================================================
# GET /users — list endpoint
# ===========================================================================

@pytest.mark.api
class TestGetUsersList:

    def test_list_users_returns_200(self, client):
        resp = client.get("/users")
        assert_status(resp, 200)

    def test_list_users_content_type_is_json(self, client):
        resp = client.get("/users")
        assert_content_type(resp, "application/json")

    def test_list_users_response_time(self, client):
        resp = client.get("/users")
        assert_response_time(resp, RESPONSE_TIME_MS)

    def test_list_users_top_level_schema(self, client):
        resp = client.get("/users")
        assert_schema(get_json(resp), LIST_SCHEMA)

    def test_list_users_metadata_types(self, client):
        """page, per_page, total, total_pages must be integers; data must be a list."""
        body = get_json(client.get("/users"))
        for field in ("page", "per_page", "total", "total_pages"):
            assert_field_type(body, field, int)
        assert isinstance(body["data"], list), (
            f"'data' must be a list, got {type(body['data']).__name__}"
        )

    def test_list_users_page_number_matches_request(self, client):
        body = get_json(client.get("/users?page=2"))
        assert body["page"] == 2

    def test_list_users_data_not_empty(self, client):
        body = get_json(client.get("/users"))
        assert len(body["data"]) > 0, "data array must not be empty"

    def test_list_users_data_items_have_user_schema(self, client):
        body = get_json(client.get("/users"))
        for user in body["data"]:
            assert_schema(user, USER_SCHEMA)

    def test_list_users_page1_and_page2_are_disjoint(self, client):
        """No user ID should appear on both pages."""
        ids_p1 = {u["id"] for u in get_json(client.get("/users?page=1"))["data"]}
        ids_p2 = {u["id"] for u in get_json(client.get("/users?page=2"))["data"]}
        assert ids_p1.isdisjoint(ids_p2), (
            f"Pages share user IDs: {ids_p1 & ids_p2}"
        )

    def test_list_users_total_pages_consistent_with_total(self, client):
        """total_pages must equal ceil(total / per_page)."""
        import math
        body = get_json(client.get("/users"))
        expected_pages = math.ceil(body["total"] / body["per_page"])
        assert body["total_pages"] == expected_pages, (
            f"total_pages={body['total_pages']} but ceil({body['total']}/{body['per_page']})={expected_pages}"
        )

    def test_list_users_per_page_param_respected(self, client):
        """?per_page=3 should return exactly 3 users in data."""
        body = get_json(client.get("/users?per_page=3"))
        assert len(body["data"]) == 3, (
            f"Expected 3 users with per_page=3, got {len(body['data'])}"
        )

    def test_list_users_per_page_reflects_in_metadata(self, client):
        body = get_json(client.get("/users?per_page=3"))
        assert body["per_page"] == 3

    def test_list_users_user_ids_are_positive_integers(self, client):
        body = get_json(client.get("/users"))
        for user in body["data"]:
            assert isinstance(user["id"], int) and user["id"] > 0, (
                f"User id must be a positive integer, got {user['id']!r}"
            )

    def test_list_users_emails_are_valid_format(self, client):
        body = get_json(client.get("/users"))
        for user in body["data"]:
            assert_email_format(user["email"])

    def test_list_users_avatars_are_urls(self, client):
        body = get_json(client.get("/users"))
        for user in body["data"]:
            assert_url_format(user["avatar"])

    def test_delayed_response_returns_200(self, client):
        """?delay=1 uses reqres.in's artificial delay endpoint — still returns 200."""
        resp = client.get("/users?delay=1", timeout=15)
        assert_status(resp, 200)
        assert_schema(get_json(resp), LIST_SCHEMA)


# ===========================================================================
# GET /users/{id} — single user
# ===========================================================================

@pytest.mark.api
class TestGetSingleUser:

    def test_get_user_2_returns_200(self, client):
        assert_status(client.get("/users/2"), 200)

    def test_get_user_2_content_type_is_json(self, client):
        assert_content_type(client.get("/users/2"), "application/json")

    def test_get_user_2_response_time(self, client):
        assert_response_time(client.get("/users/2"), RESPONSE_TIME_MS)

    def test_get_user_2_data_schema(self, client):
        body = get_json(client.get("/users/2"))
        assert_schema(body["data"], USER_SCHEMA)

    def test_get_user_2_field_types(self, client):
        user = get_json(client.get("/users/2"))["data"]
        assert_field_type(user, "id",         int)
        assert_field_type(user, "email",      str)
        assert_field_type(user, "first_name", str)
        assert_field_type(user, "last_name",  str)
        assert_field_type(user, "avatar",     str)

    def test_get_user_2_email_is_valid(self, client):
        user = get_json(client.get("/users/2"))["data"]
        assert_email_format(user["email"])

    def test_get_user_2_avatar_is_url(self, client):
        user = get_json(client.get("/users/2"))["data"]
        assert_url_format(user["avatar"])

    def test_get_user_2_names_are_non_empty(self, client):
        user = get_json(client.get("/users/2"))["data"]
        assert user["first_name"].strip(), "first_name must not be blank"
        assert user["last_name"].strip(),  "last_name must not be blank"

    def test_get_user_2_has_support_block(self, client):
        """reqres.in includes a top-level 'support' key on single-user responses."""
        body = get_json(client.get("/users/2"))
        assert "support" in body, (
            f"Response missing 'support' key. Got keys: {list(body.keys())}"
        )

    def test_get_user_2_support_has_url_and_text(self, client):
        support = get_json(client.get("/users/2"))["support"]
        assert "url" in support and "text" in support, (
            f"'support' block must have 'url' and 'text'. Got: {list(support.keys())}"
        )

    def test_get_user_specific_value(self, client):
        """id=2 should be Janet Weaver per reqres.in fixture data."""
        assert_json_value(client.get("/users/2"), "data.email", "janet.weaver@reqres.in")

    # ------------------------------------------------------------------
    # Negative — not found
    # ------------------------------------------------------------------

    def test_get_nonexistent_user_returns_404(self, client):
        assert_status(client.get("/users/9999"), 404)

    def test_get_nonexistent_user_body_is_empty_object(self, client):
        """reqres.in returns {} (empty JSON object) for unknown users."""
        body = get_json(client.get("/users/9999"))
        assert body == {} or body is None, (
            f"404 response body should be empty, got {body!r}"
        )

    def test_get_user_id_zero_returns_404(self, client):
        """ID 0 is not a valid user ID."""
        assert_status(client.get("/users/0"), 404)

    def test_get_user_non_integer_id_returns_404(self, client):
        """reqres.in treats alphabetic path segments as unknown resources."""
        assert_status(client.get("/users/abc"), 404)


# ===========================================================================
# POST /users — create
# ===========================================================================

@pytest.mark.api
class TestCreateUser:

    _PAYLOAD = {"name": "AutoQA Bot", "job": "QA Engineer"}

    def test_create_user_returns_201(self, client):
        resp = client.post("/users", json=self._PAYLOAD)
        assert_status(resp, 201)

    def test_create_user_content_type_is_json(self, client):
        resp = client.post("/users", json=self._PAYLOAD)
        assert_content_type(resp, "application/json")

    def test_create_user_echoes_sent_fields(self, client):
        """Response must include name and job with exactly the values sent."""
        resp = client.post("/users", json=self._PAYLOAD)
        assert_echoed_fields(resp, self._PAYLOAD)

    def test_create_user_response_has_id(self, client):
        body = get_json(client.post("/users", json=self._PAYLOAD))
        assert "id" in body, f"'id' missing from create response: {body}"
        assert body["id"], "id must be a non-empty value"

    def test_create_user_response_has_created_at(self, client):
        body = get_json(client.post("/users", json=self._PAYLOAD))
        assert "createdAt" in body, f"'createdAt' missing from create response: {body}"

    def test_create_user_id_is_string(self, client):
        """reqres.in returns id as a string (not int) on POST /users."""
        body = get_json(client.post("/users", json=self._PAYLOAD))
        assert_field_type(body, "id", str)

    def test_create_user_created_at_is_string(self, client):
        body = get_json(client.post("/users", json=self._PAYLOAD))
        assert_field_type(body, "createdAt", str)

    def test_create_user_response_time(self, client):
        resp = client.post("/users", json=self._PAYLOAD)
        assert_response_time(resp, RESPONSE_TIME_MS)

    def test_create_user_different_calls_get_different_ids(self, client):
        id1 = get_json(client.post("/users", json=self._PAYLOAD))["id"]
        id2 = get_json(client.post("/users", json=self._PAYLOAD))["id"]
        assert id1 != id2, "Each POST /users should yield a unique id"

    def test_create_user_with_minimal_payload(self, client):
        """Sending only 'name' (no 'job') still yields 201."""
        resp = client.post("/users", json={"name": "Minimal User"})
        assert_status(resp, 201)
        body = get_json(resp)
        assert body.get("name") == "Minimal User"

    def test_create_user_name_is_echoed_exactly(self, client):
        resp = client.post("/users", json={"name": "Exact Name Test", "job": "QA"})
        assert get_json(resp)["name"] == "Exact Name Test"

    def test_create_user_job_is_echoed_exactly(self, client):
        resp = client.post("/users", json={"name": "AutoQA Bot", "job": "Senior QA Engineer"})
        assert get_json(resp)["job"] == "Senior QA Engineer"


# ===========================================================================
# PUT /users/{id} — full update
# ===========================================================================

@pytest.mark.api
class TestUpdateUserPut:

    _PAYLOAD = {"name": "Updated Bot", "job": "Senior QA"}

    def test_put_user_returns_200(self, client):
        assert_status(client.put("/users/2", json=self._PAYLOAD), 200)

    def test_put_user_content_type_is_json(self, client):
        assert_content_type(client.put("/users/2", json=self._PAYLOAD), "application/json")

    def test_put_user_echoes_all_sent_fields(self, client):
        resp = client.put("/users/2", json=self._PAYLOAD)
        assert_echoed_fields(resp, self._PAYLOAD)

    def test_put_user_has_updated_at(self, client):
        body = get_json(client.put("/users/2", json=self._PAYLOAD))
        assert "updatedAt" in body, f"'updatedAt' missing from PUT response: {body}"

    def test_put_user_updated_at_is_string(self, client):
        body = get_json(client.put("/users/2", json=self._PAYLOAD))
        assert_field_type(body, "updatedAt", str)

    def test_put_user_name_reflected_exactly(self, client):
        resp = client.put("/users/2", json={"name": "Precise Name", "job": "QA"})
        assert get_json(resp)["name"] == "Precise Name"

    def test_put_user_response_time(self, client):
        assert_response_time(client.put("/users/2", json=self._PAYLOAD), RESPONSE_TIME_MS)

    def test_put_different_user_ids_both_return_200(self, client):
        """reqres.in accepts PUT on any ID — confirms ID is not validated."""
        for user_id in (1, 2, 7):
            assert_status(client.put(f"/users/{user_id}", json=self._PAYLOAD), 200)


# ===========================================================================
# PATCH /users/{id} — partial update
# ===========================================================================

@pytest.mark.api
class TestUpdateUserPatch:

    def test_patch_user_returns_200(self, client):
        assert_status(client.patch("/users/2", json={"job": "Staff QA"}), 200)

    def test_patch_user_content_type_is_json(self, client):
        assert_content_type(client.patch("/users/2", json={"job": "Staff QA"}), "application/json")

    def test_patch_user_echoes_changed_field(self, client):
        resp = client.patch("/users/2", json={"job": "Principal QA"})
        assert get_json(resp).get("job") == "Principal QA", (
            f"PATCH should echo back the updated 'job' field. Body: {resp.text}"
        )

    def test_patch_user_has_updated_at(self, client):
        body = get_json(client.patch("/users/2", json={"job": "Staff QA"}))
        assert "updatedAt" in body, f"'updatedAt' missing from PATCH response: {body}"

    def test_patch_user_updated_at_is_string(self, client):
        body = get_json(client.patch("/users/2", json={"job": "Staff QA"}))
        assert_field_type(body, "updatedAt", str)

    def test_patch_name_only(self, client):
        resp = client.patch("/users/2", json={"name": "Patched Name"})
        assert_status(resp, 200)
        assert get_json(resp).get("name") == "Patched Name"

    def test_patch_response_time(self, client):
        assert_response_time(client.patch("/users/2", json={"job": "Staff QA"}), RESPONSE_TIME_MS)


# ===========================================================================
# DELETE /users/{id}
# ===========================================================================

@pytest.mark.api
class TestDeleteUser:

    def test_delete_user_returns_204(self, client):
        assert_status(client.delete("/users/2"), 204)

    def test_delete_user_body_is_empty(self, client):
        """204 No Content must not include a response body."""
        assert_body_is_empty(client.delete("/users/2"))

    def test_delete_user_response_time(self, client):
        assert_response_time(client.delete("/users/2"), RESPONSE_TIME_MS)

    def test_delete_returns_204_for_multiple_ids(self, client):
        """reqres.in simulates DELETE on any ID — all should return 204."""
        for user_id in (1, 3, 5):
            assert_status(client.delete(f"/users/{user_id}"), 204)
