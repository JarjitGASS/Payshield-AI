import base64
from http import client

from openai import OpenAI
from fastapi import UploadFile
import os

def getClient():
    return OpenAI(
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
    )

def qwen_chat(system_prompt: str, user_prompt: str, model: str = "qwen-max"):
    client = getClient()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        top_p=0.8,
        max_tokens=512,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

async def qwen_file(system_prompt: str, user_prompt: str, file: UploadFile, model: str = "qwen3-vl-plus"):
    client = getClient()
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model=model,
        messages=[
            { "role": "system", "content": system_prompt },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
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