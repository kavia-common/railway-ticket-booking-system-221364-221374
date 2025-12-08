from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    booking_id: int = Field(...)
    amount: float = Field(..., ge=0.0)


class PaymentOut(BaseModel):
    id: int = Field(...)
    booking_id: int = Field(...)
    amount: float = Field(...)
    status: str = Field(...)
    provider_ref: str | None = Field(default=None)
