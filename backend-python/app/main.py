from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from dotenv import load_dotenv
from services.imageQwen import analyze_image
from datetime import datetime

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
):
    result = await analyze_image(file)

    try:
        qwen = json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="INVALID_QWEN_JSON"
        )

    for field in ["name", "place_of_birth", "date_of_birth", "gender"]:
        if not qwen.get(field):
            raise HTTPException(
                status_code=400,
                detail=f"MISSING_{field.upper()}"
            )

    input_name = fullname.strip().upper()
    input_pob = pob.strip().upper()
    input_dob = dob.strip()
    input_gender = gender.strip().upper()

    qwen_name = qwen["name"].strip().upper()
    qwen_pob = qwen["place_of_birth"].strip().upper()
    qwen_dob = qwen["date_of_birth"].strip()
    qwen_gender = qwen["gender"].strip().upper()
    qwen_nik = qwen["nik"].strip()

    try:
        dob_obj = datetime.strptime(input_dob, "%Y-%m-%d")
        input_dob = dob_obj.strftime("%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="INVALID_DOB_FORMAT")

    if input_gender in ["MALE", "L", "LAKI-LAKI"]:
        input_gender = "LAKI-LAKI"
    elif input_gender in ["FEMALE", "P", "PEREMPUAN"]:
        input_gender = "PEREMPUAN"

    if nik != qwen_nik:
        raise HTTPException(status_code=400, detail={"message":"NIK_MISMATCH", "analysis": qwen})

    if input_name != qwen_name:
        raise HTTPException(status_code=400, detail={"message":"NAME_MISMATCH", "analysis": qwen})

    if input_pob != qwen_pob:
        raise HTTPException(status_code=400, detail={"message":"POB_MISMATCH", "analysis": qwen})

    if input_dob != qwen_dob:
        raise HTTPException(status_code=400, detail={"message":"DOB_MISMATCH", "analysis": qwen})

    if input_gender != qwen_gender:
        raise HTTPException(status_code=400, detail={"message":"GENDER_MISMATCH", "analysis": qwen})

    return {
        "success": True,
        "message": "IDENTITY VERIFIED",
        "nik": nik,
        "fullname": fullname,
        "pob": pob,
        "dob": dob,
        "gender": gender,
        "analysis": qwen
    }

