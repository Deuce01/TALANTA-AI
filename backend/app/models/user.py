from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    CITIZEN = "CITIZEN"
    ADMIN = "ADMIN"
    EMPLOYER = "EMPLOYER"


class User(Base):
    """
    Users table - Core identity for TALANTA system.
    Implements progressive trust model with phone-first onboarding.
    """
    __tablename__ = "users"
    
    # Primary identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Progressive verification
    maisha_namba_hash = Column(String(64), nullable=True, unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Location (for job matching)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)  # e.g., "Kabete Ward"
    
    # Trust metrics
    trust_score = Column(Integer, default=0)  # 0-100
    
    # Role and status
    role = Column(SQLEnum(UserRole), default=UserRole.CITIZEN, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False)  # Has Maisha Namba
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.id} trust={self.trust_score}>"
