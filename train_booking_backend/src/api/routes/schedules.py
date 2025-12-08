from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from src.db.models import Schedule, TrainRoute
from src.db.session import get_db
from src.schemas.train import ScheduleDetail, ScheduleOut, StationOut, TrainOut

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("/{schedule_id}", summary="Get schedule details", response_model=ScheduleDetail)
def get_schedule_detail(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleDetail:
    """Return a detailed schedule view including train and stations."""
    schedule = (
        db.query(Schedule)
        .options(joinedload(Schedule.route).joinedload(TrainRoute.train))
        .options(joinedload(Schedule.route).joinedload(TrainRoute.source_station))
        .options(joinedload(Schedule.route).joinedload(TrainRoute.destination_station))
        .filter(Schedule.id == schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    route = schedule.route
    train = route.train
    return ScheduleDetail(
        schedule=ScheduleOut(
            id=schedule.id,
            route_id=schedule.route_id,
            travel_date=schedule.travel_date,
            departure_time=schedule.departure_time,
            arrival_time=schedule.arrival_time,
        ),
        train=TrainOut(id=train.id, number=train.number, name=train.name),
        source=StationOut(
            id=route.source_station.id,
            code=route.source_station.code,
            name=route.source_station.name,
            city=route.source_station.city,
        ),
        destination=StationOut(
            id=route.destination_station.id,
            code=route.destination_station.code,
            name=route.destination_station.name,
            city=route.destination_station.city,
        ),
        available_seats=0,
    )
