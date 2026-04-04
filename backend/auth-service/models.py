from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import database
import enum

# Association tables
# Legacy tables preserved for reference/migration safety
user_roles = Table('user_roles', database.Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('assigned_at', DateTime, default=datetime.utcnow)
)

role_permissions_legacy = Table('role_permissions_legacy', database.Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id'))
)

# New RBAC Junction Table
class RolePermission(database.Base):
    __tablename__ = "role_permissions"
    role = Column(Enum('user', 'manager', 'admin'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.permission_id'), primary_key=True)

class RoleName(str, enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    USER = "User"

class UserRole(str, enum.Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"

class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class AuditLogStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class Department(database.Base):
    __tablename__ = "departments"
    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="department_obj")

class Role(database.Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy relationships
    permissions = relationship("Permission", secondary=role_permissions_legacy, backref="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles_rel")

class Permission(database.Base):
    __tablename__ = "permissions"
    id = Column("permission_id", Integer, primary_key=True, index=True)
    name = Column("permission_name", String(50), unique=True, index=True, nullable=False)
    description = Column(Text)

class AuditLog(database.Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(255), nullable=False)
    details = Column(String(255))
    status = Column(Enum(AuditLogStatus, values_callable=lambda x: [e.value for e in x]), default=AuditLogStatus.SUCCESS)
    error_details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    
    user = relationship("User", backref="audit_logs")

class Task(database.Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]), default=TaskStatus.PENDING)
    due_date = Column(DateTime, nullable=True)
    department = Column(String(100), nullable=True, index=True) # Kept for legacy/fallback
    
    created_by_id = Column(Integer, nullable=True) # Legacy
    assigned_to_id = Column(Integer, nullable=True) # Legacy
    
    # New Fields
    is_deleted = Column(Integer, default=0) # Soft delete (0=Active, 1=Deleted)
    created_by_user_id = Column(Integer, ForeignKey('users.id'))
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    creator = relationship("User", foreign_keys=[created_by_user_id], backref="created_tasks_new")
    assignee = relationship("User", foreign_keys=[assigned_to_user_id], backref="assigned_tasks_new")

class User(database.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_no = Column(String(20), nullable=False)
    
    # New Role Enum
    role = Column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.USER)
    
    # Department
    department_id = Column(Integer, ForeignKey('departments.department_id'), nullable=True)
    department = Column(String(100), nullable=True) # Legacy string
    
    department_obj = relationship("Department", back_populates="users")
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles_rel = relationship("Role", secondary=user_roles, back_populates="users")

    @property
    def roles(self):
        # Compatibility: Return list of role names based on Enum
        # Convert "user" -> "User", "admin" -> "Admin" to match legacy RoleChecker expectations
        if self.role:
            return [self.role.value.capitalize()]
        return ["User"]
