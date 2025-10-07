from fastapi import FastAPI

from app.controllers import authController, missionController, pointsOfInterestController, runningController, waypointController, boatsController

app = FastAPI()
app.include_router(authController.router)
app.include_router(missionController.router)
app.include_router(pointsOfInterestController.router)
app.include_router(runningController.router)
app.include_router(waypointController.router)
app.include_router(boatsController.router)


@app.get("/")
async def root():
    return {"message": "Hello from Boat API"}