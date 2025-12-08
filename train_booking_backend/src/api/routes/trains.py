from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.db.models import Schedule, Station, Train, TrainRoute
from src.db.session import get_db
from src.schemas.train import ScheduleOut, StationOut, TrainOut, TrainSearchResult

router = APIRouter(prefix="/trains", tags=["Trains"])


@router.get("/search", summary="Search trains by source, destination, and date", response_model=List[TrainSearchResult])
def search_trains(
    source: str = Query(..., description="Source station code"),
    destination: str = Query(..., description="Destination station code"),
    date_: date = Query(alias="date", description="Travel date"),
    db: Session = Depends(get_db),
):
    """Return trains and routes matching requested source, destination and (optional) date."""
    src = db.query(Station).filter(Station.code == source.upper()).first()
    dst = db.query(Station).filter(Station.code == destination.upper()).first()
    if not src or not dst:
        raise HTTPException(status_code=404, detail="Invalid station code(s)")

    routes = (
        db.query(TrainRoute)
        .options(joinedload(TrainRoute.train), joinedload(TrainRoute.source_station), joinedload(TrainRoute.destination_station))
        .filter(TrainRoute.source_station_id == src.id, TrainRoute.destination_station_id == dst.id)
        .all()
    )
    results: list[TrainSearchResult] = []
    for r in routes:
        results.append(
            TrainSearchResult(
                train=TrainOut(id=r.train.id, number=r.train.number, name=r.train.name),
                route_id=r.id,
                source=StationOut(id=src.id, code=src.code, name=src.name, city=src.city),
                destination=StationOut(id=dst.id, code=dst.code, name=dst.name, city=dst.city),
            )
        )
    return results


@router.get("/{train_id}/schedules", summary="Get schedules for a train (by route/date)", response_model=List[ScheduleOut])
def get_schedules(
    train_id: int,
    date_: date | None = Query(default=None, alias="date", description="Filter by travel date"),
    db: Session = Depends(get_db),
):
    """Return schedules for a specific train_id optionally filtered by date."""
    train = db.query(Train).filter(Train.id == train_id).first()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    q = (
        db.query(Schedule)
        .join(TrainRoute, TrainRoute.id == Schedule.route_id)
        .filter(TrainRoute.train_id == train_id)
    )
    if date_:
        q = q.filter(Schedule.travel_date == date_)
    schedules = q.all()
    return [
        ScheduleOut(
            id=s.id, route_id=s.route_id, travel_date=s.travel_date, departure_time=s.departure_time, arrival_time=s.arrival_time
        )
        for s in schedules
    ]
