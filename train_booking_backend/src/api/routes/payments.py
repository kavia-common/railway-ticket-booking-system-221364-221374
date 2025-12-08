from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db.models import Booking, Payment, PaymentStatus, User
from src.db.session import get_db
from src.schemas.payment import PaymentCreateRequest, PaymentOut
from src.services.payment_provider import MockPaymentProvider

router = APIRouter(prefix="/payments", tags=["Payments"])

provider = MockPaymentProvider()


@router.post("/create", summary="Create a payment for a booking", response_model=PaymentOut)
def create_payment(payload: PaymentCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOut:
    """Create a payment record and external payment intent (mock)."""
    booking = db.query(Booking).filter(Booking.id == payload.booking_id, Booking.user_id == user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if payment:
        return PaymentOut(id=payment.id, booking_id=payment.booking_id, amount=payment.amount, status=payment.status.value, provider_ref=payment.provider_ref)

    provider_ref = provider.create(amount=payload.amount)
    payment = Payment(booking_id=booking.id, amount=payload.amount, status=PaymentStatus.created, provider_ref=provider_ref)
    db.add(payment)
    db.flush()

    return PaymentOut(id=payment.id, booking_id=payment.booking_id, amount=payment.amount, status=payment.status.value, provider_ref=payment.provider_ref)


@router.get("/{payment_id}/status", summary="Get payment status", response_model=PaymentOut)
def payment_status(payment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOut:
    """Return payment status (mock provider)."""
    payment = db.query(Payment).join(Booking).filter(Payment.id == payment_id, Booking.user_id == user.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # simulate provider status
    status_str = provider.status(payment.provider_ref or "")
    if status_str != payment.status.value and payment.status != PaymentStatus.succeeded:
        # update if provider progressed
        payment.status = PaymentStatus.pending
        db.flush()

    return PaymentOut(id=payment.id, booking_id=payment.booking_id, amount=payment.amount, status=payment.status.value, provider_ref=payment.provider_ref)


@router.post("/{payment_id}/confirm", summary="Confirm payment (mock)", response_model=PaymentOut)
def confirm_payment(payment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentOut:
    """Confirm payment and update booking status."""
    payment = db.query(Payment).join(Booking).filter(Payment.id == payment_id, Booking.user_id == user.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    provider.confirm(payment.provider_ref or "")
    payment.status = PaymentStatus.succeeded
    payment.booking.status = payment.booking.status  # no-op; could set to confirmed if different flow
    db.flush()
    return PaymentOut(id=payment.id, booking_id=payment.booking_id, amount=payment.amount, status=payment.status.value, provider_ref=payment.provider_ref)
