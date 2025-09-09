from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import database, models
from app.entity.pointsOfInterestEntities import *
from app.services.authService import get_current_user
from app.services.missionService import get_mission

router = APIRouter(prefix="/pois", tags=["Points of Interest"])

def update_poi_count(db: Session, mission_id: int):
    count = db.query(models.PointsOfInterest).filter(models.PointsOfInterest.missionId == mission_id).count()
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if mission:
        mission.pointsOfInterestsNo = count
        db.commit()

@router.post("/", response_model=POIResponse)
def create_poi(request: POICreateRequest,
               current_user: models.User = Depends(get_current_user),
               db: Session = Depends(database.get_db)):
    get_mission(models,db,request.missionId)
    poi = models.PointsOfInterest(
        missionId=request.missionId,
        lat=request.lat,
        lon=request.lon,
        name=request.name,
        description=request.description,
        pictures=request.pictures,
        createAt=datetime.utcnow()
    )
    db.add(poi)
    db.commit()
    db.refresh(poi)

    update_poi_count(db, request.missionId)

    return poi

@router.get("/{mission_id}", response_model=List[POIResponse])
def list_pois(mission_id: int,
              current_user: models.User = Depends(get_current_user),
              db: Session = Depends(database.get_db)):


    pois = db.query(models.PointsOfInterest).filter(models.PointsOfInterest.missionId == mission_id).all()
    return pois

@router.put("/{poi_id}", response_model=POIResponse)
def update_poi(poi_id: int,
               request: POIUpdateRequest,
               current_user: models.User = Depends(get_current_user),
               db: Session = Depends(database.get_db)):
    poi = db.query(models.PointsOfInterest).filter(models.PointsOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not exist")

    get_mission(models,db,poi.missionId)

    if request.name is not None:
        poi.name = request.name
    if request.description is not None:
        poi.description = request.description
    if request.pictures is not None:
        poi.pictures = request.pictures

    db.commit()
    db.refresh(poi)

    return poi

@router.delete("/{poi_id}")
def delete_poi(poi_id: int,
               current_user: models.User = Depends(get_current_user),
               db: Session = Depends(database.get_db)):
    poi = db.query(models.PointsOfInterest).filter(models.PointsOfInterest.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not exist")

    mission = get_mission(models,db,poi.missionId)

    db.delete(poi)
    db.commit()

    update_poi_count(db, mission.id)

    return {"detail": "POI deleted"}
