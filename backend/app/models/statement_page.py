import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class BankStatementPage(Base):
    __tablename__ = "bank_statement_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    statement_id = Column(String(36), ForeignKey("statements.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    page_status = Column(String(50), default="PROCESSED", nullable=False)
    char_count = Column(Integer, default=0, nullable=False)
    table_detected = Column(Boolean, default=False, nullable=False)
    extraction_time_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    statement = relationship("Statement", backref="pages")
