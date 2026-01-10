from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class DocumentType(str, enum.Enum):
    """Types of verification documents"""
    NATIONAL_ID = "NATIONAL_ID"
    CERTIFICATE = "CERTIFICATE"
    DIPLOMA = "DIPLOMA"
    LICENSE = "LICENSE"
    TRANSCRIPT = "TRANSCRIPT"


class VerificationStatus(str, enum.Enum):
    """Verification workflow states"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Verification(Base):
    """
    Verifications table - Document verification tracking.
    Implements the trust layer through OCR and validation.
    """
    __tablename__ = "verifications"
    
    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Document metadata
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    s3_url = Column(String(512), nullable=False)  # MinIO/S3 path
    file_size = Column(Integer, nullable=True)  # Bytes
    
    # OCR results
    ocr_data = Column(JSONB, nullable=True)  # Raw OCR output
    extracted_name = Column(String(255), nullable=True)
    extracted_serial = Column(String(100), nullable=True)
    extracted_skill = Column(String(255), nullable=True)
    extracted_institution = Column(String(255), nullable=True)
    
    # Verification workflow
    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False, index=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Trust impact
    trust_score_delta = Column(Integer, default=0)  # How much this adds to trust
    
    # Audit trail
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String(100), nullable=True)  # "SYSTEM" or admin user_id
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Verification {self.id} user={self.user_id} status={self.status.value}>"
