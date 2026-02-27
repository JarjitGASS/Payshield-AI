from qwen.qwen import qwen_file
from fastapi import HTTPException, UploadFile
import json
from datetime import datetime


async def check_id_card(file: UploadFile, nik: str, fullname: str, pob: str, dob: str, gender: str):
  prompt = """
You are an OCR, identity extraction, and identity verification system.
You must follow instructions strictly.

Analyze the provided image of a person holding an Indonesian ID card (KTP).

==================================================
OUTPUT RULES (CRITICAL)
==================================================
1. Return ONE valid JSON object only.
2. Do NOT include explanations, comments, markdown, or extra text outside JSON.
3. Do NOT guess or infer information that is not clearly visible.
4. If uncertain, use null or conservative values as specified.
5. All fields defined below MUST exist in the output.

==================================================
TASKS
==================================================

A. OCR & DATA EXTRACTION  
Extract the following fields ONLY if clearly visible on the ID card:
- nik
- name
- gender
- place_of_birth
- date_of_birth

OCR RULES:
- nik: numeric only, no spaces
- gender: "LAKI-LAKI" or "PEREMPUAN"
- date_of_birth format: DD-MM-YYYY
- If unreadable or missing: null

B. IDENTITY VERIFICATION  
Using the SAME image:
1. Identify issuing country and document type
2. Compare the face on the card with the person holding it
3. Check authenticity indicators (hologram, fonts, layout, physical card)
4. Assess text legibility
5. Assess whether the image appears AI-generated or digitally manipulated

VERIFICATION RULES:
- Do NOT assume authenticity
- If evidence is insufficient, choose conservative values

==================================================
FINAL JSON OUTPUT SCHEMA
==================================================

{
  "ocr_result": {
    "nik": string | null,
    "name": string | null,
    "gender": "LAKI-LAKI" | "PEREMPUAN" | null,
    "place_of_birth": string | null,
    "date_of_birth": string | null
  },
  "verification_result": {
    "generated_by_ai": "YES" | "NO" | "UNCLEAR",
    "country": string | null,
    "document_type": string | null,
    "face_match": "MATCH" | "MISMATCH" | "INCONCLUSIVE",
    "card_authenticity": "AUTHENTIC" | "SUSPICIOUS" | "INCONCLUSIVE",
    "text_legibility": "CLEAR" | "PARTIAL" | "UNREADABLE",
    "confidence_score": number,
    "reasoning": string
  }
}

FINAL CONSTRAINTS:
- confidence_score must be between 0 and 100
- reasoning must be brief, factual, and based only on visible evidence
- Output EXACTLY one JSON object matching the schema above
  """
  system = """
  Analyze the ID card image and extract the required fields.
  """

  input_name = fullname.strip().upper()
  input_pob = pob.strip().upper()
  input_dob = dob.strip()
  input_gender = gender.strip().upper()

  try:
    dob_obj = datetime.strptime(input_dob, "%Y-%m-%d")
    input_dob = dob_obj.strftime("%d-%m-%Y")
  except ValueError:
    raise HTTPException(status_code=400, detail="INVALID_DOB_FORMAT")

  result = await qwen_file(prompt, system, file)

  try:
    qwen = json.loads(result)
  except json.JSONDecodeError:
    raise HTTPException(status_code=400, detail="INVALID_QWEN_JSON")
  
  ocr_result = qwen.get("ocr_result")
  for field in ["name", "place_of_birth", "date_of_birth", "gender"]:
    if not ocr_result.get(field):
      raise HTTPException(status_code=400, detail=f"MISSING_{field.upper()}")

  qwen_name = ocr_result["name"].strip().upper()
  qwen_pob = ocr_result["place_of_birth"].strip().upper()
  qwen_dob = ocr_result["date_of_birth"].strip()
  qwen_gender = ocr_result["gender"].strip().upper()
  qwen_nik = ocr_result.get("nik")
  qwen_nik = qwen_nik.strip() if isinstance(qwen_nik, str) else qwen_nik

  if input_gender in ["MALE", "L", "LAKI-LAKI"]:
    input_gender = "LAKI-LAKI"
  elif input_gender in ["FEMALE", "P", "PEREMPUAN"]:
    input_gender = "PEREMPUAN"

  if nik != qwen_nik:
    raise HTTPException(status_code=400, detail={"message": "NIK_MISMATCH", "analysis": qwen})

  if input_name != qwen_name:
    raise HTTPException(status_code=400, detail={"message": "NAME_MISMATCH", "analysis": qwen})

  if input_pob != qwen_pob:
    raise HTTPException(status_code=400, detail={"message": "POB_MISMATCH", "analysis": qwen})

  if input_dob != qwen_dob:
    raise HTTPException(status_code=400, detail={"message": "DOB_MISMATCH", "analysis": qwen})

  if input_gender != qwen_gender:
    raise HTTPException(status_code=400, detail={"message": "GENDER_MISMATCH", "analysis": qwen})

  return {
    "success": True,
    "message": "IDENTITY VERIFIED",
    "nik": nik,
    "fullname": fullname,
    "pob": pob,
    "dob": dob,
    "gender": gender,
    "analysis": qwen,
  }
