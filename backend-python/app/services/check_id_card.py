from qwen.qwen import qwen_file
from fastapi import HTTPException
import json
from datetime import datetime


async def check_id_card(file, nik: str, fullname: str, pob: str, dob: str, gender: str):
  prompt = """
  You are an OCR and identity extraction system.

  Analyze the provided Indonesian ID card (KTP) image.

  Extract the following fields ONLY if they are clearly visible:
  - nik
  - name
  - gender
  - place_of_birth
  - date_of_birth

  Rules:
  1. Use the exact field names listed above.
  2. Return output in valid JSON only.
  3. Do NOT include explanations, comments, or extra text.
  4. If a field is not visible or unreadable, return null.
  5. The date_of_birth on the ID card is written in DD-MM-YYYY format.
  6. Use DD-MM-YYYY format for date_of_birth in the output as well.
  7. Gender must be either "LAKI-LAKI" or "PEREMPUAN".
  8. NIK must be numeric without spaces.

  Output format:
  {
    "nik": string | null,
    "name": string | null,
    "gender": "LAKI-LAKI" | "PEREMPUAN" | null,
    "place_of_birth": string | null,
    "date_of_birth": string | null
  }
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
  
  for field in ["name", "place_of_birth", "date_of_birth", "gender"]:
    if not qwen.get(field):
      raise HTTPException(status_code=400, detail=f"MISSING_{field.upper()}")

  qwen_name = qwen["name"].strip().upper()
  qwen_pob = qwen["place_of_birth"].strip().upper()
  qwen_dob = qwen["date_of_birth"].strip()
  qwen_gender = qwen["gender"].strip().upper()
  qwen_nik = qwen.get("nik")
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
