import os
import time
import httpx
from dotenv import load_dotenv
from jose import jwt, JWTError

# Loaded independently rather than relying on another module having already
# called this - see google_auth.py for why (import-order dependent env vars
# are a real footgun, not a hypothetical one).
load_dotenv()

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
# The audience for a native "Sign in with Apple" ID token is the app's
# bundle identifier, not a separate OAuth client id (unlike Google).
APPLE_BUNDLE_ID = os.getenv("APPLE_BUNDLE_ID")

_JWKS_CACHE_TTL_SECONDS = 3600
_jwks_cache = {"keys": None, "fetched_at": 0.0}


async def _get_apple_jwks(force_refresh: bool = False) -> list:
    now = time.time()
    if (
        not force_refresh
        and _jwks_cache["keys"] is not None
        and (now - _jwks_cache["fetched_at"]) < _JWKS_CACHE_TTL_SECONDS
    ):
        return _jwks_cache["keys"]

    async with httpx.AsyncClient() as client:
        response = await client.get(APPLE_KEYS_URL, timeout=10)
        response.raise_for_status()
        keys = response.json()["keys"]

    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


async def verify_apple_id_token(token: str) -> dict:
    """Verify a Sign in with Apple ID token's signature, audience, and issuer.

    Raises ValueError if the token is invalid, expired, or wasn't issued for
    this app's bundle ID.
    """
    if not APPLE_BUNDLE_ID:
        # Fail closed rather than silently accept an unverifiable audience -
        # same reasoning as GOOGLE_WEB_CLIENT_ID in google_auth.py.
        raise ValueError("APPLE_BUNDLE_ID is not configured")

    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except JWTError as e:
        raise ValueError(f"Invalid Apple token header: {e}")

    keys = await _get_apple_jwks()
    key_data = next((k for k in keys if k["kid"] == kid), None)
    if not key_data:
        # Apple may have rotated keys since we last cached them.
        keys = await _get_apple_jwks(force_refresh=True)
        key_data = next((k for k in keys if k["kid"] == kid), None)
        if not key_data:
            raise ValueError("Apple signing key not found")

    try:
        return jwt.decode(
            token,
            key_data,
            algorithms=["RS256"],
            audience=APPLE_BUNDLE_ID,
            issuer=APPLE_ISSUER,
        )
    except JWTError as e:
        raise ValueError(f"Invalid Apple token: {e}")
