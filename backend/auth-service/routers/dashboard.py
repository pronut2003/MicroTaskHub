from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import database
import models
import schemas
import auth

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_task_stats(db: Session, owner_id: int = None) -> schemas.DashboardStats:
    query = db.query(models.Task).filter(models.Task.is_deleted == False)
    if owner_id is not None:
        query = query.filter(models.Task.owner_id == owner_id)

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_end = today_start + timedelta(days=7)

    return schemas.DashboardStats(
        todo_count=query.filter(models.Task.status == "todo").count(),
        in_progress_count=query.filter(models.Task.status == "in-progress").count(),
        done_count=query.filter(models.Task.status == "done").count(),
        overdue_count=query.filter(
            models.Task.due_date < now,
            models.Task.status != "done",
            models.Task.due_date.isnot(None),
        ).count(),
        due_today_count=query.filter(
            models.Task.due_date >= today_start,
            models.Task.due_date < today_end,
        ).count(),
        due_this_week_count=query.filter(
            models.Task.due_date >= today_start,
            models.Task.due_date < week_end,
        ).count(),
    )


@router.get("/", response_model=schemas.DashboardStats)
def get_dashboard(
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    owner_id = current_user.id if current_user.role == "User" else None
    return get_task_stats(db, owner_id)


@router.get("/admin", response_model=schemas.AdminDashboardStats)
def get_admin_dashboard(
    current_user: models.User = Depends(auth.require_role(["Admin"])),
    db: Session = Depends(database.get_db),
):
    stats = get_task_stats(db)
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    return schemas.AdminDashboardStats(
        **stats.model_dump(),
        total_users=db.query(models.User).count(),
        active_users=db.query(models.User).filter(models.User.is_active == True).count(),
        total_tasks=db.query(models.Task).filter(models.Task.is_deleted == False).count(),
        recent_activity_count=db.query(models.AuditEvent).filter(
            models.AuditEvent.timestamp >= day_ago
        ).count(),
    )
