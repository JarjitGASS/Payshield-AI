from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from dotenv import load_dotenv
from services.check_id_card import check_id_card
from services.verivfy_id_card import verify_id_card
from services.verify_email_age_card import verify_email_age
from services.verify_geoip import check_geo_ip, get_real_ip

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:5173",
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

@app.post("/register")
async def register(
    nik: str = Form(...),
    fullname: str = Form(...),
    pob: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    file: UploadFile = File(...)
    # blm ada email
):
    return await check_id_card(file, nik, fullname, pob, dob, gender)

@app.post("/verify-id-card")
async def verify_id_card_endpoint(file: UploadFile = File(...)):
    return await verify_id_card(file)

@app.post("/verify-email-age")
async def verify_email_age_endpoint(email: str = Form()):
    return await verify_email_age(email)

@app.post("/verify-geo-ip")
async def verify_geo_ip_endpoint(
    request: Request,
    declared_country: str = Form(),
    declared_city: str = Form(None)
):

    ip = get_real_ip(request)

    return await check_geo_ip(ip, declared_country, declared_city)