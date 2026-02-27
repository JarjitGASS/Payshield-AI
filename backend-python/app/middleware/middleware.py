from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time

MIN_FORM_TIME = 2  # seconds

class BotProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            # --- CSRF token ---
            csrf_cookie = request.cookies.get("csrf_token")
            csrf_header = request.headers.get("X-CSRF-Token")

            if not csrf_cookie or csrf_cookie != csrf_header:
                raise HTTPException(403, "Invalid CSRF token")

            # --- Token issued time ---
            issued_at = request.cookies.get("csrf_issued_at")
            if not issued_at:
                raise HTTPException(403, "Missing token timestamp")

            if int(time.time()) - int(issued_at) < MIN_FORM_TIME:
                raise HTTPException(403, "Form submitted too quickly")

            # --- Honeypot ---
            body = await request.json()
            if body.get("company_website"):
                raise HTTPException(403, "Bot detected")

        return await call_next(request)