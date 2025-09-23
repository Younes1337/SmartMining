# Backend

FastAPI-based REST API serving data ingestion, querying, and ML predictions.

- Stack: FastAPI, Uvicorn (ASGI), SQLAlchemy, PostgreSQL, Pydantic, pandas, scikit-learn, python-dotenv
- Env: set `DATABASE_URL` (e.g., `postgresql+psycopg2://USER:PASS@HOST:5432/DB`)
- Endpoints:
  - `POST /ingest` — CSV upload (multipart) or local file via `?filename=`; loads rows into `forages`.
  - `GET /data` — returns recent forages as JSON (up to 1000 rows).
  - `GET /model/info` — shows model artifacts presence/load status.
  - `POST /predict` — body: `{ x_coord, y_coord, z_coord }`; returns `{ predicted_teneur, model }`.

## Run (local)

```
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## Notes
- Tables are created on startup for dev. Use Alembic for production migrations.
- Ensure artifacts exist under `models/`.
