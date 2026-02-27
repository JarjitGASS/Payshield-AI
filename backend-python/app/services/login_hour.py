import json
from datetime import datetime
from qwen.qwen import qwen_chat
# from services.auth_service import save_login_hour, get_login_hours

async def save_login_hour(redis, user_id: str, hour: int):
    key = f"login_hours:{user_id}"

    redis.lpush(key, hour)

    redis.ltrim(key, 0, 49)

async def get_login_hours(redis, user_id: str):
    key = f"login_hours:{user_id}"

    hours = redis.lrange(key, 0, -1)

    return [int(h) for h in hours]

async def analyze_login_hour(user_profile: dict):
    current_hour = datetime.now().hour

    prompt = f"""
ROLE:
You are a fraud detection system analyzing user login time behavior.

INPUT:
- Current login hour: {current_hour}
- User historical login hours: {user_profile.get("hours", [])}

TASK:
Determine whether this login time is suspicious.

EVALUATION CRITERIA:
1. If current hour is far outside typical pattern → suspicious
2. If user has no history → not suspicious
3. If occasional outliers exist → low suspicion
4. Consider human variability (not too strict)

OUTPUT:
Return ONLY JSON.

FORMAT:
{{
  "is_anomalous": boolean,
  "risk_level": "low" | "medium" | "high",
  "confidence": number
}}
"""

    system = "You are a strict fraud detection classifier. Output JSON only."

    raw = qwen_chat(system, prompt)

    try:
        return json.loads(raw)
    except:
        return {
            "is_anomalous": False,
            "risk_level": "low",
            "confidence": 0.0
        }

async def login_hour_service(user_id: str, redis):
    current_hour = datetime.now().hour
    await save_login_hour(redis, user_id, current_hour)

    hours = await get_login_hours(redis, user_id)

    result = await analyze_login_hour({
        "hours": hours
    })

    return result

