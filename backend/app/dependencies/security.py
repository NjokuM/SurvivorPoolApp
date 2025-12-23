import os
from fastapi import Request, HTTPException
from dotenv import load_dotenv

load_dotenv()

CRON_SECRET = os.getenv("CRON_SECRET")

async def verify_cron(request: Request):
    header = request.headers.get("x-cron-secret")
    if header != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

print (CRON_SECRET)