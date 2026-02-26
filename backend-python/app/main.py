from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import json
import os
from dotenv import load_dotenv
from services.imageQwen import analyze_image

load_dotenv()

app = FastAPI()

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

    if input_gender in ["MALE", "L", "LAKI-LAKI"]:
        input_gender = "LAKI-LAKI"
    elif input_gender in ["FEMALE", "P", "PEREMPUAN"]:
        input_gender = "PEREMPUAN"

    if nik != qwen_nik:
        raise HTTPException(status_code=400, detail="NIK_MISMATCH")

    if input_name != qwen_name:
        raise HTTPException(status_code=400, detail="NAME_MISMATCH")

    if input_pob != qwen_pob:
        raise HTTPException(status_code=400, detail="POB_MISMATCH")

    if input_dob != qwen_dob:
        raise HTTPException(status_code=400, detail="DOB_MISMATCH")

    if input_gender != qwen_gender:
        raise HTTPException(status_code=400, detail="GENDER_MISMATCH")

    return {
        "success": True,
        "message": "IDENTITY VERIFIED",
        "fullname": fullname,
        "pob": pob,
        "dob": dob,
        "gender": gender,
        "qwen_result": qwen
    }