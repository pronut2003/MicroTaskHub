from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
import databse

class User(databse.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_no = Column(String(20), nullable=False)
    role = Column(String(50), default="User") 
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
