from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError
import auth
import models
import databse
from typing import List, Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(databse.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: models.User = Depends(get_current_user)):
        # Check new RBAC roles
        user_roles = [role.name for role in user.roles_rel]
        
        # Backward compatibility with string role
        if user.role and user.role not in user_roles:
            user_roles.append(user.role)
            
        if any(role in self.allowed_roles for role in user_roles):
            return user
            
        raise HTTPException(status_code=403, detail=f"Operation not permitted. Required roles: {self.allowed_roles}")

def verify_admin(user: models.User = Depends(get_current_user)):
    checker = RoleChecker(["Admin"])
    return checker(user)

def verify_manager(user: models.User = Depends(get_current_user)):
    checker = RoleChecker(["Admin", "Manager"])
    return checker(user)

def log_audit(
    db: Session, 
    user_id: int, 
    action: str, 
    details: str, 
    status: str = "success", 
    error_details: str = None
):
    """
    Helper to create an audit log entry.
    """
    log_entry = models.AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        status=models.AuditLogStatus(status),
        error_details=error_details
    )
    db.add(log_entry)
    db.commit()
