from datetime import date, time
from sqlalchemy.orm import Session

from src.db.session import SessionLocal, Base, engine
from src.db.models import (
    Station,
    Train,
    TrainRoute,
    Schedule,
    Coach,
    Seat,
    SeatInventory,
)

def _get_or_create(db: Session, model, defaults=None, **kwargs):
    """Utility to get or create a row."""
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True

def seed():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Stations
        s1, _ = _get_or_create(db, Station, code="SRC", name="Source Central", city="Source City")
        s2, _ = _get_or_create(db, Station, code="DST", name="Destination Terminal", city="Destination City")

        # Train
        train, _ = _get_or_create(db, Train, number="TB1001", name="Kavia Express")

        # Route
        route, _ = _get_or_create(
            db, TrainRoute,
            train_id=train.id,
            source_station_id=s1.id,
            destination_station_id=s2.id,
        )

        # Schedule (today)
        today = date.today()
        sched, created = _get_or_create(
            db, Schedule,
            route_id=route.id,
            travel_date=today,
            defaults={"departure_time": time(9, 0, 0), "arrival_time": time(12, 30, 0)},
        )
        if created:
            sched.departure_time = time(9, 0, 0)
            sched.arrival_time = time(12, 30, 0)

        # Coach
        coach, _ = _get_or_create(
            db, Coach,
            train_id=train.id,
            coach_type="AC",
            coach_number="C1",
        )

        # Seats (10 seats)
        seats = []
        for i in range(1, 11):
            seat, _ = _get_or_create(
                db, Seat,
                coach_id=coach.id,
                seat_number=str(i),
                seat_type="Window" if i % 2 == 1 else "Aisle",
            )
            seats.append(seat)

        # Seat inventory for schedule
        for seat in seats:
            _si, _ = _get_or_create(
                db, SeatInventory,
                schedule_id=sched.id,
                seat_id=seat.id,
            )

        db.commit()
        print("Database seeded successfully.")
        print(f"- Stations: {s1.code} -> {s2.code}")
        print(f"- Train: {train.number} {train.name}")
        print(f"- Route ID: {route.id}")
        print(f"- Schedule ID: {sched.id} (date={sched.travel_date})")
        print("- Coach C1 with 10 seats, inventory created.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
