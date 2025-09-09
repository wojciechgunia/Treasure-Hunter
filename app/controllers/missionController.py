from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import database, models
from app.entity.missionEntity import MissionCreateRequest
from app.services.authService import get_current_user
from datetime import datetime

from app.services.missionService import get_mission

router = APIRouter(prefix="/missions", tags=["Missions"])

@router.post("/")
def create_mission(request: MissionCreateRequest,
                   current_user: models.User = Depends(get_current_user),
                   db: Session = Depends(database.get_db)):
    mission = models.Mission(
        name=request.name,
        userId=current_user.id,
        createdAt=datetime.utcnow(),
        lastRouteUpdate=None,
        lastRunning=None,
        waypointsNo=0,
        pointsOfInterestsNo=0,
        runningsNo=0
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return {"id": mission.id, "name": mission.name}

@router.get("/{mission_id}")
def mission_data(mission_id: int,
                 current_user: models.User = Depends(get_current_user),
                 db: Session = Depends(database.get_db)):
    mission = get_mission(models,db,mission_id)
    return mission

@router.get("/")
def list_missions(db: Session = Depends(database.get_db)):
    missions = db.query(models.Mission).all()
    return [{"id": m.id, "name": m.name} for m in missions]

@router.delete("/{mission_id}")
def delete_mission(mission_id: int,
                   current_user: models.User = Depends(get_current_user),
                   db: Session = Depends(database.get_db)):
    mission = get_mission(models,db,mission_id)
    db.delete(mission)
    db.commit()
    return {"detail": "Mission deleted"}
