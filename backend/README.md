# SmartMining Backend

A FastAPI-based REST API for geospatial data management and phosphate content prediction in mining operations.

## 📋 Project Overview

This backend powers a geospatial intelligence interface for phosphate mining operations in Benguerir. It provides:
- Geospatial data storage and retrieval
- Machine learning predictions for phosphate content
- RESTful API for frontend integration

## 🚀 Features

- **Data Management**
  - CSV data ingestion
  - Efficient querying of geospatial data
  - Database persistence with PostgreSQL

- **Machine Learning**
  - Phosphate content prediction based on coordinates and depth
  - Model versioning and management
  - Support for multiple prediction models

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **ML**: scikit-learn for predictive modeling
- **Utilities**: Pydantic for data validation, pandas for data manipulation
- **Server**: Uvicorn (ASGI)

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Setup

Create a `.env` file in the backend directory with the following variables:

```env
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/smartmining
```

### Running the Application

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API documentation will be available at:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## 📚 API Endpoints

### Data Management

- `POST /ingest`
  - Upload CSV data or load from local file
  - Supports multipart form data or `?filename=` parameter
  - Returns ingestion statistics

- `GET /data`
  - Retrieve forage data (limited to 1000 most recent records)
  - Returns JSON array of forage items

### Machine Learning

- `GET /model/info`
  - Check model artifacts status
  - Returns information about loaded ML models

- `POST /predict`
  - Predict phosphate content for given coordinates
  - Request body: `{ "x_coord": float, "y_coord": float, "z_coord": float }`
  - Returns: `{ "predicted_teneur": float, "model": str }`


## Notes

- Database tables are created automatically in development
- For production, use Alembic for database migrations
- Ensure model artifacts are present in the `models/` directory
- The API is rate-limited and includes CORS middleware for security


## 📄 License

This project is licensed under the MIT License.
