from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

from app.database import Base


class Job(Base):
    """
    Jobs table - Market intelligence on available opportunities.
    Populated by scraping and manual entry.
    """
    __tablename__ = "jobs"
    
    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job details
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    
    # Requirements
    required_skills = Column(JSONB, nullable=False)  # List of skill names
    experience_years = Column(Integer, nullable=True)
    education_level = Column(String(100), nullable=True)
    
    # Compensation
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(3), default="KES")
    
    # Location
    location = Column(String(255), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    is_remote = Column(String(20), default="NO")  # YES, NO, HYBRID
    
    # Source
    source_url = Column(String(512), nullable=True)
    source_name = Column(String(100), nullable=True)  # e.g., "BrighterMonday"
    
    # Status
    is_active = Column(String(20), default="ACTIVE")
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_job_skills', 'required_skills', postgresql_using='gin'),
        Index('idx_job_location', 'location'),
    )
    
    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"


class TrainingCenter(Base):
    """
    Training centers table - Government-accredited skills training facilities.
    Part of the DCI (Demand-Centered Innovation) pipeline.
    """
    __tablename__ = "training_centers"
    
    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Center details
    name = Column(String(255), nullable=False)
    accreditation = Column(String(100), nullable=True)  # KNEC, NITA, TVETA
    
    # Courses offered
    courses = Column(JSONB, nullable=False)  # [{name, skill, duration, cost}]
    
    # Location
    location_name = Column(String(255), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_long = Column(Float, nullable=False)
    county = Column(String(100), nullable=True)
    
    # Contact
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    website = Column(String(512), nullable=True)
    
    # Status
    is_active = Column(String(20), default="ACTIVE")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TrainingCenter {self.name} - {self.accreditation}>"
