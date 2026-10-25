"""
Tests for the forgot-password flow: POST /forgot-password emails a 6-digit
code, POST /reset-password exchanges it for a new password.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import re
import pytest
from datetime import datetime, timedelta, timezone
from app.routers import auth_router


@pytest.fixture
def outbox(monkeypatch):
    """Capture sent emails instead of hitting SMTP."""
    sent = []

    async def fake_send(to, subject, body):
        sent.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr(auth_router, "email_configured", lambda: True)
    monkeypatch.setattr(auth_router, "send_email", fake_send)
    return sent


def _code(email):
    return re.search(r"\b(\d{6})\b", email["body"]).group(1)


async def _reset(client, code, email="test@example.com", new_password="newpassword1"):
    return await client.post("/reset-password", json={"email": email, "code": code, "new_password": new_password})


class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_sends_code_to_existing_user(self, client, test_user, outbox):
        res = await client.post("/forgot-password", json={"email": "Test@Example.com"})
        assert res.status_code == 200
        assert len(outbox) == 1
        assert outbox[0]["to"] == "test@example.com"
        assert _code(outbox[0])

    @pytest.mark.asyncio
    async def test_unknown_email_gets_same_response_and_no_email(self, client, test_user, outbox):
        known = await client.post("/forgot-password", json={"email": "test@example.com"})
        unknown = await client.post("/forgot-password", json={"email": "nobody@example.com"})
        assert unknown.status_code == known.status_code == 200
        assert unknown.json() == known.json()
        assert len(outbox) == 1

    @pytest.mark.asyncio
    async def test_resend_cooldown(self, client, test_user, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        await client.post("/forgot-password", json={"email": "test@example.com"})
        assert len(outbox) == 1

    @pytest.mark.asyncio
    async def test_unconfigured_email_returns_503(self, client, test_user, monkeypatch):
        monkeypatch.setattr(auth_router, "email_configured", lambda: False)
        res = await client.post("/forgot-password", json={"email": "test@example.com"})
        assert res.status_code == 503

    @pytest.mark.asyncio
    async def test_send_failure_returns_503(self, client, test_user, monkeypatch):
        async def boom(*args):
            raise RuntimeError("smtp down")
        monkeypatch.setattr(auth_router, "email_configured", lambda: True)
        monkeypatch.setattr(auth_router, "send_email", boom)
        res = await client.post("/forgot-password", json={"email": "test@example.com"})
        assert res.status_code == 503


class TestResetPassword:
    @pytest.mark.asyncio
    async def test_valid_code_resets_password_and_logs_in(self, client, test_user, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        res = await _reset(client, _code(outbox[0]))
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["user"]["id"] == test_user.id
        assert "access_token" in data

        old = await client.post("/login", data={"email": "test@example.com", "password": "password123"})
        assert old.json()["success"] is False
        new = await client.post("/login", data={"email": "test@example.com", "password": "newpassword1"})
        assert new.json()["success"] is True

    @pytest.mark.asyncio
    async def test_code_is_single_use(self, client, test_user, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        code = _code(outbox[0])
        assert (await _reset(client, code)).status_code == 200
        assert (await _reset(client, code, new_password="another1234")).status_code == 400

    @pytest.mark.asyncio
    async def test_wrong_code_rejected(self, client, test_user, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        wrong = "000000" if _code(outbox[0]) != "000000" else "111111"
        res = await _reset(client, wrong)
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_locks_after_too_many_wrong_attempts(self, client, test_user, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        code = _code(outbox[0])
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(auth_router.RESET_CODE_MAX_ATTEMPTS):
            await _reset(client, wrong)
        # Even the right code is refused once the attempts are used up.
        assert (await _reset(client, code)).status_code == 400

    @pytest.mark.asyncio
    async def test_expired_code_rejected(self, client, test_user, outbox, db_session):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        await db_session.refresh(test_user)
        test_user.password_reset_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.commit()
        assert (await _reset(client, _code(outbox[0]))).status_code == 400

    @pytest.mark.asyncio
    async def test_no_code_requested(self, client, test_user):
        assert (await _reset(client, "123456")).status_code == 400

    @pytest.mark.asyncio
    async def test_short_password_rejected(self, client, test_user, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        res = await _reset(client, _code(outbox[0]), new_password="short")
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_reset_invalidates_existing_sessions(self, client, test_user, auth_headers, outbox):
        await client.post("/forgot-password", json={"email": "test@example.com"})
        await _reset(client, _code(outbox[0]))
        res = await client.get("/me", headers=auth_headers)
        assert res.status_code == 401
