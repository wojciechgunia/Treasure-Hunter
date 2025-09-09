from datetime import datetime
from pydantic import BaseModel

class WaypointCreateRequest(BaseModel):
    missionId: int
    no: int
    lat: str
    lon: str

class WaypointUpdateRequest(BaseModel):
    no: int | None = None
    lat: str | None = None
    lon: str | None = None

class WaypointResponse(BaseModel):
    id: int
    missionId: int
    no: int
    lat: str
    lon: str
    lastUpdate: datetime

    class Config:
        orm_mode = True