from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base

engine=create_engine(settings.DATABASE_URL,connect_args={"check_same_thread":False})

with engine.connect() as connection:
    connection.exec_driver_sql("PRAGMA journal_mode=WAL;")

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Provide a database session for dependency injection."""
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()