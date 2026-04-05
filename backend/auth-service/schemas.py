from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone_no: str = Field(..., min_length=10, max_length=20)
    role: str = Field(default="User", max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone_no: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserRoleUpdate(BaseModel):
    role: str


class UserStatusUpdate(BaseModel):
    is_active: bool


# Task schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field(default="todo")
    priority: str = Field(default="medium")
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    owner_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    owner_id: int
    owner_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


# Dashboard schemas
class DashboardStats(BaseModel):
    todo_count: int = 0
    in_progress_count: int = 0
    done_count: int = 0
    overdue_count: int = 0
    due_today_count: int = 0
    due_this_week_count: int = 0


class AdminDashboardStats(DashboardStats):
    total_users: int = 0
    active_users: int = 0
    total_tasks: int = 0
    recent_activity_count: int = 0


# Audit schemas
class AuditEventResponse(BaseModel):
    id: int
    correlation_id: str
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    detail: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
