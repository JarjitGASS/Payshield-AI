from pydantic import BaseModel

class NetworkInput(BaseModel):
    shared_phone_count: int
    shared_device_count: int
    shared_ip_count: int
    account_age_hours: float
    cross_merchant_reuse: bool