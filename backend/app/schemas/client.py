from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class BankAccountCreate(BaseModel):
    bank_name: str
    account_number_masked: str
    ifsc: Optional[str] = None
    account_type: Optional[str] = "Savings"
    branch: Optional[str] = None

class BankAccountResponse(BankAccountCreate):
    id: str
    client_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientCreate):
    id: str
    org_id: str
    created_at: datetime
    bank_accounts: List[BankAccountResponse] = []

    class Config:
        from_attributes = True
