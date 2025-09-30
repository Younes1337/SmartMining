from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import pandas as pd
from pathlib import Path
import re
import joblib
import warnings
from sklearn.exceptions import InconsistentVersionWarning

from .db import get_db
from . import models
from .schemas import ForageOut, PredictRequest, PredictResponse

app = FastAPI(title="Smart Mining Panel API")

# Suppress sklearn version mismatch warnings shown when unpickling estimators
#warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

# Enable CORS for all origins in development
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

    # Load pretrained ML components from models/ with detailed diagnostics
    global _POLY, _SCALER, _PCA, _KNN, _MODEL_STATUS
    _MODEL_STATUS = {
        "dir": None,
        "artifacts": {
            "poly_transform.pkl": {"exists": False, "loaded": False, "error": None},
            "scaler.pkl": {"exists": False, "loaded": False, "error": None},
            "pca_transform.pkl": {"exists": False, "loaded": False, "error": None},
            "knn_model.pkl": {"exists": False, "loaded": False, "error": None},
        },
    }

    _POLY = _SCALER = _PCA = _KNN = None
    project_root = Path(__file__).resolve().parents[1]
    models_dir = project_root / "models"
    _MODEL_STATUS["dir"] = str(models_dir)

    def _load(name: str):
        path = models_dir / name
        entry = _MODEL_STATUS["artifacts"][name]
        entry["exists"] = path.exists()
        if not entry["exists"]:
            return None
        try:
            obj = joblib.load(path)
            entry["loaded"] = True
            return obj
        except Exception as e:
            entry["error"] = str(e)
            return None

    _POLY = _load("poly_transform.pkl")
    _SCALER = _load("scaler.pkl")
    _PCA = _load("pca_transform.pkl")
    _KNN = _load("knn_model.pkl")



@app.post("/ingest")
async def ingest_csv(
    filename: Optional[str] = Query(None, description="CSV filename inside the data/ directory"),
    file: Optional[UploadFile] = File(None, description="CSV file uploaded via multipart/form-data"),
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

    # If a file is uploaded via multipart, read it. Otherwise fall back to data/ directory selection
    if file is not None:
        try:
            contents = await file.read()
            # Support auto separator detection
            df = pd.read_csv(io.BytesIO(contents), sep=None, engine="python")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read uploaded CSV: {e}")
    else:
        # Ingest from data/ directory
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
    
    # Get all existing IDs from the database once
    existing_ids = {int(id_[0]) for id_ in db.query(models.Forage.id).all()}
    max_id = max(existing_ids) if existing_ids else 0
    next_id = max_id + 1
    
    # Track IDs we've seen in this batch to handle duplicates within the same file
    seen_ids_in_batch = set()
    duplicate_count = 0
    
    for _, row in df.iterrows():
        id_val = None
        if has_id and pd.notna(row.get("id")):
            try:
                id_val = int(row["id"])
                # If this ID is already in use, assign a new one
                if id_val in seen_ids_in_batch or id_val in existing_ids:
                    id_val = next_id
                    next_id += 1
                    duplicate_count += 1
                seen_ids_in_batch.add(id_val)
                existing_ids.add(id_val)  # Add to existing to prevent reuse in this batch
                
            except (ValueError, TypeError) as e:
                # If ID is not a valid integer, generate a new one
                id_val = next_id
                next_id += 1
        else:
            id_val = next_id
            next_id += 1
        # Create record with the assigned ID
        to_insert.append(
            models.Forage(
                id=id_val,
                x_coord=float(row["x_coord"]),
                y_coord=float(row["y_coord"]),
                z_coord=float(row["z_coord"]),
                teneur=float(row["teneur"]),
            )
        )

    # Insert all records in a single transaction
    try:
        db.add_all(to_insert)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database insert failed: {e}")

    return {
        "filename": (chosen_path.name if chosen_path is not None else getattr(file, "filename", None)),
        "rows_received": int(before_rows),
        "rows_inserted": int(len(to_insert)),
        "rows_dropped": int(dropped_rows),
        "duplicate_ids_handled": int(duplicate_count),
        "next_available_id": int(next_id)
    }


@app.get("/model/info")
def model_info():
    """Return the status of model artifacts and their loading state."""
    return _MODEL_STATUS


@app.get("/data", response_model=List[ForageOut])
def get_data(db: Session = Depends(get_db)):
    items = db.query(models.Forage).limit(1000).all()
    return items


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, db: Session = Depends(get_db)):
    # Ensure pretrained artifacts are loaded
    missing = []
    if _POLY is None:
        missing.append("poly_transform.pkl")
    if _SCALER is None:
        missing.append("scaler.pkl")
    if _PCA is None:
        missing.append("pca_transform.pkl")
    if _KNN is None:
        missing.append("knn_model.pkl")
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Model pipeline not available. Missing or failed to load: {missing}. See /model/info for details.",
        )

    # Build DataFrame with expected columns order X, Y, Z
    df = pd.DataFrame({
        'X': [payload.x_coord],
        'Y': [payload.y_coord],
        'Z': [payload.z_coord],
    })

    try:
        X_poly = _POLY.transform(df[['X', 'Y', 'Z']])
        X_scaled = _SCALER.transform(X_poly)
        X_pca = _PCA.transform(X_scaled)
        y_pred = _KNN.predict(X_pca)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return PredictResponse(predicted_teneur=float(y_pred), model=type(_KNN).__name__)
