from fastapi import Request, HTTPException, Depends
import time

MIN_FORM_TIME = 2  # seconds

async def bot_protect(request: Request):
    if request.method != "POST":
        return

    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    issued_at = request.cookies.get("csrf_issued_at")
    if not issued_at:
        raise HTTPException(status_code=403, detail="Missing CSRF timestamp")

    if int(time.time()) - int(issued_at) < MIN_FORM_TIME:
        raise HTTPException(status_code=403, detail="Form submitted too quickly")