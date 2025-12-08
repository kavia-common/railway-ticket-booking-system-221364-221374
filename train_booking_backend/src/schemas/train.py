from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field


class StationOut(BaseModel):
    id: int = Field(...)
    code: str = Field(...)
    name: str = Field(...)
    city: Optional[str] = Field(default=None)


class TrainOut(BaseModel):
    id: int = Field(...)
    number: str = Field(...)
    name: str = Field(...)


class TrainSearchResult(BaseModel):
    train: TrainOut
    route_id: int = Field(...)
    source: StationOut
    destination: StationOut


class ScheduleOut(BaseModel):
    id: int = Field(...)
    route_id: int = Field(...)
    travel_date: date = Field(...)
    departure_time: time = Field(...)
    arrival_time: time = Field(...)


class ScheduleDetail(BaseModel):
    schedule: ScheduleOut
    train: TrainOut
    source: StationOut
    destination: StationOut
    available_seats: int = Field(...)
