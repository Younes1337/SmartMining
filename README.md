<div align="center">

# Smart Mining Panel

Interactive geospatial dashboard for ingesting drillhole data, visualizing samples on a map, and predicting ore grade using a pre-trained ML pipeline.

[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React-61DAFB?logo=react&logoColor=222222)](https://react.dev/)
[![Postgres](https://img.shields.io/badge/DB-PostgreSQL-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

</div>

## Documentation

For the full project documentation, visit the GitBook:

- https://youness-organization-4.gitbook.io/smartmining-panel/

---

## Overview

`Smart Mining Panel` is a full‑stack project that enables mining teams to:

- Ingest assay/drillhole CSV data into a PostgreSQL database
- Explore points on a map with Leaflet
- Query recent samples via a simple API
- Run grade predictions via a pre-trained ML pipeline (Polynomial → Scaler → PCA → KNN)

The stack is split into a FastAPI backend and a React frontend.

## Screenshot

<p align="center">
  <img src="./UI_screenshot.png" alt="Smart Mining Panel UI" width="1000" />
</p>

<p align="center"><i>Interactive map view and controls from the React frontend.</i></p>

## Repository Structure

```
smart-mining-panel8/
├─ backend/                 # FastAPI service
│  ├─ main.py               # API endpoints (/ingest, /data, /predict, /model/info)
│  ├─ db.py                 # SQLAlchemy engine & session factory
│  ├─ models.py             # ORM models (e.g., Forage)
│  ├─ schemas.py            # Pydantic schemas
│  └─ requirements.txt      # Backend dependencies
├─ frontend/                # React app (Create React App)
│  ├─ src/                  # UI code (Map view, API client)
│  └─ package.json          # Frontend scripts & deps
├─ models/                  # Pretrained ML artifacts (joblib)
│  ├─ poly_transform.pkl
│  ├─ scaler.pkl
│  ├─ pca_transform.pkl
│  └─ knn_model.pkl
├─ data/                    # Put your CSVs here for ingestion
├─ .env                     # Environment variables (see below)
├─ LICENSE                  # Apache 2.0
└─ README.md
```

## File Overview

| Path | Role |
| --- | --- |
| `backend/main.py` | FastAPI app with endpoints: `/ingest`, `/data`, `/predict`, `/model/info`; starts up DB and loads ML artifacts. |
| `backend/db.py` | SQLAlchemy engine/session factory; reads `DATABASE_URL` from `.env`. |
| `backend/models.py` | ORM models (e.g., `Forage`) and SQLAlchemy metadata. |
| `backend/schemas.py` | Pydantic request/response schemas (`ForageIn`, `ForageOut`, etc.). |
| `backend/requirements.txt` | Python dependencies for the backend. |
| `frontend/src/MapView.jsx` | Main React map UI with Leaflet, controls, and interactions. |
| `frontend/src/MapView.css` | Styles for the map and control panel components. |
| `frontend/src/api.js` | API client for calling FastAPI endpoints (ingest, data, predict). |
| `frontend/src/App.js` | App shell that mounts the `MapView` component. |
| `frontend/src/index.js` | React entry point; renders the app to the DOM. |
| `frontend/src/index.css` | Global CSS for the React app. |
| `models/poly_transform.pkl` | Polynomial feature transformer used in the ML pipeline. |
| `models/scaler.pkl` | Feature scaler fitted to training data. |
| `models/pca_transform.pkl` | PCA transformer for dimensionality reduction. |
| `models/knn_model.pkl` | KNN regressor used for grade prediction. |
| `data/` | Place CSVs here for ingestion (local file mode). |
| `README.md` | Project overview and instructions. |

## Features

- Fast ingestion pipeline with column auto-mapping (e.g., `x`/`x_coord`, `teneur`/`grade`)
- Robust CSV parsing with automatic separator detection
- Clean validation and numeric coercion; invalid rows are dropped with counts returned
- Pre-trained model pipeline for grade prediction
- Map-based visualization using Leaflet in the frontend

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 13+

## Environment Setup

Create `.env` at repository root with your database connection string. The backend reads `DATABASE_URL` via `backend/db.py` using `python-dotenv`.

Example (PostgreSQL):

```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/smart_mining
```

Ensure the target database exists and is reachable.

## Backend (FastAPI)

- Location: `backend/`
- Dependencies: `backend/requirements.txt`
- App entrypoint: `backend/main.py` (FastAPI app instance `app`)

Install and run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

On startup, the backend will:
- Create tables using SQLAlchemy metadata
- Attempt to load ML artifacts from `models/` and expose status at `GET /model/info`

### Key Endpoints

- `POST /ingest`
  - Ingest CSV data into the `forages` table.
  - Modes:
    - Multipart upload via `file`
    - Local file in `data/` via query `filename`
  - Response returns rows received/inserted/dropped and the source filename.

- `GET /data`
  - Returns recent rows (up to 1000) as `ForageOut` schema.

- `GET /model/info`
  - Reports whether each model artifact exists/loaded or any load errors.

- `POST /predict`
  - Body: `{ x_coord: number, y_coord: number, z_coord: number }`
  - Runs the pipeline (Poly → Scale → PCA → KNN) and returns `{ predicted_teneur, model }`.

## Frontend (React)

- Location: `frontend/`
- Scripts: `npm start`, `npm run build` (from `frontend/package.json`)

Install and run locally:

```bash
cd frontend
npm install
npm start
```

By default, CRA serves at `http://localhost:3000`. CORS is enabled in `backend/main.py` for localhost during development.

## Data Ingestion Workflow

1. Place a CSV under `data/` or prepare a CSV for upload via the UI.
2. Ensure columns can be auto-mapped. Required columns are:
   - `x_coord`, `y_coord`, `z_coord`, `teneur`
   - Optional: `id` (nullable; if omitted, DB will auto-generate)
3. Use the UI or call the API directly:

```bash
# Local file from data/
curl -X POST "http://localhost:8000/ingest?filename=your.csv"

# Multipart upload
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@/absolute/path/to/your.csv"
```

The service coerces numeric fields and drops invalid rows. The response details counts for transparency.

## Model Artifacts

The backend loads artifacts from `models/` on startup:

- `poly_transform.pkl`
- `scaler.pkl`
- `pca_transform.pkl`
- `knn_model.pkl`

If artifacts are missing or incompatible, `POST /predict` returns `503`, and `GET /model/info` explains what failed.

## Development Notes

- ORM and sessions: See `backend/db.py` and `backend/models.py`
- Schemas: See `backend/schemas.py`
- Frontend API client: See `frontend/src/api.js`
- Map UI: See `frontend/src/MapView.jsx` and styles in `frontend/src/MapView.css`

## Roadmap Ideas

- Docker Compose for one-command dev (API + DB + UI)
- Alembic migrations and seed scripts
- Authentication and role-based access
- File upload UI with progress and validation
- Model management: versioning and model registry integration

## Contributing

Issues and PRs are welcome. Please open an issue to discuss significant changes.

## License

Licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).
