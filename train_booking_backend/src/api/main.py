from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.auth import router as auth_router
from src.api.routes.trains import router as trains_router
from src.api.routes.schedules import router as schedules_router
from src.api.routes.bookings import router as bookings_router
from src.api.routes.payments import router as payments_router
from src.api.routes.notifications import router as notifications_router
from src.core.config import get_cors_origins, get_settings
from src.db.session import Base, engine

settings = get_settings()

app = FastAPI(
    title="Train Booking Backend",
    description="APIs for authentication, train search, schedules, bookings, payments (mock), and notifications.",
    version="0.1.0",
)

# Create tables if not present (for demo simplicity; production would use migrations)
Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Health Check", tags=["Health"])
def health_check():
    """Health check endpoint.

    Returns:
        dict: Simple JSON indicating service health.
    """
    return {"message": "Healthy"}


# Include routers
app.include_router(auth_router)
app.include_router(trains_router)
app.include_router(schedules_router)
app.include_router(bookings_router)
app.include_router(payments_router)
app.include_router(notifications_router)
