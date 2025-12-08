from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from src.api.deps import get_current_user
from src.db.models import Booking, BookingItem, BookingStatus, Notification, Seat, SeatInventory, Schedule, User
from src.db.session import get_db
from src.schemas.booking import (
    BookingItemOut,
    BookingOut,
    CreateBookingRequest,
    LockSeatsRequest,
    SeatMapResponse,
    SeatStatus,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _refresh_locks(db: Session, schedule_id: int):
    now = datetime.now(tz=timezone.utc)
    # Release expired locks
    db.query(SeatInventory).filter(
        SeatInventory.schedule_id == schedule_id,
        SeatInventory.is_locked.is_(True),
        SeatInventory.lock_expires_at.isnot(None),
        SeatInventory.lock_expires_at < now,
    ).update({"is_locked": False, "lock_expires_at": None}, synchronize_session=False)
    db.flush()


@router.get("/availability", summary="Get seat availability for a schedule", response_model=SeatMapResponse)
def availability(schedule_id: int = Query(...), db: Session = Depends(get_db)) -> SeatMapResponse:
    """Return seat map with lock and booking status for a schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    _refresh_locks(db, schedule_id)

    invs = (
        db.query(SeatInventory)
        .join(Seat, Seat.id == SeatInventory.seat_id)
        .filter(SeatInventory.schedule_id == schedule_id)
        .all()
    )
    seats = []
    for inv in invs:
        seat = inv.seat
        seats.append(
            SeatStatus(
                seat_inventory_id=inv.id,
                seat_id=seat.id,
                coach_number=seat.coach.coach_number,
                seat_number=seat.seat_number,
                seat_type=seat.seat_type,
                is_locked=inv.is_locked,
                is_booked=inv.is_booked,
            )
        )
    return SeatMapResponse(schedule_id=schedule_id, seats=seats)


@router.post("/lock", summary="Lock seats for limited time", response_model=SeatMapResponse)
def lock_seats(payload: LockSeatsRequest, db: Session = Depends(get_db)) -> SeatMapResponse:
    """Lock seats for N minutes to allow user to checkout."""
    _refresh_locks(db, payload.schedule_id)
    now = datetime.now(tz=timezone.utc)
    expires = now + timedelta(minutes=payload.lock_minutes)

    invs = (
        db.query(SeatInventory)
        .filter(SeatInventory.schedule_id == payload.schedule_id, SeatInventory.id.in_(payload.seat_inventory_ids))
        .with_for_update()
        .all()
    )
    if len(invs) != len(payload.seat_inventory_ids):
        raise HTTPException(status_code=400, detail="Some seats not found in schedule")

    # Ensure none are already booked or locked
    for inv in invs:
        if inv.is_booked:
            raise HTTPException(status_code=400, detail=f"Seat {inv.id} already booked")
        if inv.is_locked and inv.lock_expires_at and inv.lock_expires_at > now:
            raise HTTPException(status_code=400, detail=f"Seat {inv.id} already locked")

    for inv in invs:
        inv.is_locked = True
        inv.lock_expires_at = expires
    db.flush()

    # Return updated availability
    return availability(payload.schedule_id, db)


@router.post("", summary="Confirm booking", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: CreateBookingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingOut:
    """Confirm a booking by converting locked seats into booking items."""
    _refresh_locks(db, payload.schedule_id)
    now = datetime.now(tz=timezone.utc)

    invs = (
        db.query(SeatInventory)
        .filter(SeatInventory.schedule_id == payload.schedule_id, SeatInventory.id.in_(payload.seat_inventory_ids))
        .with_for_update()
        .all()
    )
    if len(invs) != len(payload.seat_inventory_ids):
        raise HTTPException(status_code=400, detail="Some seats not found")

    for inv in invs:
        if inv.is_booked:
            raise HTTPException(status_code=400, detail=f"Seat {inv.id} already booked")
        if not inv.is_locked or not inv.lock_expires_at or inv.lock_expires_at < now:
            raise HTTPException(status_code=400, detail=f"Seat {inv.id} not locked or lock expired")

    booking = Booking(user_id=user.id, schedule_id=payload.schedule_id, status=BookingStatus.confirmed, total_amount=payload.total_amount)
    db.add(booking)
    db.flush()

    items_out: list[BookingItemOut] = []
    for inv in invs:
        inv.is_booked = True
        inv.is_locked = False
        inv.lock_expires_at = None
        # For simplicity, distribute price evenly
        price_each = round(payload.total_amount / max(1, len(invs)), 2)
        item = BookingItem(booking_id=booking.id, seat_inventory_id=inv.id, price=price_each)
        db.add(item)
        db.flush()
        label = f"{inv.seat.coach.coach_number}-{inv.seat.seat_number}"
        items_out.append(BookingItemOut(seat_inventory_id=inv.id, seat_label=label, price=price_each))

    # Notification
    db.add(
        Notification(
            user_id=user.id,
            title="Booking Confirmed",
            message=f"Booking #{booking.id} has been confirmed.",
        )
    )

    return BookingOut(
        id=booking.id, schedule_id=booking.schedule_id, status=booking.status.value, total_amount=booking.total_amount, items=items_out
    )


@router.get("/mine", summary="List my bookings", response_model=List[BookingOut])
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> List[BookingOut]:
    """Return list of bookings for the current user."""
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.items).joinedload(BookingItem.seat_inventory).joinedload(SeatInventory.seat).joinedload(Seat.coach))
        .filter(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    results: list[BookingOut] = []
    for b in bookings:
        items: list[BookingItemOut] = []
        for it in b.items:
            inv = it.seat_inventory
            label = f"{inv.seat.coach.coach_number}-{inv.seat.seat_number}"
            items.append(BookingItemOut(seat_inventory_id=inv.id, seat_label=label, price=it.price))
        results.append(
            BookingOut(id=b.id, schedule_id=b.schedule_id, status=b.status.value, total_amount=b.total_amount, items=items)
        )
    return results


@router.get("/{booking_id}", summary="Get booking by id", response_model=BookingOut)
def get_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BookingOut:
    """Return a booking that belongs to the current user."""
    b = (
        db.query(Booking)
        .options(joinedload(Booking.items).joinedload(BookingItem.seat_inventory).joinedload(SeatInventory.seat).joinedload(Seat.coach))
        .filter(Booking.id == booking_id, Booking.user_id == user.id)
        .first()
    )
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")

    items: list[BookingItemOut] = []
    for it in b.items:
        inv = it.seat_inventory
        label = f"{inv.seat.coach.coach_number}-{inv.seat.seat_number}"
        items.append(BookingItemOut(seat_inventory_id=inv.id, seat_label=label, price=it.price))
    return BookingOut(id=b.id, schedule_id=b.schedule_id, status=b.status.value, total_amount=b.total_amount, items=items)
