from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# Create engine
engine = create_engine(DATABASE_URL)

# Base model for SQLAlchemy
Base = declarative_base()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI routes to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
