"""Tests for PATCH /users/me - editing username, email and name."""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
import pytest_asyncio
from app.models.user import User
from app.utils.auth import hash_password


@pytest_asyncio.fixture
async def other_user(db_session):
    user = User(userName="taken", email="taken@example.com", password=hash_password("pw123456"),
                firstName="O", lastName="U")
    db_session.add(user)
    await db_session.commit()
    return user


class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_updates_all_fields(self, client, test_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={
            "userName": " newname ", "email": " New@Example.com ",
            "firstName": " Mike ", "lastName": "Njoku",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["userName"] == "newname"
        assert data["email"] == "new@example.com"
        assert data["firstName"] == "Mike"
        assert data["lastName"] == "Njoku"

        # Can log in with the new email
        login = await client.post("/login", data={"email": "new@example.com", "password": "password123"})
        assert login.json()["success"] is True

    @pytest.mark.asyncio
    async def test_partial_update_leaves_other_fields(self, client, test_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={"firstName": "Only"})
        data = res.json()
        assert data["firstName"] == "Only"
        assert data["userName"] == "testuser"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_saving_unchanged_values_is_fine(self, client, test_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={
            "userName": "testuser", "email": "TEST@example.com",
        })
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_username_taken(self, client, test_user, other_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={"userName": "taken"})
        assert res.status_code == 400
        assert "Username already taken" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_email_taken_case_insensitive(self, client, test_user, other_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={"email": "TAKEN@example.com"})
        assert res.status_code == 400
        assert "Email already in use" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_blank_username_rejected(self, client, test_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={"userName": "   "})
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_email_rejected(self, client, test_user, auth_headers):
        res = await client.patch("/users/me", headers=auth_headers, json={"email": "not-an-email"})
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_auth(self, client, test_user):
        res = await client.patch("/users/me", json={"firstName": "X"})
        assert res.status_code in (401, 403)
