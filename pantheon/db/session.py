from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
from config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite only
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
