from pydantic import BaseModel
from datetime import datetime

class POICreateRequest(BaseModel):
    missionId: int
    lat: str
    lon: str
    name: str | None = None
    description: str | None = None
    pictures: str | None = None  # lista URL w formie JSON stringa np. '["url1","url2"]'

class POIUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    pictures: str | None = None

class POIResponse(BaseModel):
    id: int
    missionId: int
    lat: str
    lon: str
    name: str | None
    description: str | None
    pictures: str | None
    createAt: datetime

    class Config:
        orm_mode = True