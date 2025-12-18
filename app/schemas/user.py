from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # bcrypt has a 72-byte limit
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
