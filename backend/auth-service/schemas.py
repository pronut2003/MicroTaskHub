from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models import TaskPriority, TaskStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(..., min_length=1, max_length=255)
    phone_no: str = Field(..., min_length=10, max_length=20)
    role: str = Field(default="User", max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone_no: str
    role: str
    department: Optional[str]
    roles: list[str] = []
    is_active: bool

    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    department: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    department: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    creator: UserResponse
    assignee: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class TaskPaginationResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    size: int
    pages: int

