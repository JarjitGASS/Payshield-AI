from fastapi import Request
from datetime import datetime, timezone
import json
from dtos.network_input import NetworkInput

from services.verify_geoip import get_real_ip
from services.network_signal import get_network_signals

from database.redis_client import redis_client

NETWORK_LOGIN_HISTORY_KEY = "network:login_history"
NETWORK_LOGIN_HISTORY_MAX_LEN = 5000

def _fetch_login_history(limit: int = NETWORK_LOGIN_HISTORY_MAX_LEN) -> list[dict]:
    raw_logs = redis_client.lrange(NETWORK_LOGIN_HISTORY_KEY, 0, max(limit - 1, 0))
    parsed_logs = []

    for raw in raw_logs:
        try:
            decoded = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            parsed_logs.append(json.loads(decoded))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            continue

    return parsed_logs

def build_network_features(
    request: Request,
    device_id: str,
) -> tuple[str, NetworkInput]:
    client_ip = get_real_ip(request)
    login_history = _fetch_login_history()
    signals = get_network_signals(client_ip, device_id, login_history)
    return client_ip, signals


def append_login_history(
    user_id: str,
    ip: str,
    device_id: str,
) -> None:
    log_entry = {
        "user_id": user_id,
        "ip": ip,
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    payload = json.dumps(log_entry)
    pipe = redis_client.pipeline()
    pipe.lpush(NETWORK_LOGIN_HISTORY_KEY, payload)
    pipe.ltrim(NETWORK_LOGIN_HISTORY_KEY, 0, NETWORK_LOGIN_HISTORY_MAX_LEN - 1)
    pipe.execute()