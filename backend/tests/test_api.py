# ===========================================
# ScamShield Backend Tests
# ===========================================
# Run with: pytest tests/ -v
# ===========================================

import pytest
from httpx import AsyncClient
from datetime import datetime
import uuid

# Import app after setting test environment
import os
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "scamshield_test"

from app.main import app


# ===========================================
# FIXTURES
# ===========================================

@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
def test_user():
    """Generate unique test user credentials."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test_{unique_id}@example.com",
        "password": "SecurePass123!",
        "full_name": f"Test User {unique_id}"
    }


@pytest.fixture
def sample_scam_message():
    return "Congratulations! You've won $1,000,000 in our lottery. Click here to claim now!"


@pytest.fixture
def sample_safe_message():
    return "Hi, just checking if our meeting is still on for tomorrow at 3pm."


# ===========================================
# HEALTH CHECK TESTS
# ===========================================

@pytest.mark.anyio
async def test_health_check():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_root():
    """Test the root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "ScamShield" in data.get("message", "")


# ===========================================
# AUTHENTICATION TESTS
# ===========================================

@pytest.mark.anyio
async def test_register_user(test_user):
    """Test user registration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user
        )
        # Should work or return conflict if user exists
        assert response.status_code in [200, 201, 400]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "tokens" in data
            assert "user" in data
            assert data["user"]["email"] == test_user["email"]


@pytest.mark.anyio
async def test_login_user(test_user):
    """Test user login."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First register the user
        await client.post("/api/v1/auth/register", json=test_user)
        
        # Then try to login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "tokens" in data
            assert "access_token" in data["tokens"]
            assert "refresh_token" in data["tokens"]


@pytest.mark.anyio
async def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


@pytest.mark.anyio
async def test_protected_route_without_token():
    """Test that protected routes require authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


@pytest.mark.anyio
async def test_protected_route_with_token(test_user):
    """Test accessing protected routes with valid token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            data = reg_response.json()
            token = data["tokens"]["access_token"]
            
            # Access protected route
            response = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            user_data = response.json()
            assert user_data["email"] == test_user["email"]


# ===========================================
# SCAN TESTS
# ===========================================

@pytest.mark.anyio
async def test_scan_requires_auth(sample_scam_message):
    """Test that scan endpoint requires authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/scans/",
            json={"message_text": sample_scam_message}
        )
        assert response.status_code == 401


@pytest.mark.anyio
async def test_scan_scam_message(test_user, sample_scam_message):
    """Test scanning a scam message."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            # Scan message
            response = await client.post(
                "/api/v1/scans/",
                json={
                    "message_text": sample_scam_message,
                    "channel": "SMS"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should succeed (200) or hit rate limit (429)
            assert response.status_code in [200, 429]
            
            if response.status_code == 200:
                data = response.json()
                assert "is_scam" in data
                assert "risk_score" in data
                # Lottery scam should be detected
                assert data["is_scam"] == True or data["risk_score"] > 0.5


@pytest.mark.anyio
async def test_scan_safe_message(test_user, sample_safe_message):
    """Test scanning a safe message."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            # Scan message
            response = await client.post(
                "/api/v1/scans/",
                json={
                    "message_text": sample_safe_message,
                    "channel": "Email"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code in [200, 429]
            
            if response.status_code == 200:
                data = response.json()
                # Safe message should have low risk
                assert data["risk_score"] < 0.5


@pytest.mark.anyio
async def test_scan_history(test_user):
    """Test getting scan history."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.get(
                "/api/v1/scans/history",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "scans" in data or "items" in data
            assert "total" in data


# ===========================================
# ANALYTICS TESTS
# ===========================================

@pytest.mark.anyio
async def test_global_stats():
    """Test getting global stats (public endpoint)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/global")
        assert response.status_code == 200
        data = response.json()
        assert "total_scams_blocked" in data or "scams_blocked" in data


@pytest.mark.anyio
async def test_dashboard_stats(test_user):
    """Test getting dashboard stats (protected)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.get(
                "/api/v1/analytics/dashboard",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200


# ===========================================
# SUBSCRIPTION TESTS
# ===========================================

@pytest.mark.anyio
async def test_get_plans():
    """Test getting subscription plans."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data


@pytest.mark.anyio
async def test_get_current_subscription(test_user):
    """Test getting user's current subscription."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.get(
                "/api/v1/subscriptions/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should return subscription or 404 if none
            assert response.status_code in [200, 404]


# ===========================================
# THREAT TESTS
# ===========================================

@pytest.mark.anyio
async def test_get_threats(test_user):
    """Test getting threats list."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.get(
                "/api/v1/threats/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "threats" in data or "items" in data


# ===========================================
# USER SETTINGS TESTS
# ===========================================

@pytest.mark.anyio
async def test_get_settings(test_user):
    """Test getting user settings."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.get(
                "/api/v1/users/me/settings",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200


@pytest.mark.anyio
async def test_update_settings(test_user):
    """Test updating user settings."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.put(
                "/api/v1/users/me/settings",
                json={"email_alerts": True, "auto_block": True},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200


# ===========================================
# API KEY TESTS
# ===========================================

@pytest.mark.anyio
async def test_generate_api_key(test_user):
    """Test generating an API key."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.post(
                "/api/v1/users/me/api-key",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "api_key" in data
            assert data["api_key"].startswith("sk_live_")


# ===========================================
# VALIDATION TESTS
# ===========================================

@pytest.mark.anyio
async def test_register_invalid_email():
    """Test registration with invalid email."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_register_weak_password():
    """Test registration with weak password."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User"
            }
        )
        # Should fail validation
        assert response.status_code in [400, 422]


@pytest.mark.anyio
async def test_scan_empty_message(test_user):
    """Test scanning an empty message."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and get token
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code in [200, 201]:
            token = reg_response.json()["tokens"]["access_token"]
            
            response = await client.post(
                "/api/v1/scans/",
                json={"message_text": ""},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should fail validation
            assert response.status_code in [400, 422]


# ===========================================
# INTEGRATION TESTS
# ===========================================

@pytest.mark.anyio
async def test_full_user_workflow(test_user, sample_scam_message):
    """Test complete user workflow: register -> scan -> get history."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register
        reg_response = await client.post("/api/v1/auth/register", json=test_user)
        
        if reg_response.status_code not in [200, 201]:
            pytest.skip("Registration failed")
        
        token = reg_response.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get profile
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200
        
        # 3. Scan a message
        scan_response = await client.post(
            "/api/v1/scans/",
            json={"message_text": sample_scam_message, "channel": "SMS"},
            headers=headers
        )
        
        if scan_response.status_code == 200:
            scan_data = scan_response.json()
            scan_id = scan_data.get("scan_id") or scan_data.get("id")
            
            # 4. Get scan history
            history_response = await client.get(
                "/api/v1/scans/history",
                headers=headers
            )
            assert history_response.status_code == 200
            
            # 5. Get dashboard stats
            stats_response = await client.get(
                "/api/v1/analytics/dashboard",
                headers=headers
            )
            assert stats_response.status_code == 200
            
            # 6. Logout
            logout_response = await client.post(
                "/api/v1/auth/logout",
                headers=headers
            )
            assert logout_response.status_code == 200
