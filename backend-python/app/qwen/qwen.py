from openai import OpenAI
import os

client = OpenAI(
    api_key = os.getenv("QWEN_API_KEY"),
    base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
)

def qwen_chat(system_prompt: str, user_prompt: str, model: str = "qwen-max"):
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