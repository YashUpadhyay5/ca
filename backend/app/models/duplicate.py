import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    statement_id = Column(String(36), ForeignKey("statements.id", ondelete="CASCADE"), nullable=False, index=True)
    primary_txn_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_txn_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity_score = Column(Numeric(5, 2), default=1.00, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    statement = relationship("Statement", backref="duplicates")
    primary_txn = relationship("Transaction", foreign_keys=[primary_txn_id])
    candidate_txn = relationship("Transaction", foreign_keys=[candidate_txn_id])
