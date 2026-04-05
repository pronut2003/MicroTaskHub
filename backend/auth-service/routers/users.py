from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import database
import models
import schemas
import auth
from middleware import log_audit_event

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

    log_audit_event(db, "auth.register", new_user.id, new_user.email, "user", new_user.id)
    return new_user


@router.post("/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        log_audit_event(db, "auth.login_fail", user_email=user.email, detail="Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"sub": db_user.email, "role": db_user.role})
    log_audit_event(db, "auth.login", db_user.id, db_user.email, "user", db_user.id)
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserResponse.model_validate(db_user),
    )


@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_profile(
    current_user: models.User = Depends(auth.get_current_user_from_db),
):
    return current_user


@router.get("/", response_model=List[schemas.UserResponse])
def get_users(
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    return db.query(models.User).all()


@router.put("/{user_id}/role", response_model=schemas.UserResponse)
def update_user_role(
    user_id: int,
    role_update: schemas.UserRoleUpdate,
    current_user: models.User = Depends(auth.require_role(["Admin"])),
    db: Session = Depends(database.get_db),
):
    if role_update.role not in ("User", "Manager", "Admin"):
        raise HTTPException(status_code=422, detail="Role must be User, Manager, or Admin")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = role_update.role
    db.commit()
    db.refresh(user)

    log_audit_event(
        db, "user.role_change", current_user.id, current_user.email,
        "user", user.id, f"{old_role} -> {role_update.role}",
    )
    return user


@router.put("/{user_id}/status", response_model=schemas.UserResponse)
def update_user_status(
    user_id: int,
    status_update: schemas.UserStatusUpdate,
    current_user: models.User = Depends(auth.require_role(["Admin"])),
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = status_update.is_active
    db.commit()
    db.refresh(user)

    action = "user.activate" if status_update.is_active else "user.deactivate"
    log_audit_event(db, action, current_user.id, current_user.email, "user", user.id)
    return user
