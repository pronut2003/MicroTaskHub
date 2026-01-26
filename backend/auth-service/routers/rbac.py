from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import databse
import models
import rbac_schemas
import rbac

router = APIRouter(prefix="/rbac", tags=["rbac"])

@router.get("/roles", response_model=List[rbac_schemas.Role])
def list_roles(
    db: Session = Depends(databse.get_db),
    current_user: models.User = Depends(rbac.verify_admin)
):
    return db.query(models.Role).all()

@router.post("/roles", response_model=rbac_schemas.Role)
def create_role(
    role: rbac_schemas.RoleCreate,
    db: Session = Depends(databse.get_db),
    current_user: models.User = Depends(rbac.verify_admin)
):
    db_role = db.query(models.Role).filter(models.Role.name == role.name).first()
    if db_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    
    new_role = models.Role(name=role.name, description=role.description)
    db.add(new_role)
    
    # Audit Log
    rbac.log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_ROLE",
        details=f"Created role {role.name}"
    )
    
    db.refresh(new_role)
    return new_role

@router.post("/users/{user_id}/roles", response_model=List[rbac_schemas.Role])
def assign_roles_to_user(
    user_id: int,
    roles_update: rbac_schemas.UserRoleUpdate,
    db: Session = Depends(databse.get_db),
    current_user: models.User = Depends(rbac.verify_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get roles
    roles = db.query(models.Role).filter(models.Role.name.in_(roles_update.role_names)).all()
    if len(roles) != len(roles_update.role_names):
        raise HTTPException(status_code=400, detail="Some roles not found")
    
    user.roles_rel = roles
    
    # Update legacy role column to the first role for backward compatibility
    if roles:
        user.role = roles[0].name
    
    # Audit Log
    rbac.log_audit(
        db=db,
        user_id=current_user.id,
        action="ASSIGN_ROLES",
        details=f"Assigned roles {roles_update.role_names} to user {user.email}"
    )
    
    return user.roles_rel

@router.post("/initialize")
def initialize_rbac(db: Session = Depends(databse.get_db)):
    """Initialize default roles and permissions. Safe to run multiple times."""
    roles = ["User", "Manager", "Admin"]
    created_roles = []
    for role_name in roles:
        role = db.query(models.Role).filter(models.Role.name == role_name).first()
        if not role:
            role = models.Role(name=role_name, description=f"Default {role_name} role")
            db.add(role)
            created_roles.append(role_name)
    
    db.commit()
    return {"message": "RBAC initialized", "created_roles": created_roles}

@router.get("/audit", response_model=List[rbac_schemas.AuditLog])
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(databse.get_db),
    current_user: models.User = Depends(rbac.verify_admin)
):
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
