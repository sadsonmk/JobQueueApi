import uuid

from app.core.security import hash_password


def _email():
    return f"{uuid.uuid4().hex[:10]}@test.com"


async def test_register(client):
    resp = await client.post("/auth/register", json={
        "email": _email(), "password": "secret123",
    })
    assert resp.status_code == 201
    assert "hashed_password" not in resp.json()


async def test_register_duplicate(client):
    email = _email()
    first = await client.post("/auth/register", json={
        "email": email, "password": "secret123"})
    second = await client.post("/auth/register", json={
        "email": email, "password": "secret123"})
    assert first.status_code == 201
    assert second.status_code == 409


async def test_login_wrong_password_same_error_as_unknown_user(client, user):
    r1 = await client.post("/auth/login", json={
        "email": "ghost@example.com", "password": "x"})
    r2 = await client.post("/auth/login", json={
        "email": user.email, "password": "wrong"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


async def test_protected_route_requires_token(client):
    resp = await client.get("/jobs")
    assert resp.status_code in (401, 403)