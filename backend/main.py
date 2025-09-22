from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import pandas as pd
from pathlib import Path
import re

from .db import get_db
from . import models
from .schemas import ForageOut, PredictRequest, PredictResponse

app = FastAPI(title="Smart Mining Panel API")

# Enable CORS for local development (React default ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 


# Create tables on startup (development convenience; replace with Alembic in prod)
@app.on_event("startup")
def on_startup():
    # Import Base and engine lazily to avoid circular imports
    from .db import Base, engine

    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
async def ingest_csv(
    filename: Optional[str] = Query(None, description="CSV filename inside the data/ directory"),
    db: Session = Depends(get_db),
):
    """Ingest data into the forages table.

    Supported modes:
    - Multipart upload: provide a CSV file via 'file'.
    - Local file: omit 'file' and provide 'filename' that exists under the project's data/ directory.
    If 'filename' is omitted and exactly one CSV is found in data/, it will be used automatically.
    """

    df = None
    chosen_path: Optional[Path] = None

    # Ingest strictly from data/ directory
    project_root = Path(__file__).resolve().parents[1]  # repo root
    data_dir = project_root / "data"
    if not data_dir.exists() or not data_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Data directory not found: {data_dir}")

    if filename:
        candidate = data_dir / filename
        if not candidate.exists() or not candidate.is_file():
            raise HTTPException(status_code=400, detail=f"File not found in data/: {filename}")
        chosen_path = candidate
    else:
        csvs = list(data_dir.glob("*.csv"))
        if len(csvs) == 0:
            raise HTTPException(status_code=400, detail="No CSV files found in data/ directory")
        if len(csvs) > 1:
            raise HTTPException(status_code=400, detail=f"Multiple CSVs found in data/. Specify one via filename. Available: {[p.name for p in csvs]}")
        chosen_path = csvs[0]

    try:
        # Auto-detect separators like ',' or ';'
        df = pd.read_csv(chosen_path, sep=None, engine="python")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV from data/: {e}")

    # Normalize and map columns to expected names
    def _normalize(name: str) -> str:
        s = name.strip().lower()
        s = s.replace("%", "percent")
        s = s.replace(" ", "_")
        s = re.sub(r"[^a-z0-9_]", "", s)
        return s

    rename_map = {}
    for col in list(df.columns):
        norm = _normalize(col)
        target = None
        if norm in {"id"}:
            target = "id"
        elif norm in {"x", "x_coord", "xcoordinate"}:
            target = "x_coord"
        elif norm in {"y", "y_coord", "ycoordinate"}:
            target = "y_coord"
        elif norm in {"z", "z_coord", "zcoordinate"}:
            target = "z_coord"
        elif norm in {"teneur", "teneur_", "teneurpercent", "teneur_percent", "grade"}:
            target = "teneur"
        if target and col != target:
            rename_map[col] = target

    if rename_map:
        df = df.rename(columns=rename_map)

    required_cols = ["x_coord", "y_coord", "z_coord", "teneur"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    # Detect optional 'id' column
    has_id = "id" in df.columns

    # Coerce to numeric and drop invalid rows
    for c in required_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if has_id:
        # Allow nullable integer IDs; DB will auto-generate when null
        df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    before_rows = len(df)
    df = df.dropna(subset=required_cols)
    valid_rows = len(df)
    dropped_rows = before_rows - valid_rows

    # Prepare SQLAlchemy objects
    to_insert = []
    for _, row in df.iterrows():
        id_val = None
        if has_id and pd.notna(row.get("id")):
            try:
                id_val = int(row["id"])
            except Exception:
                id_val = None
        to_insert.append(
            models.Forage(
                id=id_val,
                x_coord=float(row["x_coord"]),
                y_coord=float(row["y_coord"]),
                z_coord=float(row["z_coord"]),
                teneur=float(row["teneur"]),
            )
        )

    try:
        if to_insert:
            db.add_all(to_insert)
            db.commit()
        inserted = len(to_insert)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database insert failed: {e}")

    return {
        "filename": (chosen_path.name if chosen_path is not None else None),
        "rows_received": int(before_rows),
        "rows_inserted": int(inserted),
        "rows_dropped": int(dropped_rows),
    }


@app.get("/data", response_model=List[ForageOut])
def get_data(db: Session = Depends(get_db)):
    items = db.query(models.Forage).limit(1000).all()
    return items


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, db: Session = Depends(get_db)):
    # Placeholder implementation; will be replaced after training the ML model
    # For now, return a naive baseline (e.g., mean of available teneur) to keep the flow working
    avg = db.query(models.Forage).with_entities(models.Forage.teneur).all()
    if not avg:
        raise HTTPException(status_code=503, detail="No data available to compute baseline prediction.")
    mean_teneur = sum(v[0] for v in avg) / len(avg)
    return PredictResponse(predicted_teneur=float(mean_teneur), model="baseline-mean")
