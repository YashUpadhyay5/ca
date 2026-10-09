from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class OrgCreate(BaseModel):
    name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None

class OrgResponse(BaseModel):
    id: str
    name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "CA"
    org_name: Optional[str] = "Chartered Accountants Firm"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    org_id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
