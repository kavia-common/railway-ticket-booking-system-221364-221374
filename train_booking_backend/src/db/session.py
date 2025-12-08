from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine (sync)
engine = create_engine(settings.DATABASE_URL, future=True, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base class for models
Base = declarative_base()


# PUBLIC_INTERFACE
@contextmanager
def get_db() -> Generator:
    """Yield a database session and ensure proper close/rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
