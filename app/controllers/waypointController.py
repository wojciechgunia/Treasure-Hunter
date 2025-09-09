from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import database, models
from app.entity.waypointEntities import *
from app.services.authService import get_current_user
from datetime import datetime

from app.services.missionService import get_mission

router = APIRouter(prefix="/waypoints", tags=["Waypoints"])

def update_waypoint_count(db: Session, mission_id: int):
    count = db.query(models.Waypoint).filter(models.Waypoint.missionId == mission_id).count()
    if count == 0:
        return
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if mission:
        mission.waypointsNo = count
        mission.lastRouteUpdate = datetime.utcnow()
        db.commit()

@router.post("/", response_model=WaypointResponse)
def create_waypoint(request: WaypointCreateRequest,
                    current_user: models.User = Depends(get_current_user),
                    db: Session = Depends(database.get_db)):
    get_mission(models,db,request.missionId)

    waypoint = models.Waypoint(
        missionId=request.missionId,
        no=request.no,
        lat=request.lat,
        lon=request.lon,
        lastUpdate=datetime.utcnow()
    )
    db.add(waypoint)
    db.commit()
    db.refresh(waypoint)

    update_waypoint_count(db, request.missionId)

    return waypoint

@router.get("/{mission_id}", response_model=List[WaypointResponse])
def list_waypoints(mission_id: int,
                   current_user: models.User = Depends(get_current_user),
                   db: Session = Depends(database.get_db)):
    get_mission(models,db,mission_id)

    waypoints = db.query(models.Waypoint).filter(models.Waypoint.missionId == mission_id).order_by(models.Waypoint.no).all()
    return waypoints

@router.put("/{waypoint_id}", response_model=WaypointResponse)
def update_waypoint(waypoint_id: int,
                    request: WaypointUpdateRequest,
                    current_user: models.User = Depends(get_current_user),
                    db: Session = Depends(database.get_db)):
    waypoint = db.query(models.Waypoint).filter(models.Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not exist")

    db.query(models.Mission).filter(models.Mission.id == waypoint.missionId).first()

    if request.no is not None:
        waypoint.no = request.no
    if request.lat is not None:
        waypoint.lat = request.lat
    if request.lon is not None:
        waypoint.lon = request.lon
    waypoint.lastUpdate = datetime.utcnow()

    db.commit()
    db.refresh(waypoint)

    return waypoint

@router.delete("/{waypoint_id}")
def delete_waypoint(waypoint_id: int,
                    current_user: models.User = Depends(get_current_user),
                    db: Session = Depends(database.get_db)):
    waypoint = db.query(models.Waypoint).filter(models.Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not exist")

    mission = db.query(models.Mission).filter(models.Mission.id == waypoint.missionId).first()

    db.delete(waypoint)
    db.commit()

    update_waypoint_count(db, mission.id)

    return {"detail": "Waypoint deleted"}
