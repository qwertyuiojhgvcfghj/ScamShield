"""
oauth_service.py - OAuth authentication service for Google and GitHub

Handles OAuth2 authentication flow:
1. Generate authorization URLs
2. Exchange codes for tokens
3. Fetch user info from providers
4. Create/update users in database
"""

import httpx
from typing import Optional, Tuple
from datetime import datetime

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.db.models.user import User, AuthProvider
from app.db.models.user_settings import UserSettings
from app.db.models.subscription import Subscription, PlanTier, SubscriptionStatus
from app.schemas.auth import Token, OAuthUserInfo


# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

# GitHub OAuth endpoints
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class OAuthService:
    """
    Service for handling OAuth authentication.
    """
    
    # ============================================================
    # GOOGLE OAUTH
    # ============================================================
    
    @staticmethod
    def get_google_auth_url(state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        
        if state:
            params["state"] = state
            
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query_string}"
    
    @staticmethod
    async def exchange_google_code(code: str, redirect_uri: Optional[str] = None) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Google callback
            redirect_uri: Optional custom redirect URI
            
        Returns:
            Token response from Google
            
        Raises:
            ValueError: If token exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri or settings.GOOGLE_REDIRECT_URI,
                },
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(f"Failed to exchange code: {error_data.get('error_description', 'Unknown error')}")
                
            return response.json()
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> OAuthUserInfo:
        """
        Fetch user info from Google.
        
        Args:
            access_token: Google access token
            
        Returns:
            OAuthUserInfo object
            
        Raises:
            ValueError: If fetching user info fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to fetch user info from Google")
                
            data = response.json()
            
            return OAuthUserInfo(
                email=data["email"],
                full_name=data.get("name", ""),
                avatar_url=data.get("picture"),
                oauth_id=data["id"],
                provider="google",
            )
    
    @staticmethod
    async def verify_google_id_token(id_token: str) -> OAuthUserInfo:
        """
        Verify Google ID token (for frontend flow).
        
        Args:
            id_token: Google ID token from frontend
            
        Returns:
            OAuthUserInfo object
            
        Raises:
            ValueError: If token verification fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GOOGLE_TOKEN_INFO_URL}?id_token={id_token}"
            )
            
            if response.status_code != 200:
                raise ValueError("Invalid Google ID token")
                
            data = response.json()
            
            # Verify the token is for our app
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise ValueError("Token was not issued for this application")
            
            return OAuthUserInfo(
                email=data["email"],
                full_name=data.get("name", ""),
                avatar_url=data.get("picture"),
                oauth_id=data["sub"],
                provider="google",
            )
    
    @staticmethod
    async def authenticate_google(code: str, redirect_uri: Optional[str] = None) -> Tuple[User, Token]:
        """
        Complete Google OAuth authentication flow.
        
        Args:
            code: Authorization code from Google
            redirect_uri: Optional custom redirect URI
            
        Returns:
            Tuple of (User, Token)
        """
        # Exchange code for tokens
        token_data = await OAuthService.exchange_google_code(code, redirect_uri)
        
        # Get user info
        user_info = await OAuthService.get_google_user_info(token_data["access_token"])
        
        # Create or update user
        user, tokens = await OAuthService._get_or_create_oauth_user(user_info)
        
        return user, tokens
    
    @staticmethod
    async def authenticate_google_token(id_token: str) -> Tuple[User, Token]:
        """
        Authenticate using Google ID token (frontend flow).
        
        Args:
            id_token: Google ID token from frontend
            
        Returns:
            Tuple of (User, Token)
        """
        # Verify token and get user info
        user_info = await OAuthService.verify_google_id_token(id_token)
        
        # Create or update user
        user, tokens = await OAuthService._get_or_create_oauth_user(user_info)
        
        return user, tokens
    
    # ============================================================
    # GITHUB OAUTH
    # ============================================================
    
    @staticmethod
    def get_github_auth_url(state: Optional[str] = None) -> str:
        """
        Generate GitHub OAuth authorization URL.
        """
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "user:email",
        }
        
        if state:
            params["state"] = state
            
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{GITHUB_AUTH_URL}?{query_string}"
    
    @staticmethod
    async def exchange_github_code(code: str) -> dict:
        """
        Exchange authorization code for access token.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to exchange code with GitHub")
                
            data = response.json()
            
            if "error" in data:
                raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")
                
            return data
    
    @staticmethod
    async def get_github_user_info(access_token: str) -> OAuthUserInfo:
        """
        Fetch user info from GitHub.
        """
        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                GITHUB_USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to fetch user info from GitHub")
                
            user_data = response.json()
            
            # Get user emails (email might be private)
            email = user_data.get("email")
            if not email:
                emails_response = await client.get(
                    GITHUB_EMAILS_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    # Get primary email
                    for e in emails:
                        if e.get("primary"):
                            email = e["email"]
                            break
                    # Fallback to first verified email
                    if not email:
                        for e in emails:
                            if e.get("verified"):
                                email = e["email"]
                                break
            
            if not email:
                raise ValueError("Could not get email from GitHub")
            
            return OAuthUserInfo(
                email=email,
                full_name=user_data.get("name") or user_data.get("login", ""),
                avatar_url=user_data.get("avatar_url"),
                oauth_id=str(user_data["id"]),
                provider="github",
            )
    
    @staticmethod
    async def authenticate_github(code: str) -> Tuple[User, Token]:
        """
        Complete GitHub OAuth authentication flow.
        """
        # Exchange code for token
        token_data = await OAuthService.exchange_github_code(code)
        
        # Get user info
        user_info = await OAuthService.get_github_user_info(token_data["access_token"])
        
        # Create or update user
        user, tokens = await OAuthService._get_or_create_oauth_user(user_info)
        
        return user, tokens
    
    # ============================================================
    # SHARED METHODS
    # ============================================================
    
    @staticmethod
    async def _get_or_create_oauth_user(user_info: OAuthUserInfo) -> Tuple[User, Token]:
        """
        Get existing user or create new one from OAuth info.
        
        Args:
            user_info: OAuth user info
            
        Returns:
            Tuple of (User, Token)
        """
        provider = AuthProvider.GOOGLE if user_info.provider == "google" else AuthProvider.GITHUB
        
        # Check if user exists by OAuth ID
        user = await User.find_one(
            User.oauth_id == user_info.oauth_id,
            User.auth_provider == provider
        )
        
        if not user:
            # Check if user exists with same email
            user = await User.find_one(User.email == user_info.email.lower())
            
            if user:
                # Link existing account to OAuth
                user.oauth_id = user_info.oauth_id
                user.auth_provider = provider
                if user_info.avatar_url:
                    user.avatar_url = user_info.avatar_url
                user.is_verified = True  # OAuth emails are verified
                user.update_timestamp()
                await user.save()
            else:
                # Create new user
                user = User(
                    email=user_info.email.lower(),
                    password_hash=None,  # OAuth users don't have password
                    full_name=user_info.full_name or "",
                    avatar_url=user_info.avatar_url,
                    auth_provider=provider,
                    oauth_id=user_info.oauth_id,
                    is_verified=True,  # OAuth emails are pre-verified
                )
                await user.insert()
                
                # Create default settings
                user_settings = UserSettings(user_id=str(user.id))
                await user_settings.insert()
                
                # Create free subscription
                subscription = Subscription(
                    user_id=str(user.id),
                    plan_id="free",
                    plan_tier=PlanTier.FREE,
                    status=SubscriptionStatus.ACTIVE,
                )
                await subscription.insert()
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.save()
        
        # Generate tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        
        tokens = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return user, tokens
