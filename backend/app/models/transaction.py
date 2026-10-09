import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    statement_id = Column(String(36), ForeignKey("statements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    transaction_date = Column(Date, nullable=False, index=True)
    value_date = Column(Date, nullable=True)
    
    narration = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=False)  # Immutable raw source line
    
    reference_number = Column(String(100), nullable=True, index=True)
    cheque_number = Column(String(50), nullable=True, index=True)
    
    debit_amount = Column(Numeric(15, 2), default=0.00, nullable=False, index=True)
    credit_amount = Column(Numeric(15, 2), default=0.00, nullable=False, index=True)
    balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    payment_mode = Column(String(50), default="TRANSFER", nullable=False, index=True) # UPI, NEFT, RTGS, IMPS, CASH, CHEQUE, etc.
    category = Column(String(100), default="Miscellaneous", nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    
    counterparty = Column(String(255), nullable=True, index=True)
    upi_id = Column(String(255), nullable=True, index=True)
    
    source_page = Column(Integer, default=1, nullable=False)
    source_row = Column(Integer, default=0, nullable=False)
    
    confidence_score = Column(Numeric(4, 2), default=1.00, nullable=False)
    validation_status = Column(String(50), default="VALIDATED", nullable=False, index=True) # VALIDATED, REVIEW_REQUIRED, MANUAL_CORRECTED
    
    is_internal_transfer = Column(Boolean, default=False, nullable=False)
    is_potential_duplicate = Column(Boolean, default=False, nullable=False)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    statement = relationship("Statement", back_populates="transactions")
    review_items = relationship("ReviewItem", back_populates="transaction", cascade="all, delete-orphan")
