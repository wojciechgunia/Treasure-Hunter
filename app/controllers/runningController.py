from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import database, models
from app.entity.runningEntities import *
from app.services.authService import get_current_user
from app.services.missionService import get_mission

router = APIRouter(prefix="/runnings", tags=["Runnings"])

def update_runnings_count(db: Session, mission_id: int):
    count = db.query(models.Runnings).filter(models.Runnings.missionId == mission_id).count()
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if mission:
        mission.runningsNo = count
        mission.lastRunning = datetime.utcnow()
        db.commit()


@router.post("/", response_model=RunningResponse)
def create_running(request: RunningCreateRequest,
                   db: Session = Depends(database.get_db)):
    get_mission(models,db,request.missionId)

    running = models.Runnings(
        missionId=request.missionId,
        date=datetime.utcnow(),
        stats=request.stats
    )
    db.add(running)
    db.commit()
    db.refresh(running)

    update_runnings_count(db, request.missionId)

    return running


@router.get("/{mission_id}", response_model=List[RunningResponse])
def list_runnings(mission_id: int,
                  current_user: models.User = Depends(get_current_user),
                  db: Session = Depends(database.get_db)):
    get_mission(models,db,mission_id)

    runnings = db.query(models.Runnings).filter(models.Runnings.missionId == mission_id).all()
    return runnings


@router.get("/{mission_id}/last", response_model=RunningResponse)
def get_last_running(mission_id: int,
                     current_user: models.User = Depends(get_current_user),
                     db: Session = Depends(database.get_db)):
    get_mission(models,db,mission_id)

    running = (
        db.query(models.Runnings)
        .filter(models.Runnings.missionId == mission_id)
        .order_by(models.Runnings.date.desc())
        .first()
    )
    if not running:
        raise HTTPException(status_code=404, detail="No running's for this mission")

    return running
