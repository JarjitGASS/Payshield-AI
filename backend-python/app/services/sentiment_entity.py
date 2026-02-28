import json
import re
from fastapi import Form, HTTPException
from qwen.qwen import qwen_chat

async def analyze_company_sentiment(company_name: str):
    system = """
    You are a Corporate Risk Analyst. You must respond ONLY with a valid JSON object. 
    Do not include markdown code blocks (like ```json), no preamble, and no conversational text.
    """

    prompt = f"""
    Perform a sentiment and risk analysis for the company: "{company_name}".
    
    Required JSON Schema:
    {{
      "entity_name": "string",
      "overall_sentiment": "Positive/Negative/Neutral",
      "risk_level": "Low/Medium/High",
      "sentiment_score": integer (0-100),
      "is_good_company": boolean,
      "reasoning": "string",
      "legitimacy": "string"
    }}
    
    Analysis Guide:
    - If the company has fraud reports or bad debt history, set is_good_company to false.
    - If the company is unknown, provide a neutral score of 50.
    - For "legitimacy", evaluate their operational footprint and categorize as:
        1. "Established" (Recognized business, clear product/service, visible digital footprint)
        2. "Suspicious" (Shell company traits, unregulated, hidden ownership, or scam warnings)
        3. "Unknown" (Cannot find sufficient public data to verify existence)
    """

    raw_response = qwen_chat(prompt, system)
    
    try:
        clean_json = re.sub(r'^```json\s*|```$', '', raw_response.strip(), flags=re.MULTILINE)
        return json.loads(clean_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response was not in valid JSON format.")