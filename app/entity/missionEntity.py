from pydantic import BaseModel

class MissionCreateRequest(BaseModel):
    name: str