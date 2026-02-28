from pydantic import BaseModel

class NetworkInput(BaseModel):
    shared_device_count: int
    shared_ip_count: int