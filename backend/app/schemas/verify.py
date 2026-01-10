from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ==================== Verification Schemas ====================

class UploadDocumentResponse(BaseModel):
    """Response after document upload"""
    verification_id: str
    status: str
    estimated_time: str
    message: str


class VerificationStatusResponse(BaseModel):
    """Verification status check"""
    verification_id: str
    status: str
    document_type: str
    created_at: datetime
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    extracted_skill: Optional[str] = None
    trust_score_delta: int


class MyVerificationsResponse(BaseModel):
    """List of user's verifications"""
    verifications: List[VerificationStatusResponse]
    total_count: int
    verified_count: int
    pending_count: int
