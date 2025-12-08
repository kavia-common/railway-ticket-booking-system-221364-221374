from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.security import create_access_token, get_password_hash, verify_password
from src.db.models import User
from src.db.session import get_db
from src.schemas.auth import UserCreate, UserLogin, UserOut
from src.schemas.common import Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", summary="Register a new user", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """Create a new user account."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()  # assign id
    return UserOut(id=user.id, email=user.email, full_name=user.full_name)


@router.post("/login", summary="Login and get JWT token", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate user and return JWT bearer token."""
    user: User | None = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    settings = get_settings()
    token = create_access_token(subject=user.email, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=token, token_type="bearer")
