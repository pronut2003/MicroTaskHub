from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import database
import models
import schemas
import auth

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if not user.phone_no.isdigit():
        raise HTTPException(status_code=400, detail="Phone number must contain only digits")

    new_user = models.User(
        email=user.email,
        password_hash=auth.hash_password(user.password),
        full_name=user.full_name,
        phone_no=user.phone_no,
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"sub": db_user.email, "role": db_user.role})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserResponse.model_validate(db_user),
    )


@router.get("/", response_model=List[schemas.UserResponse])
def get_users(
    current_user: dict = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    return db.query(models.User).all()
