from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []
    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role_names: List[str]

class AuditLogBase(BaseModel):
    action: str
    details: Optional[str] = None
    timestamp: datetime
    user_id: int

class AuditLog(AuditLogBase):
    id: int
    class Config:
        from_attributes = True
