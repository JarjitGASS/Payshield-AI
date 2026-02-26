from pydantic import BaseModel

class IdentityInput(BaseModel):
    ktp_match_score: float
    face_similarity_score: float
    email_age_days: int
    geo_ip_mismatch: bool
    name_entropy: float
    entity_sentiment_score: float
