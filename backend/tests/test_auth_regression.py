"""
Regression tests for authentication endpoints.
Tests the full HTTP flow: signup, login, /me, /refresh, /logout.
Uses httpx AsyncClient against the real FastAPI app with an in-memory DB.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
from jose import jwt
from app.utils.auth import SECRET_KEY, ALGORITHM, create_access_token, create_refresh_token
from datetime import datetime, timedelta, timezone


# ==================== Signup ====================

class TestSignup:
    @pytest.mark.asyncio
    async def test_signup_success(self, client):
        res = await client.post("/signup", data={
            "userName": "newuser",
            "email": "new@example.com",
            "password": "securepass",
            "firstName": "New",
            "lastName": "User",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "User created successfully"
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_signup_logs_user_in(self, client):
        """Signup should return a usable token pair, same as /login - the
        user shouldn't have to re-enter credentials on a second screen
        right after creating the account."""
        res = await client.post("/signup", data={
            "userName": "autologin",
            "email": "autologin@example.com",
            "password": "securepass",
            "firstName": "Auto",
            "lastName": "Login",
        })
        data = res.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "autologin@example.com"

        me_res = await client.get("/me", headers={"Authorization": f"Bearer {data['access_token']}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "autologin@example.com"

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client, test_user):
        res = await client.post("/signup", data={
            "userName": "different",
            "email": "test@example.com",  # same as test_user
            "password": "pass123",
            "firstName": "Dup",
            "lastName": "User",
        })
        assert res.status_code == 400
        assert "Email already in use" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_duplicate_username(self, client, test_user):
        res = await client.post("/signup", data={
            "userName": "testuser",  # same as test_user
            "email": "different@example.com",
            "password": "pass123",
            "firstName": "Dup",
            "lastName": "User",
        })
        assert res.status_code == 400
        assert "Username already taken" in res.json()["detail"]


# ==================== Login ====================

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self, client, test_user):
        res = await client.post("/login", data={
            "email": "test@example.com",
            "password": "password123",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["id"] == test_user.id
        assert data["user"]["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        res = await client.post("/login", data={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is False
        assert "Invalid credentials" in data["message"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        res = await client.post("/login", data={
            "email": "nobody@example.com",
            "password": "whatever",
        })
        data = res.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_login_tokens_are_valid_jwt(self, client, test_user):
        res = await client.post("/login", data={
            "email": "test@example.com",
            "password": "password123",
        })
        data = res.json()
        access_payload = jwt.decode(data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(data["refresh_token"], SECRET_KEY, algorithms=[ALGORITHM])

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_payload["sub"] == str(test_user.id)
        assert refresh_payload["sub"] == str(test_user.id)


# ==================== /me (Protected Route) ====================

class TestMe:
    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, client, test_user, auth_headers):
        res = await client.get("/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_me_without_token_returns_403(self, client):
        res = await client.get("/me")
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(self, client):
        res = await client.get("/me", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_expired_token_returns_401(self, client, test_user):
        expired_payload = {
            "sub": str(test_user.id),
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        res = await client.get("/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_refresh_token_returns_401(self, client, auth_tokens):
        """Using a refresh token on a protected route should fail."""
        res = await client.get("/me", headers={
            "Authorization": f"Bearer {auth_tokens['refresh_token']}"
        })
        assert res.status_code == 401
        assert "Invalid token type" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_me_with_nonexistent_user_returns_401(self, client):
        """Token for a user ID that doesn't exist in DB."""
        token = create_access_token(user_id=99999)
        res = await client.get("/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert res.status_code == 401
        assert "User not found" in res.json()["detail"]


# ==================== /refresh ====================

class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_with_valid_token(self, client, test_user, auth_tokens):
        res = await client.post("/refresh", data={
            "refresh_token": auth_tokens["refresh_token"],
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Verify new tokens are valid JWTs with correct claims
        access_payload = jwt.decode(data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(data["refresh_token"], SECRET_KEY, algorithms=[ALGORITHM])
        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client, auth_tokens):
        """Using an access token for refresh should fail."""
        res = await client.post("/refresh", data={
            "refresh_token": auth_tokens["access_token"],
        })
        assert res.status_code == 401
        assert "Invalid token type" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token_fails(self, client):
        res = await client.post("/refresh", data={
            "refresh_token": "not.a.real.token",
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_fails(self, client, test_user):
        expired_payload = {
            "sub": str(test_user.id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        res = await client.post("/refresh", data={
            "refresh_token": expired_token,
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_returns_working_access_token(self, client, test_user, auth_tokens):
        """After refresh, the new access token should work on /me."""
        refresh_res = await client.post("/refresh", data={
            "refresh_token": auth_tokens["refresh_token"],
        })
        new_access = refresh_res.json()["access_token"]

        me_res = await client.get("/me", headers={
            "Authorization": f"Bearer {new_access}"
        })
        assert me_res.status_code == 200
        assert me_res.json()["id"] == test_user.id


# ==================== /logout ====================

class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_returns_success(self, client, auth_headers):
        res = await client.post("/logout", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["message"] == "Logged out"

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_403(self, client):
        res = await client.post("/logout")
        assert res.status_code == 403


# ==================== Full Auth Flow ====================

class TestFullAuthFlow:
    @pytest.mark.asyncio
    async def test_signup_login_me_refresh_flow(self, client):
        """End-to-end: signup -> login -> /me -> refresh -> /me again."""
        # 1. Signup
        signup_res = await client.post("/signup", data={
            "userName": "flowuser",
            "email": "flow@example.com",
            "password": "flowpass123",
            "firstName": "Flow",
            "lastName": "Test",
        })
        assert signup_res.status_code == 200

        # 2. Login
        login_res = await client.post("/login", data={
            "email": "flow@example.com",
            "password": "flowpass123",
        })
        assert login_res.json()["success"] is True
        tokens = login_res.json()

        # 3. Access /me with access token
        me_res = await client.get("/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "flow@example.com"

        # 4. Refresh tokens
        refresh_res = await client.post("/refresh", data={
            "refresh_token": tokens["refresh_token"],
        })
        assert refresh_res.status_code == 200
        new_tokens = refresh_res.json()

        # 5. Access /me with new access token
        me_res2 = await client.get("/me", headers={
            "Authorization": f"Bearer {new_tokens['access_token']}"
        })
        assert me_res2.status_code == 200
        assert me_res2.json()["email"] == "flow@example.com"
