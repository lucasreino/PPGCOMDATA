from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from app.config import settings

# Create engine with pool settings for reliability
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

def get_session() -> Generator[Session, None, None]:
    """Dependency generator to yield a database session.
    
    Ensures the session is closed automatically after the request.
    """
    with Session(engine) as session:
        yield session

def init_db() -> None:
    """Initialize database tables (alternative to Alembic migrations for local prototyping)."""
    SQLModel.metadata.create_all(engine)
