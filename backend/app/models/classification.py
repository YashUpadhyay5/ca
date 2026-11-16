import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class TransactionClassification(Base):
    __tablename__ = "transaction_classifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_category = Column(String(100), nullable=False, index=True)
    confidence = Column(Numeric(5, 2), default=1.00, nullable=False)
    model_version = Column(String(50), default="v1.0-rules-tfidf", nullable=False)
    feature_keywords = Column(Text, nullable=True)
    is_reviewed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    transaction = relationship("Transaction", backref="classification_records")
