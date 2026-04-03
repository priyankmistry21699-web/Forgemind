"""FM-074 — Authentication tests: register, login, token verification, /auth/me."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "securepass123",
                "display_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "dup@test.com",
            "password": "securepass123",
            "display_name": "Dup User",
        }
        # First registration
        resp1 = await client.post("/auth/register", json=payload)
        assert resp1.status_code == 201

        # Second registration with same email
        resp2 = await client.post("/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_missing_fields(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "incomplete@test.com",
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestAuthLogin:
    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post(
            "/auth/register",
            json={
                "email": "login@test.com",
                "password": "mypassword",
                "display_name": "Login User",
            },
        )

        # Login
        resp = await client.post(
            "/auth/login",
            json={
                "email": "login@test.com",
                "password": "mypassword",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "email": "wrongpw@test.com",
                "password": "correctpassword",
                "display_name": "WP User",
            },
        )

        resp = await client.post(
            "/auth/login",
            json={
                "email": "wrongpw@test.com",
                "password": "incorrectpassword",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            json={
                "email": "nobody@test.com",
                "password": "anything",
            },
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestAuthMe:
    async def test_get_me_with_token(self, client: AsyncClient):
        # Register to get token
        reg = await client.post(
            "/auth/register",
            json={
                "email": "me@test.com",
                "password": "mepassword",
                "display_name": "Me User",
            },
        )
        token = reg.json()["access_token"]

        # Access /auth/me
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@test.com"
        assert data["display_name"] == "Me User"
        assert data["is_active"] is True

    async def test_get_me_no_token_dev_mode(self, client: AsyncClient):
        # In dev mode (secret_key == default), returns stub user
        # Stub user exists (seeded by conftest) so should return 200
        resp = await client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@forgemind.dev"


@pytest.mark.asyncio
class TestPasswordSecurity:
    async def test_password_hashed_not_plaintext(self, client: AsyncClient):
        """Verify passwords are stored hashed, not in plaintext."""
        from app.api.routes.auth import _hash_password, _verify_password

        hashed = _hash_password("test123")
        assert "test123" not in hashed
        assert "$" in hashed  # salt$hash format
        assert _verify_password("test123", hashed) is True
        assert _verify_password("wrong", hashed) is False

    async def test_different_passwords_different_hashes(self, client: AsyncClient):
        from app.api.routes.auth import _hash_password

        h1 = _hash_password("password1")
        h2 = _hash_password("password2")
        assert h1 != h2
