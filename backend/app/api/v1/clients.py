from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.client import Client
from app.models.bank_account import BankAccount
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, BankAccountCreate, BankAccountResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ClientResponse])
def list_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists all taxpayer clients managed by the CA organization."""
    clients = db.query(Client).filter(Client.org_id == current_user.org_id).order_by(Client.name).all()
    return clients

@router.post("/", response_model=ClientResponse)
def create_client(req: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Creates a new CA client profile."""
    client = Client(
        org_id=current_user.org_id,
        name=req.name,
        pan=req.pan.upper() if req.pan else None,
        gstin=req.gstin.upper() if req.gstin else None,
        email=req.email,
        phone=req.phone,
        notes=req.notes
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Gets client details with bank accounts."""
    client = db.query(Client).filter(Client.id == client_id, Client.org_id == current_user.org_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return client

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: str, req: ClientUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Updates client profile."""
    client = db.query(Client).filter(Client.id == client_id, Client.org_id == current_user.org_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    
    for field, val in req.dict(exclude_unset=True).items():
        setattr(client, field, val)

    db.commit()
    db.refresh(client)
    return client

@router.post("/{client_id}/bank-accounts", response_model=BankAccountResponse)
def add_bank_account(
    client_id: str,
    req: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Associates a bank account with a client."""
    client = db.query(Client).filter(Client.id == client_id, Client.org_id == current_user.org_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    acc = BankAccount(
        client_id=client.id,
        bank_name=req.bank_name,
        account_number_masked=req.account_number_masked,
        ifsc=req.ifsc,
        account_type=req.account_type or "Savings",
        branch=req.branch
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc
