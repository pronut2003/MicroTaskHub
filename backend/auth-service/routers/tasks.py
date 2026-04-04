import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from typing import List, Optional
from datetime import datetime
import database
import models
import schemas
import rbac

from database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])

def check_task_permission(task: models.Task, user: models.User, action: str):
    user_roles = user.roles

    if "Admin" in user_roles:
        return True

    if action == "read":
        if "Manager" in user_roles:
            if task.department and task.department == user.department:
                return True
        if task.created_by_user_id == user.id or task.assigned_to_user_id == user.id:
            return True

    elif action == "update":
        if "Manager" in user_roles:
            if task.department and task.department == user.department:
                return True
        if task.created_by_user_id == user.id or task.assigned_to_user_id == user.id:
            return True

    elif action == "delete":
        if task.created_by_user_id == user.id:
            return True

    return False

def log_audit(db: Session, user_id: int, action: str, details: str):
    log = models.AuditLog(
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(log)
    db.commit()

@router.post("/", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    if task.due_date and task.due_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Due date must be in the future")
        
    
    department = task.department
    if not department and current_user.department:
        department = current_user.department
        
    new_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=models.TaskStatus.PENDING,
        due_date=task.due_date,
        department=department,
        created_by_user_id=current_user.id,
        assigned_to_user_id=task.assigned_to_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    log_audit(db, current_user.id, "CREATE_TASK", f"Created task {new_task.id}: {new_task.title}")
    return new_task

@router.get("/", response_model=schemas.TaskPaginationResponse)
def list_tasks(
    skip: int = 0,
    limit: int = 20,
    status: Optional[models.TaskStatus] = None,
    priority: Optional[models.TaskPriority] = None,
    assigned_to_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    query = db.query(models.Task).filter(models.Task.deleted_at.is_(None))
    

    user_roles = current_user.roles

    if "Admin" in user_roles:
        pass
    elif "Manager" in user_roles:
        conditions = [
            models.Task.created_by_user_id == current_user.id,
            models.Task.assigned_to_user_id == current_user.id
        ]
        if current_user.department:
            conditions.append(models.Task.department == current_user.department)
        query = query.filter(or_(*conditions))
    else:
        query = query.filter(or_(
            models.Task.created_by_user_id == current_user.id,
            models.Task.assigned_to_user_id == current_user.id
        ))
        

    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if assigned_to_id:
        query = query.filter(models.Task.assigned_to_id == assigned_to_id)
    if from_date:
        query = query.filter(models.Task.due_date >= from_date)
    if to_date:
        query = query.filter(models.Task.due_date <= to_date)
        
   
    total = query.count()
        
    if sort_desc:
        query = query.order_by(desc(getattr(models.Task, sort_by, models.Task.created_at)))
    else:
        query = query.order_by(asc(getattr(models.Task, sort_by, models.Task.created_at)))
        
    items = query.offset(skip).limit(limit).all()
    
    pages = math.ceil(total / limit) if limit > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": limit,
        "pages": pages
    }

@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if not check_task_permission(task, current_user, "read"):
        raise HTTPException(status_code=403, detail="Not authorized to view this task")
        
    return task

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if not check_task_permission(task, current_user, "update"):
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
        
    # Status transition validation
    if task_update.status:
        if task.status == models.TaskStatus.COMPLETED and task_update.status == models.TaskStatus.PENDING:
             raise HTTPException(status_code=400, detail="Cannot revert completed task to pending")
             
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
        
    db.commit()
    db.refresh(task)
    
    log_audit(db, current_user.id, "UPDATE_TASK", f"Updated task {task.id}. Fields: {list(update_data.keys())}")
    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if not check_task_permission(task, current_user, "delete"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
        
    task.deleted_at = datetime.utcnow()
    db.commit()
    
    log_audit(db, current_user.id, "DELETE_TASK", f"Deleted task {task.id}")
    return {"message": "Task deleted successfully"}
