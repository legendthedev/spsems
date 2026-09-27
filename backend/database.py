import os, sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from typing import Generator

from config import get_settings

settings = get_settings()

db_url = os.getenv("DATABASE_URL")
if db_url:
    # Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = db_url
    connect_args = {}
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    _db_file  = (
        settings.db_path if os.path.isabs(settings.db_path)
        else os.path.join(_base_dir, settings.db_path)
    )
    DATABASE_URL = f"sqlite:///{_db_file}"
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        if os.getenv("DATABASE_URL"):
            print("  Database connected -> Remote PostgreSQL")
        else:
            print(f"  SQLite connected -> {_db_file}")
        return True
    except Exception as e:
        print(f"  Database connection failed: {e}", file=sys.stderr)
        return False
