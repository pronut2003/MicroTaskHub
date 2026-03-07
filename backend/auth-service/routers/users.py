from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import databse as database
from databse import get_db
import models
import schemas
import auth
import rbac

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(rbac.get_current_user)):
    return current_user

@router.get("/", response_model=list[schemas.UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(rbac.verify_manager)
):
    query = db.query(models.User)
    
    user_roles = [r.name for r in current_user.roles_rel]
    if "Admin" not in user_roles and current_user.role != "Admin":
   
        query = query.filter(models.User.role != "Admin")
        
    return query.offset(skip).limit(limit).all()

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if not user.phone_no.isdigit():
        raise HTTPException(status_code=400, detail="Phone number must contain only digits")
    
    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_pw,
        full_name=user.full_name,
        phone_no=user.phone_no,
        role=user.role,
        department=user.department
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": db_user.email, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}