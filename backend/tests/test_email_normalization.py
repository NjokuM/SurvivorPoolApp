"""
Emails are case-insensitive: "Michael@email.com" and "michael@email.com"
must resolve to the same account on signup and login.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
from sqlalchemy import select
from app.models.user import User
from app.utils.auth import hash_password, normalize_email


def _signup_form(email, userName="michael"):
    return {
        "userName": userName,
        "email": email,
        "password": "securepass",
        "firstName": "Michael",
        "lastName": "N",
    }


def test_normalize_email_lowercases_and_strips():
    assert normalize_email("  Michael@Email.COM ") == "michael@email.com"


class TestSignupNormalization:
    @pytest.mark.asyncio
    async def test_signup_stores_lowercase_email(self, client, db_session):
        res = await client.post("/signup", data=_signup_form(" Michael@Email.com "))
        assert res.status_code == 200
        assert res.json()["user"]["email"] == "michael@email.com"

        user = (await db_session.execute(select(User).where(User.userName == "michael"))).scalar_one()
        assert user.email == "michael@email.com"

    @pytest.mark.asyncio
    async def test_signup_rejects_case_variant_of_existing_email(self, client, test_user):
        # test_user is test@example.com
        res = await client.post("/signup", data=_signup_form("TEST@Example.com"))
        assert res.status_code == 400
        assert "Email already in use" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_rejects_lowercase_of_legacy_mixed_case_email(self, client, db_session):
        """Accounts created before normalization may be stored mixed-case."""
        db_session.add(User(
            userName="legacy", email="Legacy@Example.com",
            password=hash_password("password123"), firstName="L", lastName="U",
        ))
        await db_session.commit()

        res = await client.post("/signup", data=_signup_form("legacy@example.com"))
        assert res.status_code == 400


class TestLoginNormalization:
    @pytest.mark.asyncio
    async def test_login_with_different_case(self, client, test_user):
        res = await client.post("/login", data={"email": " Test@EXAMPLE.com", "password": "password123"})
        data = res.json()
        assert data["success"] is True
        assert data["user"]["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_login_matches_legacy_mixed_case_account(self, client, db_session):
        legacy = User(
            userName="legacy", email="Legacy@Example.com",
            password=hash_password("password123"), firstName="L", lastName="U",
        )
        db_session.add(legacy)
        await db_session.commit()

        res = await client.post("/login", data={"email": "legacy@example.com", "password": "password123"})
        data = res.json()
        assert data["success"] is True
        assert data["user"]["id"] == legacy.id

    @pytest.mark.asyncio
    async def test_signup_then_login_with_other_case(self, client):
        await client.post("/signup", data=_signup_form("Michael@email.com"))
        res = await client.post("/login", data={"email": "michael@email.com", "password": "securepass"})
        assert res.json()["success"] is True
