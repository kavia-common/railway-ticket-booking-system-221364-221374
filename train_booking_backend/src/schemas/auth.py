from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Payload to create a user account."""
    email: EmailStr = Field(..., description="User email")
    full_name: str | None = Field(default=None, description="Full name")
    password: str = Field(..., min_length=6, description="Password")


class UserLogin(BaseModel):
    """Payload to login and obtain JWT."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")


class UserOut(BaseModel):
    """User info to return to clients."""
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email")
    full_name: str | None = Field(default=None, description="Full name")
