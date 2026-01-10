from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.schema import Index
from datetime import datetime
import uuid

from app.database import Base


class AuditLog(Base):
    """
    Immutable audit log for government accountability.
    Tracks all state changes and critical operations.
    
    CRITICAL: This table is append-only. No updates or deletes allowed.
    """
    __tablename__ = "audit_logs"
    
    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Actor
    user_id = Column(String(100), nullable=False, index=True)  # Who performed action
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., "SKILL_VERIFIED"
    entity_type = Column(String(50), nullable=False)  # e.g., "User", "Verification"
    entity_id = Column(String(100), nullable=False, index=True)
    
    # State change
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    
    # Additional context
    metadata = Column(JSONB, nullable=True)
    
    # Timestamp (immutable)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id} at {self.timestamp}>"
