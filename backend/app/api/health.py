from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import get_settings
import redis

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status