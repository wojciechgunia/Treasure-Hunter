from fastapi import HTTPException

def get_mission(models,db,mission_id):
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not exist")
    return mission