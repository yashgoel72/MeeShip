"""
Meesho Image Optimizer API

Main FastAPI application module.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import Settings
from app.routers import auth
from app.routers import images
from app.routers import dashboard
from app.routers import payment
from app.routers import kinde_auth

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info("Starting Meesho Image Optimizer API...")
    yield
    # Shutdown
    logger.info("Shutting down Meesho Image Optimizer API...")


app = FastAPI(
    title="Meesho Image Optimizer API",
    description="Image optimization service for Meesho sellers",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration - Allow frontend origins
allowed_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev port
    "http://localhost:3001",  # Current dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Add production frontend URL from environment
if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
    allowed_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(images.router)
app.include_router(payment.router, prefix="/api")
app.include_router(kinde_auth.router)  # Kinde OAuth routes


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/db", tags=["Health"])
async def health_db(db: AsyncSession = Depends(get_db)):
    """Database health check endpoint."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "db": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "db": str(e)}


@app.get("/storage-health", tags=["Health"])
async def storage_health():
    """S3 storage health check endpoint - uploads test file and returns presigned URL."""
    try:
        from app.services.s3_storage import upload_to_s3, generate_presigned_url
        from app.config import get_settings
        import uuid
        from datetime import datetime, timezone
        
        settings = get_settings()
        
        if not settings.S3_ENABLED:
            return {
                "status": "disabled",
                "message": "S3 storage is not enabled"
            }
        
        # Create test data
        test_content = f"Storage health check - {datetime.now(timezone.utc).isoformat()}".encode('utf-8')
        test_filename = f"health_check_{uuid.uuid4().hex[:8]}.txt"
        
        # Upload test file
        object_key = await upload_to_s3(
            test_content,
            filename=test_filename,
            content_type="text/plain"
        )
        
        # Generate presigned URL
        presigned_result = await generate_presigned_url(object_key, expires_in=60)
        
        return {
            "status": "healthy",
            "bucket": settings.S3_BUCKET,
            "endpoint": settings.S3_ENDPOINT,
            "test_object_key": object_key,
            "test_url": presigned_result["signed_url"],
            "expires_at": presigned_result["expires_at"],
            "message": "S3 storage is operational"
        }
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "S3 storage check failed"
        }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Meesho Image Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }