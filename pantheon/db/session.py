"""
Database session management using SQLModel.
PostgreSQL via Neon — no SQLite flags needed.
"""

from sqlmodel import create_engine, Session, SQLModel
from db.models import SignalRecord, PaperTrade, TokenRecord, ModelWeight
from config.settings import settings

engine = create_engine(settings.DATABASE_URL)


def SessionLocal():
    return Session(engine)


def init_db():
    SQLModel.metadata.create_all(engine)
    print("Database tables created.")


def get_db():
    with Session(engine) as session:
        yield session
