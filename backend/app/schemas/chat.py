from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Chat Schemas ====================

class ChatMessageRequest(BaseModel):
    """User message in conversational interface"""
    text: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class SuggestedAction(BaseModel):
    """Suggested action for user"""
    action_type: str  # e.g., "UPLOAD_CERTIFICATE", "VIEW_JOBS"
    label: str  # Human-readable label
    data: Optional[Dict[str, Any]] = None


class ExtractedEntities(BaseModel):
    """Entities extracted from user message"""
    skills: List[str] = []
    location: Optional[str] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """AI response to user message"""
    reply_text: str
    session_id: str
    suggested_actions: List[SuggestedAction] = []
    entities_extracted: Optional[ExtractedEntities] = None
    intent: Optional[str] = None  # PROFILE_UPDATE, JOB_SEARCH, etc.


class ConversationHistory(BaseModel):
    """User's conversation history"""
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
