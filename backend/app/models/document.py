import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_hash = Column(String(64), nullable=False)
    page_count = Column(Integer, default=0)
    status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PROCESSING, COMPLETED, FAILED, REVIEW_REQUIRED
    is_scanned = Column(Boolean, default=False)
    error_message = Column(String(1000), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    statement = relationship("Statement", back_populates="document", uselist=False, cascade="all, delete-orphan")
