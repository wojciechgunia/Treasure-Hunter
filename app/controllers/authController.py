from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, database
from app.entity.authModels import LoginRequest
from app.services.authService import authenticate_user, create_access_token, get_current_user, get_password_hash

router = APIRouter(prefix="/auth", tags=["user"])

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=400, detail="Błędny login lub hasło")
    if user.isBlocked:
        raise HTTPException(status_code=400, detail="Użytkownik jest zablokowany")
    access_token = create_access_token(data={"sub": user.login})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "login": current_user.login,
        "role": current_user.role,
        "isBlocked": current_user.isBlocked,
        "createdAt": current_user.createAt.isoformat()
    }

@router.get("/userList", response_model=List[str])
def list_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    return [u.login for u in users]


@router.post("/change-password")
def change_password(
    new_password: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    hashed = get_password_hash(new_password)
    current_user.password = hashed
    db.commit()
    return {"msg": "Hasło zmienione"}
