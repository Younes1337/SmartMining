from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .db import get_db
from . import models

app = FastAPI(title="Smart Mining Panel API")


# Create tables on startup (development convenience; replace with Alembic in prod)
@app.on_event("startup")
def on_startup():
    # Import Base and engine lazily to avoid circular imports
    from .db import Base, engine

    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/samples")
def list_samples(db: Session = Depends(get_db)):
    items = db.query(models.Sample).limit(100).all()
    return [
        {
            "id": s.id,
            "x": s.x,
            "y": s.y,
            "z": s.z,
            "grade_percent": s.grade_percent,
        }
        for s in items
    ]
