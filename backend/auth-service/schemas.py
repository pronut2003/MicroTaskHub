from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str
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
