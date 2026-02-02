# Schemas package
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenPayload,
    PasswordReset,
    PasswordResetConfirm,
)
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.schemas.scan import (
    ScanInput,
    ScanResponse,
    ScanHistoryItem,
    ScanDetail,
)
from app.schemas.threat import (
    ThreatResponse,
    ThreatReport,
    ThreatListResponse,
)
from app.schemas.subscription import (
    PlanResponse,
    SubscriptionResponse,
    SubscribeRequest,
)
from app.schemas.analytics import (
    DashboardStats,
    TrendData,
    ScamTypeBreakdown,
)

__all__ = [
    # Auth
    "UserRegister", "UserLogin", "Token", "TokenPayload",
    "PasswordReset", "PasswordResetConfirm",
    # User
    "UserResponse", "UserUpdate", "UserSettingsResponse", "UserSettingsUpdate",
    # Scan
    "ScanInput", "ScanResponse", "ScanHistoryItem", "ScanDetail",
    # Threat
    "ThreatResponse", "ThreatReport", "ThreatListResponse",
    # Subscription
    "PlanResponse", "SubscriptionResponse", "SubscribeRequest",
    # Analytics
    "DashboardStats", "TrendData", "ScamTypeBreakdown",
]
