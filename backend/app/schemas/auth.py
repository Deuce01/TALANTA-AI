from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


# ==================== Authentication Schemas ====================

class LoginRequest(BaseModel):
    """Request to initiate login with phone number"""
    phone_number: str = Field(..., description="Phone number (format: +254XXXXXXXXX or 07XXXXXXXX)")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate Kenyan phone number format"""
        import re
        # Remove whitespace
        v = v.strip().replace(" ", "")
        
        # Accept both +254 and 07/01 formats
        if not re.match(r'^(\+254|254|0)[17]\d{8}$', v):
            raise ValueError('Invalid Kenyan phone number format')
        
        # Normalize to +254 format
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        
        return v


class LoginResponse(BaseModel):
    """Response after login request"""
    message: str
    session_id: str
    expires_in_minutes: int


class VerifyOTPRequest(BaseModel):
    """Request to verify OTP"""
    phone_number: str
    otp: str = Field(..., min_length=6, max_length=6)
    session_id: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: 'UserProfile'


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str


# ==================== User Schemas ====================

class UserProfile(BaseModel):
    """User profile information"""
    id: str
    phone_hash: str
    full_name: Optional[str] = None
    location_name: Optional[str] = None
    trust_score: int
    role: str
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update user profile"""
    full_name: Optional[str] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_long: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = None
