from fastapi import FastAPI

from app.controllers import authController

app = FastAPI()
app.include_router(authController.router)


@app.get("/")
async def root():
    return {"message": "Hello from Boat API"}