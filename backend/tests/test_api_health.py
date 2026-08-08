"""
Endpoint-level tests that do NOT require a live database.

These exercise the parts of the request lifecycle that run before any DB
access: the health route, auth-token rejection, and Pydantic request
validation. Tests that would hit Postgres are intentionally omitted (see the
plan: pure-unit + mocked API, no test DB).
"""


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_db_responds_with_status_key(self, client):
        # No DB in the test env — the endpoint catches the failure and returns
        # a graceful body rather than raising. We assert on shape, not on
        # connectivity.
        resp = client.get("/health/db")
        assert resp.status_code == 200
        assert "status" in resp.json()


class TestAuthGuards:
    def test_me_without_token_is_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_garbage_token_is_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer nonsense"})
        assert resp.status_code == 401


class TestRequestValidation:
    def test_signup_empty_body_is_422(self, client):
        resp = client.post("/auth/signup", json={})
        assert resp.status_code == 422

    def test_signup_invalid_email_is_422(self, client):
        resp = client.post(
            "/auth/signup",
            json={"name": "A", "email": "not-an-email", "password": "secret123"},
        )
        assert resp.status_code == 422
