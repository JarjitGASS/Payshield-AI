import os
from datetime import datetime, timedelta, timezone
from typing import Any

WINDOW_SECONDS = int(os.getenv("FRAUD_WINDOW_SECONDS", "120"))
IP_UNIQUE_USERS_THRESHOLD = int(os.getenv("FRAUD_IP_UNIQUE_USERS_THRESHOLD", "10"))
DEVICE_UNIQUE_USERS_THRESHOLD = int(os.getenv("FRAUD_DEVICE_UNIQUE_USERS_THRESHOLD", "3"))

def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def analyze_fraud(user_id: str, device_id: str, ip: str, login_history: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=WINDOW_SECONDS)

    recent = [e for e in login_history if _to_utc(e["timestamp"]) >= window_start]

    current_event = {
        "user_id": user_id,
        "device_id": device_id,
        "ip": ip,
        "timestamp": now,
    }
    recent_with_current = recent + [current_event]

    ip_unique_users = {e["user_id"] for e in recent_with_current if e["ip"] == ip}
    device_unique_users = {e["user_id"] for e in recent_with_current if e["device_id"] == device_id}

    flags: list[str] = []
    score = 0

    if len(ip_unique_users) >= IP_UNIQUE_USERS_THRESHOLD:
        flags.append("IP_SHARED_BURST")
        score += 70

    if len(device_unique_users) >= DEVICE_UNIQUE_USERS_THRESHOLD:
        flags.append("DEVICE_SHARED_BURST")
        score += 50

    if score >= 70:
        level = "high"
        action = "block"
    elif score >= 40:
        level = "medium"
        action = "step_up"
    else:
        level = "low"
        action = "allow"

    return {
        "risk_score": score,
        "risk_level": level,
        "recommended_action": action,
        "flags": flags,
        "metrics": {
            "window_seconds": WINDOW_SECONDS,
            "ip_unique_users_count": len(ip_unique_users),
            "device_unique_users_count": len(device_unique_users),
            "ip_threshold": IP_UNIQUE_USERS_THRESHOLD,
            "device_threshold": DEVICE_UNIQUE_USERS_THRESHOLD,
        },
    }