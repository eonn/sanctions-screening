"""
Database connection and session management.

Author: Eon (Himanshu Shekhar)
Email: himanshu.shekhar@example.com
GitHub: https://github.com/eon-himanshu
Created: 2024
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import settings
from app.models.database import Base

# Create database engine
if settings.database_url.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL/MySQL configuration for production
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """
    Get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with sample data."""
    from app.services.data_loader import load_sample_sanctions_data
    
    # Create tables
    create_tables()
    
    # Load sample data if database is empty
    db = SessionLocal()
    try:
        from app.models.database import SanctionsList
        count = db.query(SanctionsList).count()
        if count == 0:
            load_sample_sanctions_data(db)
            print("Sample sanctions data loaded successfully.")
        else:
            print(f"Database already contains {count} sanctions entries.")
    finally:
        db.close() 