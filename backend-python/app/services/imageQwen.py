from openai import OpenAI
import os
import base64

def get_client():
    return OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

async def analyze_image(file):
    client = get_client()
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
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

    response = client.chat.completions.create(
        model="qwen3-vl-plus",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content