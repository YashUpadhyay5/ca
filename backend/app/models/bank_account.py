import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False)
    account_number_masked = Column(String(50), nullable=False)
    ifsc = Column(String(20), nullable=True)
    account_type = Column(String(50), default="Savings")  # Savings, Current, OD, CC
    branch = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="bank_accounts")
    statements = relationship("Statement", back_populates="bank_account", cascade="all, delete-orphan")
