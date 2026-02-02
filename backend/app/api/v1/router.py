"""
router.py - API v1 router combining all routes
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.scans import router as scans_router
from app.api.v1.threats import router as threats_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.admin import router as admin_router
from app.api.v1.contact import router as contact_router
from app.api.v1.health import router as health_router
from app.api.v1.export import router as export_router


# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(scans_router)
api_router.include_router(threats_router)
api_router.include_router(subscriptions_router)
api_router.include_router(analytics_router)
api_router.include_router(admin_router)
api_router.include_router(contact_router)
api_router.include_router(health_router)
api_router.include_router(export_router)
