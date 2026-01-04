import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Create database tables directly.
    
    NOTE: This function is kept for development/testing purposes.
    For production, use Alembic migrations instead:
        alembic upgrade head
    
    This ensures schema changes can be made without losing data.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session