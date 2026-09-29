import copy


def test_register_creates_user_and_pet(client, register_payload):
    resp = client.post("/api/auth/register", json=register_payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == register_payload["email"]
    assert body["user"]["username"] == register_payload["username"]
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]
    assert body["pet"]["name"] == "Bruno"
    assert body["pet"]["species"] == "dog"

    # Registration should auto-login: the session cookie must be set.
    assert "pawai_session" in resp.cookies


def test_register_rejects_duplicate_email(client, register_payload):
    client.post("/api/auth/register", json=register_payload)

    second = copy.deepcopy(register_payload)
    second["username"] = "someone_else"
    resp = client.post("/api/auth/register", json=second)
    assert resp.status_code == 409
    assert "email" in resp.json()["detail"].lower()


def test_register_rejects_duplicate_username(client, register_payload):
    client.post("/api/auth/register", json=register_payload)

    second = copy.deepcopy(register_payload)
    second["email"] = "someone-else@example.com"
    resp = client.post("/api/auth/register", json=second)
    assert resp.status_code == 409
    assert "username" in resp.json()["detail"].lower()


def test_register_rejects_weak_password(client, register_payload):
    bad = copy.deepcopy(register_payload)
    bad["password"] = "alllettersnodigits"
    resp = client.post("/api/auth/register", json=bad)
    assert resp.status_code == 422


def test_register_rejects_short_password(client, register_payload):
    bad = copy.deepcopy(register_payload)
    bad["password"] = "a1"
    resp = client.post("/api/auth/register", json=bad)
    assert resp.status_code == 422


def test_password_is_never_stored_in_plaintext(client, register_payload, db_session):
    client.post("/api/auth/register", json=register_payload)

    from app.models.user import User

    user = db_session.query(User).filter_by(email=register_payload["email"]).one()
    assert user.password_hash != register_payload["password"]
    assert user.password_hash.startswith("$argon2id$")


def test_login_with_correct_credentials_succeeds(client, register_payload):
    client.post("/api/auth/register", json=register_payload)

    resp = client.post(
        "/api/auth/login",
        json={
            "identifier": register_payload["username"],
            "password": register_payload["password"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == register_payload["username"]
    assert "pawai_session" in resp.cookies


def test_login_with_email_as_identifier_succeeds(client, register_payload):
    client.post("/api/auth/register", json=register_payload)

    resp = client.post(
        "/api/auth/login",
        json={
            "identifier": register_payload["email"],
            "password": register_payload["password"],
        },
    )
    assert resp.status_code == 200


def test_login_with_wrong_password_fails(client, register_payload):
    client.post("/api/auth/register", json=register_payload)

    resp = client.post(
        "/api/auth/login",
        json={"identifier": register_payload["username"], "password": "totally-wrong-1"},
    )
    assert resp.status_code == 401
    assert "pawai_session" not in resp.cookies


def test_login_with_nonexistent_user_fails_same_as_wrong_password(client):
    resp = client.post(
        "/api/auth/login",
        json={"identifier": "nobody_here", "password": "whatever-1"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username/email or password."


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_when_authenticated(client, register_payload):
    client.post("/api/auth/register", json=register_payload)
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == register_payload["username"]


def test_logout_clears_session_so_me_fails_afterward(client, register_payload):
    client.post("/api/auth/register", json=register_payload)
    assert client.get("/api/auth/me").status_code == 200

    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_succeeds_when_the_session_is_already_expired(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Logged out."}


def test_expired_session_is_rejected(client, register_payload, db_session):
    from datetime import datetime, timedelta, timezone

    client.post("/api/auth/register", json=register_payload)

    from app.models.session import SessionModel

    session_row = db_session.query(SessionModel).one()
    session_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_forgot_password_is_deferred_not_implemented(client):
    resp = client.post("/api/auth/password/forgot", json={"email": "a@b.com"})
    assert resp.status_code == 501


def test_reset_password_is_deferred_not_implemented(client):
    resp = client.post(
        "/api/auth/password/reset", json={"token": "x", "new_password": "y12345678"}
    )
    assert resp.status_code == 501


def test_login_rate_limit(client, register_payload):
    client.post("/api/auth/register", json=register_payload)
    for _ in range(10):
        resp = client.post("/api/auth/login", json={"identifier": register_payload["username"], "password": "wrong-1"})
        assert resp.status_code == 401
    limited = client.post("/api/auth/login", json={"identifier": register_payload["username"], "password": "wrong-1"})
    assert limited.status_code == 429
