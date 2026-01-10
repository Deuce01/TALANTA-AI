from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
import string

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Password Utilities ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== Phone Number Hashing (Data Sovereignty) ====================

def hash_phone_number(phone: str) -> str:
    """
    Hash phone number with salt for privacy.
    This ensures phone numbers are never stored in plain text.
    """
    salted = f"{phone}{settings.PHONE_HASH_SALT}"
    return hashlib.sha256(salted.encode()).hexdigest()


# ==================== JWT Token Management ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode (typically user_id, role, etc.)
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ==================== OTP Generation ====================

def generate_otp(length: int = None) -> str:
    """
    Generate a cryptographically secure numeric OTP.
    
    Args:
        length: OTP length (default from settings)
    
    Returns:
        Numeric OTP string (e.g., "749302")
    """
    if length is None:
        length = settings.OTP_LENGTH
    
    # Generate cryptographically secure random digits
    digits = string.digits
    otp = ''.join(secrets.choice(digits) for _ in range(length))
    
    return otp


def generate_session_id() -> str:
    """Generate a unique session identifier"""
    return secrets.token_urlsafe(32)


# ==================== Data Encryption Utilities ====================

def hash_maisha_namba(namba: str) -> str:
    """
    Hash Maisha Namba (National ID) for secure storage.
    Uses SHA256 to create a one-way hash.
    """
    return hashlib.sha256(f"{namba}{settings.PHONE_HASH_SALT}".encode()).hexdigest()


# ==================== Token Validation ====================

class TokenData:
    """Structure for validated token data"""
    def __init__(self, user_id: str, role: str, **kwargs):
        self.user_id = user_id
        self.role = role
        self.extra = kwargs


def get_token_data(token: str) -> Optional[TokenData]:
    """
    Extract and validate token data.
    
    Returns:
        TokenData object if valid, None otherwise
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != "access":
        return None
    
    user_id = payload.get("sub")
    role = payload.get("role", "CITIZEN")
    
    if user_id is None:
        return None
    
    return TokenData(user_id=user_id, role=role, **payload)
