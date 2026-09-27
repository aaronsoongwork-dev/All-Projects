"""
Database configuration and session management for ShipCheck SQLite persistence.
"""
import os
from pathlib import Path
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session

DB_PATH = Path(__file__).resolve().parent.parent / "shipcheck.db"
raw_db_url = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Normalize postgres:// scheme for SQLAlchemy
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
else:
    # Supabase Postgres connection pooling
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )



def init_db(target_engine=None) -> None:
    """Initializes database tables if they do not exist."""
    import api.models  # noqa: F401
    SQLModel.metadata.create_all(target_engine or engine)


# Initialize default database tables
init_db()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency providing a database session."""
    with Session(engine) as session:
        yield session

