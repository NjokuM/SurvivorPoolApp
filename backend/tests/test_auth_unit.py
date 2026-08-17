"""
Unit tests for JWT authentication utilities.
Tests token creation, decoding, expiry, and password hashing in isolation.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


# ==================== Password Hashing ====================

class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"

    def test_hash_password_different_each_time(self):
        """bcrypt uses a random salt, so two hashes of the same password differ."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_verify_password_correct(self):
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_string(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False


# ==================== Access Token ====================

class TestAccessToken:
    def test_create_access_token_returns_string(self):
        token = create_access_token(user_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_correct_claims(self):
        token = create_access_token(user_id=42)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "42"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_access_token_expiry_is_correct(self):
        before = datetime.now(timezone.utc)
        token = create_access_token(user_id=1)
        after = datetime.now(timezone.utc)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # JWT exp is integer seconds, so allow 1s tolerance for truncation
        expected_min = before + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) - timedelta(seconds=1)
        expected_max = after + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) + timedelta(seconds=1)

        assert expected_min <= exp <= expected_max

    def test_access_token_user_id_is_string(self):
        """sub claim should always be a string per JWT convention."""
        token = create_access_token(user_id=99)
        payload = decode_token(token)
        assert isinstance(payload["sub"], str)


# ==================== Refresh Token ====================

class TestRefreshToken:
    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token(user_id=1)
        assert isinstance(token, str)

    def test_refresh_token_contains_correct_claims(self):
        token = create_refresh_token(user_id=7)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "7"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_refresh_token_expiry_is_longer_than_access(self):
        access = create_access_token(user_id=1)
        refresh = create_refresh_token(user_id=1)

        access_payload = jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])

        assert refresh_payload["exp"] > access_payload["exp"]

    def test_refresh_token_expiry_is_correct(self):
        before = datetime.now(timezone.utc)
        token = create_refresh_token(user_id=1)
        after = datetime.now(timezone.utc)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # JWT exp is integer seconds, so allow 1s tolerance for truncation
        expected_min = before + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS) - timedelta(seconds=1)
        expected_max = after + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS) + timedelta(seconds=1)

        assert expected_min <= exp <= expected_max


# ==================== Token Decoding ====================

class TestDecodeToken:
    def test_decode_valid_access_token(self):
        token = create_access_token(user_id=5)
        payload = decode_token(token)
        assert payload["sub"] == "5"
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self):
        token = create_refresh_token(user_id=5)
        payload = decode_token(token)
        assert payload["sub"] == "5"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("this.is.not.a.valid.token")

    def test_decode_tampered_token_raises(self):
        token = create_access_token(user_id=1)
        # Flip a character in the signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_decode_token_wrong_secret_raises(self):
        token = create_access_token(user_id=1)
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=[ALGORITHM])

    def test_decode_expired_token_raises(self):
        """Manually create an already-expired token and verify it's rejected."""
        expired_payload = {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(expired_token)


# ==================== Token Type Distinction ====================

class TestTokenTypes:
    def test_access_and_refresh_tokens_are_different(self):
        access = create_access_token(user_id=1)
        refresh = create_refresh_token(user_id=1)
        assert access != refresh

    def test_access_token_type_is_access(self):
        token = create_access_token(user_id=1)
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_type_is_refresh(self):
        token = create_refresh_token(user_id=1)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_different_users_get_different_tokens(self):
        t1 = create_access_token(user_id=1)
        t2 = create_access_token(user_id=2)
        assert t1 != t2
