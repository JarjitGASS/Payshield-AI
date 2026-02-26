from fastapi import HTTPException
from datetime import datetime, timezone
import whois


async def check_email_age(email: str):
    try:
        domain = email.split("@")[-1].strip().lower()

        w = whois.whois(domain)
        creation_date = w.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if not creation_date:
          return {
              "success": True,
              "email": email,
              "domain": domain,
              "email_age_days": None,
              "status": "unknown"
          }

        if creation_date.tzinfo is None:
            creation_date = creation_date.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        age_days = (now - creation_date).days

        return {
            "success": True,
            "email": email,
            "domain": domain,
            "email_age_days": age_days
        }

    except Exception as e:
      raise HTTPException(status_code=400, detail=str(e))
    
async def verify_email_age(email: str):
    result = await check_email_age(email)
    return result