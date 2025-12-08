from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Message(BaseModel):
    """Simple message response."""
    message: str = Field(..., description="Human readable message")


class Token(BaseModel):
    """JWT Token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type, typically bearer")


class ResponseEnvelope(Generic[T], BaseModel):
    """Envelope for standard API responses."""
    success: bool = Field(default=True, description="Flag indicating success")
    data: Optional[T] = Field(default=None, description="Response payload")
    error: Optional[str] = Field(default=None, description="Error message if any")
