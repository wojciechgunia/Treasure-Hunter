from datetime import datetime
from pydantic import BaseModel

class RunningCreateRequest(BaseModel):
    missionId: int
    stats: str

class RunningResponse(BaseModel):
    id: int
    missionId: int
    date: datetime
    stats: str

    class Config:
        orm_mode = True