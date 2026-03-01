from webbrowser import get

import database.redis_client
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, APIRouter, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import model.model
from dotenv import load_dotenv
from services.check_id_card import check_id_card
from services.verivfy_id_card import verify_id_card
from services.verify_email_age_card import verify_email_age
from services.name_entropy import shannon_entropy, has_digits_or_symbols, ngram_entropy
from services.verify_geoip import check_geo_ip, get_real_ip
from services.sentiment_entity import analyze_company_sentiment
from services.auth_service import login_service
from services.navigation_consistency_score import navigation_consistency_score, store_click_position
from services.login_hour import login_hour_service
from database.redis_client import redis_client
from dtos.auth_input import LoginRequest
from dtos.auth_result import LoginResponse
from database.database import SessionLocal
import model, database.database
from services.network_fraud import build_network_features, append_login_history
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import secrets, time
from middleware.middleware import bot_protect
from dtos.identity_input import IdentityInput
from dtos.behavioral_input import BehavioralInput
from dtos.network_input import NetworkInput
from dtos.session_state import SessionState
from dtos.human_review_input import HumanReviewInput, HumanReviewResponse, ReviewRating
from agents.identity_risk_agent import run_identity_agent
from agents.behavioral_agent import run_behavioral_agent
from agents.synthetic_network_agent import run_network_agent
from agents.orchestrator import run_orchestrator
from guardrails.result_validation import enforce_policy
from services.rag_service import store_human_review, fetch_pending_reviews
from services.user_activation import activate_user, deactivate_user
import uuid
import asyncio

load_dotenv()
database.database.Base.metadata.create_all(bind=database.database.engine)

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:80",
    "http://localhost:85",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    
    allow_credentials=True,     
    allow_methods=["*"],               
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/csrf")
def issue_csrf(response: Response):
    os.getenv("SECRET_KEY")
    token = secrets.token_hex(32)
    issued_at = str(int(time.time()))

    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=True,
        samesite="lax"  
    )
    response.set_cookie(
        key="csrf_issued_at",
        value=issued_at,
        httponly=True,
        samesite="strict"
    )

    return {"csrfToken": token}

@app.post("/auth/login", dependencies=[Depends(bot_protect)])
async def login(body: LoginRequest) -> LoginResponse:
    return await login_service(body)

@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    nik: str = Form(...),
    fullname: str = Form(...),
    pob: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    file: UploadFile = File(...)
    # blm ada email
):
    return await check_id_card(username, password, confirmPassword, file, nik, fullname, pob, dob, gender)

@app.post("/verify-id-card")
async def verify_id_card_endpoint(file: UploadFile = File(...)):
    return await verify_id_card(file)

@app.post("/verify-email-age")
async def verify_email_age_endpoint(email: str = Form()):
    return await verify_email_age(email)

@app.post("/validate-name-entropy")
async def validate_name_entropy(name: str = Form()):
    #entropy g cukup karena kurang akurat jadi harus ada digit validation juga
    shannon_result = shannon_entropy(name)
    ngram_result = ngram_entropy(name)
    name_has_digit_or_symbols = has_digits_or_symbols(name)
    return {
        "status": 200,
        "name": name,
        "shannon_entropy": shannon_result,
        "ngram_entropy": ngram_result,
        "digitsOrSymbols": name_has_digit_or_symbols
    }

@app.post("/verify-geo-ip")
async def verify_geo_ip_endpoint(
    request: Request,
    declared_country: str = Form(),
    declared_city: str = Form(None)
):

    ip = get_real_ip(request)

    return await check_geo_ip(ip, declared_country, declared_city)

@app.post("/sentiment-entity-analysis")
async def sentiment_entity_analysis(
    company_name: str = Form(...)
):
    result = await analyze_company_sentiment(company_name)

    return result

@app.post("/store-click")
async def store_click(
    user_id: str = Form(...),
    x: int = Form(...),
    y: int = Form(...)
):
    store_click_position(user_id, x, y)

    result = navigation_consistency_score(user_id, 0)
    print(x, y, result, user_id)
    return {
        "status": "ok",
        "user_id": user_id,
        "entropy": result,
    }

@app.post("/verify-network-fraud")
async def verify_network_fraud_endpoint(
    request: Request,
    user_id: str = Form(...),
    device_id: str = Form(...)
):
    ip, signals = build_network_features(
        request=request,
        device_id=device_id,
    )

    state = SessionState(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        current_step="Initializing network agent",
    )

    network_result = await run_network_agent(signals, state)

    append_login_history(
        user_id=user_id,
        ip=ip,
        device_id=device_id,
    )

    return {
        "status": 200,
        "session_id": state.session_id,
        "fraud_assessment": {
            "risk_score": network_result.risk,
            "confidence_score": network_result.confidence,
            "triggered_flags": state.flags,
            "reason": network_result.explanation,
        },
    }

router = APIRouter()
class LoginHourRequest(BaseModel):
    user_id: str
    hours: list[int] = [] 

@router.post("/check-login-hour")
async def login_hour_endpoint(user_id: str):
    return await login_hour_service(user_id, redis_client)

@app.post("/agentic-risk-assessment")
async def agentic_risk_assessment(
    identity: IdentityInput,
    behavioral: BehavioralInput,
    network: NetworkInput,
    user_id: str = Form(...),
):
    state = SessionState(session_id=str(uuid.uuid4()), user_id=user_id)
    
    identity_result = await run_identity_agent(identity, state)
    behavioral_result = await run_behavioral_agent(behavioral, state)
    network_result = await run_network_agent(network, state)

    meta_result = await run_orchestrator(identity_result, behavioral_result, network_result, state)

    final_result = await enforce_policy(meta_result, state)

    return {
        "user_id": user_id,
        "session_state": state.model_dump(),
        "final_decision": final_result.decision,
        "meta_result": final_result.model_dump(),
    }

@app.post("/human-review", response_model=HumanReviewResponse)
async def submit_human_review(body: HumanReviewInput):
    """
    Submit a human analyst's review for a REVIEW-flagged session.

    - If rating == GOOD: the AI decision was correct. Override decision = original decision.
    - If rating == BAD:  override_decision is required (APPROVE or REJECT).

    The review is stored in OrchestratorHistory and injected into future
    agent RAG context so the system learns from analyst corrections.
    """
    if body.rating == ReviewRating.BAD:
        if body.override_decision is None:
            raise HTTPException(
                status_code=422,
                detail="override_decision is required when rating is BAD"
            )
        applied_decision = body.override_decision.value
    else:
        # GOOD rating — analyst confirms the AI decision was correct
        # We still store the review but mark the override as the analyst's confirmation
        applied_decision = body.override_decision.value if body.override_decision else "CONFIRMED"

    # Build the override note with rating context
    override_note = f"[{body.rating.value}] {body.note}"

    try:
        result = await asyncio.to_thread(
            store_human_review,
            session_id=body.session_id,
            override_decision=applied_decision,
            override_note=override_note,
        )

        # Activate or deactivate the user based on the analyst's decision
        user_id = result.get("user_id")
        activation_message = ""
        if user_id and applied_decision in ("APPROVE", "REJECT"):
            try:
                if applied_decision == "APPROVE":
                    await asyncio.to_thread(activate_user, user_id)
                    activation_message = f" User {user_id} activated."
                elif applied_decision == "REJECT":
                    await asyncio.to_thread(deactivate_user, user_id)
                    activation_message = f" User {user_id} deactivated."
            except (ValueError, RuntimeError) as activation_err:
                activation_message = f" User activation failed: {activation_err}"

        return HumanReviewResponse(
            session_id=body.session_id,
            applied_decision=applied_decision,
            message=(
                f"Review stored. Original decision: {result['original_decision']}, "
                f"analyst override: {applied_decision}.{activation_message}"
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/human-review/pending")
async def get_pending_reviews():
    """
    List sessions flagged as REVIEW that have NOT yet been reviewed
    by a human analyst. Returns session details for the analyst dashboard.
    """
    pending = await asyncio.to_thread(fetch_pending_reviews, limit=20)
    return {
        "count": len(pending),
        "pending_reviews": pending,
    }