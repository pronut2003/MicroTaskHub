from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

import database
import models
import schemas
import auth

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[schemas.AuditEventResponse])
def get_audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: models.User = Depends(auth.require_role(["Admin"])),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.AuditEvent)

    if action:
        query = query.filter(models.AuditEvent.action == action)
    if user_id:
        query = query.filter(models.AuditEvent.user_id == user_id)

    query = query.order_by(models.AuditEvent.timestamp.desc())
    events = query.offset((page - 1) * page_size).limit(page_size).all()
    return events
