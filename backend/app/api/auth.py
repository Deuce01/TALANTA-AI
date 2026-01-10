from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import logging

from app.database import get_db, get_redis
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    VerifyOTPRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfile,
)
from app.core.security import (
    hash_phone_number,
    generate_otp,
    generate_session_id,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Module A: Progressive Authentication - Step 1
    
    Initiate login with phone number.
    Generates OTP and stores in Redis with 5-minute TTL.
    
    Zero-friction entry: No password required initially.
    """
    phone = request.phone_number
    
    # Check rate limiting (max 3 OTP requests per hour per phone)
    rate_limit_key = f"otp_rate:{hash_phone_number(phone)}"
    request_count = await redis.get(rate_limit_key)
    
    if request_count and int(request_count) >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please try again in 1 hour."
        )
    
    # Generate OTP
    otp = generate_otp()
    session_id = generate_session_id()
    
    # Store OTP in Redis (5-minute TTL)
    otp_key = f"otp:{session_id}"
    otp_data = f"{phone}:{otp}"
    await redis.setex(otp_key, settings.OTP_EXPIRY_MINUTES * 60, otp_data)
    
    # Initialize attempt counter
    attempt_key = f"otp_attempts:{session_id}"
    await redis.setex(attempt_key, settings.OTP_EXPIRY_MINUTES * 60, "0")
    
    # Update rate limiting
    if request_count:
        await redis.incr(rate_limit_key)
    else:
        await redis.setex(rate_limit_key, 3600, "1")  # 1 hour TTL
    
    # In production: Send SMS via Africa's Talking
    if settings.ENVIRONMENT == "production" and settings.SMS_API_KEY:
        # TODO: Integrate Africa's Talking SMS API
        logger.info(f"Sending OTP {otp} to {phone}")
    else:
        # Development: Log OTP
        logger.info(f"🔐 OTP for {phone}: {otp}")
    
    return LoginResponse(
        message="OTP sent successfully. Check your SMS.",
        session_id=session_id,
        expires_in_minutes=settings.OTP_EXPIRY_MINUTES,
    )


@router.post("/verify", response_model=TokenResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Module A: Progressive Authentication - Step 2
    
    Verify OTP and issue JWT tokens.
    Creates user account if first-time login.
    """
    session_id = request.session_id
    provided_otp = request.otp
    phone = request.phone_number
    
    # Check attempts
    attempt_key = f"otp_attempts:{session_id}"
    attempts = await redis.get(attempt_key)
    
    if attempts and int(attempts) >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maximum OTP attempts exceeded. Please request a new OTP."
        )
    
    # Retrieve OTP from Redis
    otp_key = f"otp:{session_id}"
    stored_data = await redis.get(otp_key)
    
    if not stored_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP session."
        )
    
    stored_phone, stored_otp = stored_data.split(":")
    
    # Verify phone match
    if stored_phone != phone:
        await redis.incr(attempt_key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number mismatch."
        )
    
    # Verify OTP
    if stored_otp != provided_otp:
        await redis.incr(attempt_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP. Please try again."
        )
    
    # OTP verified! Clean up Redis
    await redis.delete(otp_key)
    await redis.delete(attempt_key)
    
    # Find or create user
    phone_hash = hash_phone_number(phone)
    
    result = await db.execute(
        select(User).where(User.phone_hash == phone_hash)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # First-time user: Create account
        user = User(
            phone_hash=phone_hash,
            role=UserRole.CITIZEN,
            trust_score=0,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✓ New user created: {user.id}")
    else:
        # Existing user: Update last active
        from datetime import datetime
        user.last_active_at = datetime.utcnow()
        await db.commit()
    
    # Generate JWT tokens
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
        "trust_score": user.trust_score,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Create user profile response
    user_profile = UserProfile(
        id=str(user.id),
        phone_hash=user.phone_hash,
        full_name=user.full_name,
        location_name=user.location_name,
        trust_score=user.trust_score,
        role=user.role.value,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile,
    )


@router.post("/refresh", response_model=dict)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    token_data = {
        "sub": str(user.id),
        "role": user.role.value,
        "trust_score": user.trust_score,
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
