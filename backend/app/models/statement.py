import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Statement(Base):
    __tablename__ = "statements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    bank_account_id = Column(String(36), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    bank_name = Column(String(100), default="Generic Indian Bank", nullable=False)
    account_number_detected = Column(String(50), nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    opening_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    closing_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    calculated_closing_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    balance_discrepancy = Column(Numeric(15, 2), default=0.00, nullable=False)
    reconciliation_status = Column(String(50), default="UNVERIFIED", nullable=False)  # RECONCILED, DISCREPANCY_DETECTED, UNVERIFIED
    total_transactions = Column(Integer, default=0, nullable=False)
    total_credits = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_debits = Column(Numeric(15, 2), default=0.00, nullable=False)
    net_movement = Column(Numeric(15, 2), default=0.00, nullable=False)
    parser_used = Column(String(50), default="GENERIC", nullable=False)
    confidence_avg = Column(Numeric(5, 2), default=1.00, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="statement")
    bank_account = relationship("BankAccount", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan", order_by="Transaction.transaction_date")
