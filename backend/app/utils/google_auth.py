import os
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

GOOGLE_WEB_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")

_google_request = google_requests.Request()


def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token's signature and audience, returning its claims.

    Raises ValueError (via google-auth) if the token is invalid, expired, or
    wasn't issued for this app's Google Web Client ID.
    """
    return google_id_token.verify_oauth2_token(token, _google_request, GOOGLE_WEB_CLIENT_ID)
