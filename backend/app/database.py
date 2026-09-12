"""
Database configuration for RepoMind-AI.

Uses SQLite for local development and SQLAlchemy as the ORM.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "repomind.db"


# ---------------------------------------------------------
# DATABASE URL
# ---------------------------------------------------------

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ---------------------------------------------------------
# SQLALCHEMY ENGINE
# ---------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# ---------------------------------------------------------
# SESSION
# ---------------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------
# BASE MODEL
# ---------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

def init_db() -> None:
    """
    Create all database tables.
    """

    # Import models here so SQLAlchemy knows about them
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# DATABASE SESSION DEPENDENCY
# ---------------------------------------------------------

def get_db():
    """
    Provide a database session to FastAPI endpoints.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()