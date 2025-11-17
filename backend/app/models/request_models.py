# request_models.py
from pydantic import BaseModel

class DeployRequest(BaseModel):
    device_id: str
    instance_name: str
    user: str
