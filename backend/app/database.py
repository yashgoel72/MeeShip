from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Configure engine with connection pooling for production
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,         # Max number of connections
    max_overflow=10,     # Additional connections if pool is full
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Don't log SQL in production
)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session