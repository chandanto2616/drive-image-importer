"""
Shared database module - used by both API and Worker services
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.config import DATABASE_URL
from shared.models import Base

# Database setup - shared by both services (Postgres-focused; no SQLite hacks)
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    """Create all tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Get a database session"""
    return SessionLocal()