from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

import database
import models
import schemas
import auth
from middleware import log_audit_event

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUSES = ("todo", "in-progress", "done")
VALID_PRIORITIES = ("low", "medium", "high")
VALID_SORT_FIELDS = ("created_at", "due_date", "priority", "title", "status")


def task_to_response(task: models.Task, db: Session) -> schemas.TaskResponse:
    owner = db.query(models.User).filter(models.User.id == task.owner_id).first()
    resp = schemas.TaskResponse.model_validate(task)
    resp.owner_name = owner.full_name if owner else None
    return resp


@router.post("/", response_model=schemas.TaskResponse)
def create_task(
    task_data: schemas.TaskCreate,
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    if task_data.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    if task_data.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"Invalid priority. Must be one of: {VALID_PRIORITIES}")

    task = models.Task(
        owner_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    log_audit_event(db, "task.create", current_user.id, current_user.email, "task", task.id, task.title)
    return task_to_response(task, db)


@router.get("/", response_model=schemas.TaskListResponse)
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Task).filter(models.Task.is_deleted == False)

    # Role-based scoping
    if current_user.role == "User":
        query = query.filter(models.Task.owner_id == current_user.id)

    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)

    total = query.count()

    # Sorting
    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "created_at"
    sort_col = getattr(models.Task, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    task_responses = [task_to_response(t, db) for t in tasks]

    return schemas.TaskListResponse(tasks=task_responses, total=total, page=page, page_size=page_size)


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    task_id: int,
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.is_deleted == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role == "User" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")
    return task_to_response(task, db)


@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_data: schemas.TaskUpdate,
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.is_deleted == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role == "User" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")

    if task_data.status is not None and task_data.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    if task_data.priority is not None and task_data.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"Invalid priority. Must be one of: {VALID_PRIORITIES}")
    if task_data.owner_id is not None and current_user.role == "User":
        raise HTTPException(status_code=403, detail="Only Manager or Admin can reassign tasks")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    log_audit_event(db, "task.update", current_user.id, current_user.email, "task", task.id, task.title)
    return task_to_response(task, db)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_user: models.User = Depends(auth.get_current_user_from_db),
    db: Session = Depends(database.get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.is_deleted == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role == "User" and task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    task.is_deleted = True
    db.commit()

    log_audit_event(db, "task.delete", current_user.id, current_user.email, "task", task.id, task.title)
    return {"detail": "Task deleted"}
