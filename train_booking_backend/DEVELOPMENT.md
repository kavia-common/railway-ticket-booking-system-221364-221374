Development notes

- Environment:
  - Copy .env and adjust DATABASE_URL, JWT_SECRET, CORS_ORIGINS as needed.
  - For Postgres, set DATABASE_URL to a SQLAlchemy DSN like:
    postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME

- Run server:
  uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

- Regenerate OpenAPI:
  python -m src.api.generate_openapi

- Seed minimal data for smoke test:
  python -m src.db.seed
