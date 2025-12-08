from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for a subject (user id or email)."""
    settings = get_settings()
    to_encode = {"sub": subject, "iat": datetime.now(tz=timezone.utc)}
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


# PUBLIC_INTERFACE
def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT token returning its payload or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
