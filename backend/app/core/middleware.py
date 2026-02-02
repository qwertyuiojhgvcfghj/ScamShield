"""
middleware.py - Custom middleware for rate limiting, logging, and security
"""

import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Callable, Dict, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

from app.core.config import settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scamshield")


# ============================================================
# RATE LIMITING MIDDLEWARE
# ============================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    Uses in-memory storage (for single instance) or can be extended to Redis.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        whitelist_paths: list = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.whitelist_paths = whitelist_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
        
        # In-memory storage: {ip: [(timestamp, count), ...]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        
        # Cleanup task
        self._cleanup_lock = asyncio.Lock()
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request, considering proxies."""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, ip: str):
        """Remove expired request records."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        # Clean minute window
        self.minute_requests[ip] = [
            ts for ts in self.minute_requests[ip] if ts > minute_ago
        ]
        
        # Clean hour window
        self.hour_requests[ip] = [
            ts for ts in self.hour_requests[ip] if ts > hour_ago
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for whitelisted paths
        if any(request.url.path.startswith(path) for path in self.whitelist_paths):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        now = time.time()
        
        # Cleanup old requests
        self._cleanup_old_requests(client_ip)
        
        # Check minute limit
        if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60,
                    "limit": self.requests_per_minute,
                    "window": "minute"
                },
                headers={"Retry-After": "60"}
            )
        
        # Check hour limit
        if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Hourly rate limit exceeded. Please try again later.",
                    "retry_after": 3600,
                    "limit": self.requests_per_hour,
                    "window": "hour"
                },
                headers={"Retry-After": "3600"}
            )
        
        # Record this request
        self.minute_requests[client_ip].append(now)
        self.hour_requests[client_ip].append(now)
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.minute_requests[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        
        return response


# ============================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests for debugging and monitoring.
    """
    
    def __init__(self, app, log_body: bool = False, exclude_paths: list = None):
        super().__init__(app)
        self.log_body = log_body
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Get request details
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                   request.headers.get("X-Real-IP") or \
                   (request.client.host if request.client else "unknown")
        
        # Generate request ID
        request_id = f"{int(start_time * 1000)}-{id(request)}"
        
        # Log request
        logger.info(
            f"[{request_id}] --> {request.method} {request.url.path} "
            f"| Client: {client_ip} "
            f"| User-Agent: {request.headers.get('User-Agent', 'unknown')[:50]}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] <-- {response.status_code} "
                f"| Duration: {duration:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] !!! ERROR: {str(e)} "
                f"| Duration: {duration:.3f}s"
            )
            raise


# ============================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


# ============================================================
# API KEY AUTHENTICATION MIDDLEWARE
# ============================================================

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate requests using API keys.
    Checks X-API-Key header for programmatic access.
    """
    
    def __init__(self, app, require_auth_paths: list = None):
        super().__init__(app)
        # Paths that require API key authentication (if no Bearer token)
        self.require_auth_paths = require_auth_paths or ["/api/v1/scans"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if path requires authentication
        requires_auth = any(
            request.url.path.startswith(path) 
            for path in self.require_auth_paths
        )
        
        if not requires_auth:
            return await call_next(request)
        
        # Check for Authorization header (JWT takes priority)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return await call_next(request)
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Validate API key (will be done in dependency)
            # Just pass through here, actual validation in endpoint
            return await call_next(request)
        
        # No authentication provided for protected route
        # Let the endpoint handle the 401 response
        return await call_next(request)
