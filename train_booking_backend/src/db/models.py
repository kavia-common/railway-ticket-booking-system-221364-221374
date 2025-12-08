from datetime import datetime, date, time
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.session import Base


class PaymentStatus(str, Enum):
    created = "created"
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class BookingStatus(str, Enum):
    created = "created"
    locked = "locked"
    confirmed = "confirmed"
    cancelled = "cancelled"


class NotificationType(str, Enum):
    info = "info"
    booking = "booking"
    payment = "payment"
    system = "system"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Station(Base):
    __tablename__ = "stations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    routes_from = relationship("TrainRoute", back_populates="source_station", foreign_keys="TrainRoute.source_station_id")
    routes_to = relationship("TrainRoute", back_populates="destination_station", foreign_keys="TrainRoute.destination_station_id")


class Train(Base):
    __tablename__ = "trains"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    routes = relationship("TrainRoute", back_populates="train")
    coaches = relationship("Coach", back_populates="train")


class TrainRoute(Base):
    __tablename__ = "train_routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False)
    source_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    destination_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)

    train = relationship("Train", back_populates="routes")
    source_station = relationship("Station", foreign_keys=[source_station_id], back_populates="routes_from")
    destination_station = relationship("Station", foreign_keys=[destination_station_id], back_populates="routes_to")
    schedules = relationship("Schedule", back_populates="route", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("train_id", "source_station_id", "destination_station_id", name="uq_route"),)


class Schedule(Base):
    __tablename__ = "schedules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("train_routes.id"), nullable=False, index=True)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, nullable=False)

    route = relationship("TrainRoute", back_populates="schedules")
    seat_inventories = relationship("SeatInventory", back_populates="schedule", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="schedule")


class Coach(Base):
    __tablename__ = "coaches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False)
    coach_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "AC", "Sleeper"
    coach_number: Mapped[str] = mapped_column(String(20), nullable=False)

    train = relationship("Train", back_populates="coaches")
    seats = relationship("Seat", back_populates="coach", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("train_id", "coach_number", name="uq_train_coach"),)


class Seat(Base):
    __tablename__ = "seats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id"), nullable=False)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    seat_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Window", "Middle", "Aisle"

    coach = relationship("Coach", back_populates="seats")

    __table_args__ = (UniqueConstraint("coach_id", "seat_number", name="uq_coach_seat"),)


class SeatInventory(Base):
    __tablename__ = "seat_inventory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), index=True, nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"), nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lock_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    schedule = relationship("Schedule", back_populates="seat_inventories")
    seat = relationship("Seat")

    __table_args__ = (UniqueConstraint("schedule_id", "seat_id", name="uq_schedule_seat"),)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), nullable=False, index=True)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), default=BookingStatus.created, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="bookings")
    schedule = relationship("Schedule", back_populates="bookings")
    items = relationship("BookingItem", back_populates="booking", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")


class BookingItem(Base):
    __tablename__ = "booking_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False, index=True)
    seat_inventory_id: Mapped[int] = mapped_column(ForeignKey("seat_inventory.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    booking = relationship("Booking", back_populates="items")
    seat_inventory = relationship("SeatInventory")

    __table_args__ = (UniqueConstraint("booking_id", "seat_inventory_id", name="uq_booking_seat_inv"),)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.created, nullable=False)
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    booking = relationship("Booking", back_populates="payment")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType), default=NotificationType.info, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("length(action) > 0", name="ck_action_non_empty"),
    )
