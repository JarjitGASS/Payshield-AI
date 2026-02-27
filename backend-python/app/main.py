from webbrowser import get

import database.redis_client
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
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
from services.navigation_consistency_score import store_click_position
from dtos.auth_input import LoginRequest
from dtos.auth_result import LoginResponse
from database.database import SessionLocal
import model, database.database
from services.network_fraud import evaluate_network_fraud_service
from datetime import datetime, timedelta, timezone

load_dotenv()
database.database.Base.metadata.create_all(bind=database.database.engine)

app = FastAPI()

# db sementara buat simpen data login
login_history = []

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/auth/login")
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
    return {"status": "ok", "user_id": user_id}

@app.post("/verify-network-fraud")
async def verify_network_fraud_endpoint(
    request: Request,
    user_id: str = Form(...),
    device_id: str = Form(...)
):
    return await evaluate_network_fraud_service(
        request=request,
        user_id=user_id,
        device_id=device_id,
        login_history=login_history
    )