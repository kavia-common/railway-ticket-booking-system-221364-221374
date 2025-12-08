from typing import List

from pydantic import BaseModel, Field


class SeatStatus(BaseModel):
    seat_inventory_id: int = Field(...)
    seat_id: int = Field(...)
    coach_number: str = Field(...)
    seat_number: str = Field(...)
    seat_type: str = Field(...)
    is_locked: bool = Field(...)
    is_booked: bool = Field(...)


class SeatMapResponse(BaseModel):
    schedule_id: int = Field(...)
    seats: List[SeatStatus] = Field(default_factory=list)


class LockSeatsRequest(BaseModel):
    schedule_id: int = Field(...)
    seat_inventory_ids: List[int] = Field(...)
    lock_minutes: int = Field(default=10, ge=1, le=60)


class CreateBookingRequest(BaseModel):
    schedule_id: int = Field(...)
    seat_inventory_ids: List[int] = Field(...)
    total_amount: float = Field(..., ge=0.0)


class BookingItemOut(BaseModel):
    seat_inventory_id: int = Field(...)
    seat_label: str = Field(...)
    price: float = Field(...)


class BookingOut(BaseModel):
    id: int = Field(...)
    schedule_id: int = Field(...)
    status: str = Field(...)
    total_amount: float = Field(...)
    items: List[BookingItemOut] = Field(default_factory=list)
