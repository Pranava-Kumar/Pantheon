"""
Database session management using SQLModel.
PostgreSQL via Neon — no SQLite flags needed.
"""

from sqlmodel import create_engine, Session, SQLModel
from pantheon.config.settings import settings

# Configure connection pooling for production workloads
# pool_size: Number of connections to keep open
# max_overflow: Additional connections allowed beyond pool_size
# pool_pre_ping: Test connections before use to detect stale connections
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)


def SessionLocal():
    return Session(engine)


def init_db():
    SQLModel.metadata.create_all(engine)
    print("Database tables created.")


def get_db():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
