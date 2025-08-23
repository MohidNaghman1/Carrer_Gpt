# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This is the critical import for creating the Base
from sqlalchemy.ext.declarative import declarative_base

from core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# === THIS IS THE LINE THAT WAS LIKELY MISSING OR INCORRECT ===
# Create a Base class. All our ORM models will inherit from this class.
Base = declarative_base()
# =============================================================

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()