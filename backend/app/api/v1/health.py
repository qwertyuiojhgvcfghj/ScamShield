"""
health.py - Health check endpoints for monitoring
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import platform
import psutil
import asyncio

from app.core.config import settings
from app.db.mongodb import get_database


router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str  # healthy, degraded, unhealthy
    version: str
    timestamp: str
    uptime_seconds: float
    checks: Dict[str, Any]


class DetailedHealthStatus(HealthStatus):
    """Detailed health check with system info."""
    system: Dict[str, Any]
    dependencies: Dict[str, Any]


# Track server start time
_start_time = datetime.utcnow()


async def check_mongodb() -> Dict[str, Any]:
    """Check MongoDB connection health."""
    try:
        db = await get_database()
        # Ping the database
        await db.client.admin.command('ping')
        return {
            "status": "healthy",
            "latency_ms": 0  # Could measure actual latency
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_ai_providers() -> Dict[str, Any]:
    """Check AI provider availability."""
    providers = {}
    
    if settings.GROQ_API_KEY:
        providers["groq"] = "configured"
    else:
        providers["groq"] = "not_configured"
    
    if settings.GEMINI_API_KEY:
        providers["gemini"] = "configured"
    else:
        providers["gemini"] = "not_configured"
    
    if settings.DEEPSEEK_API_KEY:
        providers["deepseek"] = "configured"
    else:
        providers["deepseek"] = "not_configured"
    
    # Check if at least one provider is configured
    configured_count = sum(1 for v in providers.values() if v == "configured")
    
    return {
        "status": "healthy" if configured_count > 0 else "degraded",
        "providers": providers,
        "configured_count": configured_count
    }


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    try:
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "percent_used": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                "percent_used": psutil.disk_usage('/').percent
            }
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("", response_model=HealthStatus)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns minimal health status for load balancers and monitoring.
    """
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    
    # Quick MongoDB check
    mongo_status = await check_mongodb()
    
    # Determine overall status
    if mongo_status["status"] == "unhealthy":
        overall_status = "unhealthy"
    else:
        overall_status = "healthy"
    
    return HealthStatus(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime,
        checks={
            "database": mongo_status["status"]
        }
    )


@router.get("/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.
    
    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe.
    
    Returns 200 if the application is ready to accept traffic.
    """
    # Check if database is connected
    mongo_status = await check_mongodb()
    
    if mongo_status["status"] == "unhealthy":
        return {"status": "not_ready", "reason": "database_unavailable"}
    
    return {"status": "ready"}


@router.get("/detailed", response_model=DetailedHealthStatus)
async def detailed_health_check():
    """
    Detailed health check with system information.
    
    Includes:
    - Database status
    - AI provider status
    - System metrics (CPU, memory, disk)
    - Dependency versions
    """
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    
    # Run checks in parallel
    mongo_check, ai_check = await asyncio.gather(
        check_mongodb(),
        check_ai_providers()
    )
    
    # Determine overall status
    if mongo_check["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif ai_check["status"] == "degraded":
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return DetailedHealthStatus(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime,
        checks={
            "database": mongo_check,
            "ai_providers": ai_check
        },
        system=get_system_info(),
        dependencies={
            "fastapi": "0.128.0",
            "beanie": "1.26.0",
            "motor": "3.6.0"
        }
    )


@router.get("/metrics")
async def get_metrics():
    """
    Get application metrics for monitoring.
    
    Returns metrics in a format suitable for Prometheus or similar.
    """
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    
    try:
        db = await get_database()
        
        # Get collection stats
        users_count = await db["users"].count_documents({})
        scans_count = await db["scan_requests"].count_documents({})
        threats_count = await db["blocked_threats"].count_documents({})
        
    except Exception:
        users_count = scans_count = threats_count = -1
    
    return {
        "app_uptime_seconds": uptime,
        "app_version": settings.APP_VERSION,
        "database_users_total": users_count,
        "database_scans_total": scans_count,
        "database_threats_total": threats_count,
        "system_cpu_percent": psutil.cpu_percent(),
        "system_memory_percent": psutil.virtual_memory().percent,
        "system_disk_percent": psutil.disk_usage('/').percent
    }
