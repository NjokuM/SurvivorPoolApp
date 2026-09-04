"""
Sends push notifications via Expo's push API. Deliberately no SDK
dependency - it's a single POST endpoint, easier to call directly with
httpx (already a dependency) than to pull in exponent-server-sdk for one
call shape.
"""
import httpx
from typing import Optional

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """Send one push notification. Returns True on success, False on any
    failure - callers should not let a push failure block the caller's own
    transaction (e.g. results processing), just log and move on."""
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
    }
    if data:
        payload["data"] = data

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(EXPO_PUSH_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()
            # Expo returns {"data": {"status": "ok"}} or {"data": {"status": "error", ...}}
            ticket = result.get("data", {})
            if ticket.get("status") == "error":
                print(f"Expo push error for token {token[:20]}...: {ticket.get('message')}")
                return False
            return True
    except Exception as e:
        print(f"Failed to send push notification: {e}")
        return False
