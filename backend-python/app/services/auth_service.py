import json
from qwen.qwen import qwen_chat
from dtos.auth_input import LoginRequest
from dtos.auth_result import LoginResponse, BehaviorAnalysis
from database.database import SessionLocal
from model.model import User
from argon2 import PasswordHasher


async def login_service(body: LoginRequest) -> LoginResponse:
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.username == body.username).first()
        if not user:
            return LoginResponse(
            success=False,
            message="Invalid credentials"
            )

        # Create prompt for behavioral analysis
        prompt = f"""
ROLE:
You are a behavioral security system specialized in distinguishing humans from automated bots.

INPUT:
You are given a chronological list of browser interaction events from a single session.
Each event may include:
- t: timestamp in milliseconds
- x, y: cursor coordinates
- key: keyboard key
- type: mousemove | keydown | keyup

TASK:
Analyze the interaction data and determine whether the session behavior is more likely Human or Bot.

EVALUATION CRITERIA (use all that apply):
1. Mouse dynamics:
  - Human: curved paths, variable speed, micro-corrections, pauses
  - Bot: linear paths, constant velocity, repeated coordinates

2. Timing characteristics:
  - Human: irregular reaction times, natural pauses
  - Bot: uniform or unrealistically fast intervals

3. Keyboard behavior:
  - Human: realistic key press durations and overlaps
  - Bot: instantaneous or perfectly timed sequences

4. Input coordination:
  - Human: natural alternation between mouse and keyboard
  - Bot: rigid or mechanically ordered patterns

5. Data quality:
  - If the dataset is sparse, noisy, or insufficient, reduce confidence accordingly.

DECISION RULES:
- Classify as "Bot" only if multiple strong bot indicators are present.
- Otherwise, classify as "Human".
- Confidence must reflect certainty given the data quality.

OUTPUT:
Return ONLY valid JSON.
Do NOT include explanations, markdown, or extra text.

FORMAT:
{{
  "classification": "Human" | "Bot",
  "confidence": number
}}

INTERACTION DATA:
{json.dumps(body.behavior)}
"""

        system_prompt = "You are a deterministic security classifier. Output must be strict JSON only."

        # Get analysis from Qwen
        raw_analysis = qwen_chat(system_prompt, prompt)

        # Parse analysis result
        try:
            analysis = json.loads(raw_analysis.strip())
            behavior_analysis = BehaviorAnalysis(**analysis)
        except (json.JSONDecodeError, ValueError):
            return LoginResponse(
                success=False,
                message="Behavior analysis failed"
            )

        # Check if behavior is detected as bot
        if behavior_analysis.classification == "Bot" and behavior_analysis.confidence >= 0.5:
            return LoginResponse(
                success=False,
                message="Login blocked: automated behavior detected",
                analysis=raw_analysis
            )

        return LoginResponse(
            success=True,
            message="Login successful",
            analysis=raw_analysis
        )

    except Exception as err:
        print(f"Login error: {err}")
        return LoginResponse(
            success=False,
            message="Login failed"
        )
