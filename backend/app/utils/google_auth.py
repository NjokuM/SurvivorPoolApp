import os
from dotenv import load_dotenv
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

# Loaded independently (rather than relying on another module having already
# called this) since main.py imports routers - which import this module -
# before it calls load_dotenv() itself. Without this, GOOGLE_WEB_CLIENT_ID
# could resolve to None depending on import order, which silently disables
# audience verification (see verify_oauth2_token's docstring).
load_dotenv()

GOOGLE_WEB_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")

_google_request = google_requests.Request()


def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token's signature and audience, returning its claims.

    Raises ValueError (via google-auth) if the token is invalid, expired, or
    wasn't issued for this app's Google Web Client ID.
    """
    if not GOOGLE_WEB_CLIENT_ID:
        # Passing audience=None to verify_oauth2_token skips audience checking
        # entirely, which would accept any Google-issued token from any app.
        # Fail closed instead of silently accepting everything.
        raise ValueError("GOOGLE_WEB_CLIENT_ID is not configured")
    return google_id_token.verify_oauth2_token(token, _google_request, GOOGLE_WEB_CLIENT_ID)
