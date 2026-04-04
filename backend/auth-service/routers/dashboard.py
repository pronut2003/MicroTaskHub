from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Dict, Any
from datetime import datetime, timedelta
import database
import models
import rbac

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stats")
def get_task_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    """
    Get task counts grouped by status.
    """
    # Base query
    query = db.query(models.Task.status, func.count(models.Task.id))
    
    # Filter based on RBAC (Reuse logic from tasks.py roughly, or simplify)
    # Admin: All
    # Manager: Dept
    # User: Own
    
    user_roles = current_user.roles

    if "Admin" in user_roles:
        pass
    elif "Manager" in user_roles:
        if current_user.department:
            query = query.filter(models.Task.department == current_user.department)
        else:
            query = query.filter(models.Task.created_by_user_id == current_user.id)
    else:
        query = query.filter(models.Task.assigned_to_user_id == current_user.id)

    results = query.group_by(models.Task.status).all()
    
    stats = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "cancelled": 0
    }
    
    for status, count in results:
        key = status.value.lower()
        if key in stats:
            stats[key] = count
            
    return stats

@router.get("/tasks-time")
def get_time_tasks_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    """
    Get counts for Today, Week, Overdue
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_end = today_start + timedelta(days=7)
    
    # Base query logic
    base_query = db.query(models.Task)
    
    user_roles = current_user.roles

    if "Admin" in user_roles:
        pass
    elif "Manager" in user_roles:
        if current_user.department:
            base_query = base_query.filter(models.Task.department == current_user.department)
        else:
            base_query = base_query.filter(models.Task.created_by_user_id == current_user.id)
    else:
        base_query = base_query.filter(models.Task.assigned_to_user_id == current_user.id)
        
    due_today = base_query.filter(
        models.Task.due_date >= today_start,
        models.Task.due_date < today_end
    ).count()
    
    due_week = base_query.filter(
        models.Task.due_date >= today_start,
        models.Task.due_date < week_end
    ).count()
    
    overdue = base_query.filter(
        models.Task.due_date < now,
        models.Task.status != models.TaskStatus.COMPLETED
    ).count()
    
    return {
        "due_today": due_today,
        "due_week": due_week,
        "overdue": overdue
    }

@router.get("/activity")
def get_activity_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.get_current_user)
):
    """
    Get activity counts for the last N days
    """
    # Everyone sees their own activity? Or Managers see Dept?
    # Requirement: "Activity Summary Module" - let's show System Wide for Admin, Dept for Manager, Personal for User
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        func.date(models.AuditLog.timestamp).label('date'),
        func.count(models.AuditLog.id).label('count')
    ).filter(models.AuditLog.timestamp >= start_date)
    
    user_roles = current_user.roles

    if "Admin" in user_roles:
        pass
    elif "Manager" in user_roles:
        # Complex: Manager should see activities related to their dept users?
        # For simplicity/performance: Show only their own + explicit logs if we had dept_id in audit
        # Current AuditLog only has user_id.
        # Let's join with User
        query = query.join(models.User).filter(models.User.department == current_user.department)
    else:
        query = query.filter(models.AuditLog.user_id == current_user.id)
        
    results = query.group_by(func.date(models.AuditLog.timestamp)).all()
    
    # Format: { "2023-10-01": 5, ... }
    data = {}
    for r in results:
        # r.date might be a date object or string depending on driver
        d_str = str(r.date)
        data[d_str] = r.count
        
    return data

@router.get("/admin/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.verify_admin)
):
    """
    Admin specific stats: Active Users, System Activity, Error Rate
    """
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    
    # Total operations (last 30 days default?) or all time?
    # "within a specified time period" -> Let's say last 30 days
    last_30 = datetime.utcnow() - timedelta(days=30)
    
    total_ops = db.query(models.AuditLog).filter(models.AuditLog.timestamp >= last_30).count()
    
    error_ops = db.query(models.AuditLog).filter(
        models.AuditLog.timestamp >= last_30,
        models.AuditLog.status == models.AuditLogStatus.FAILURE
    ).count()
    
    error_rate = 0
    if total_ops > 0:
        error_rate = (error_ops / total_ops) * 100
        
    return {
        "active_users": active_users,
        "total_operations_30d": total_ops,
        "error_count_30d": error_ops,
        "error_rate": round(error_rate, 2)
    }
