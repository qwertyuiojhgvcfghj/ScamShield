"""
auth.py - Authentication routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import RedirectResponse

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    RefreshToken,
    PasswordReset,
    PasswordResetConfirm,
    ChangePassword,
    VerifyEmail,
    ResendVerificationEmail,
    SendPhoneOTP,
    VerifyPhoneOTP,
    VerificationStatus,
    GoogleAuthRequest,
    GoogleTokenRequest,
    GitHubAuthRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.oauth_service import OAuthService
from app.core.dependencies import get_current_user, security
from app.core.config import settings
from app.db.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
async def register(data: UserRegister):
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Min 8 chars with uppercase, lowercase, and digit
    - **full_name**: User's full name
    - **phone**: Optional phone number
    """
    try:
        user, tokens = await AuthService.register_user(data)
        
        # Send verification email
        if user.verification_token:
            await EmailService.send_verification_email(
                user.email,
                user.verification_token,
                user.full_name
            )
        
        return {
            "status": "success",
            "message": "Account created successfully. Please check your email to verify your account.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
            },
            "tokens": tokens.model_dump()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=dict,
    summary="User login"
)
async def login(data: UserLogin):
    """
    Authenticate user and return JWT tokens.
    
    - **email**: Registered email address
    - **password**: Account password
    """
    try:
        user, tokens = await AuthService.authenticate_user(data)
        
        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
            },
            "tokens": tokens.model_dump()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/logout",
    summary="User logout"
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user by invalidating the current token.
    """
    await AuthService.logout(credentials.credentials)
    
    return {
        "status": "success",
        "message": "Logged out successfully"
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token"
)
async def refresh_token(data: RefreshToken):
    """
    Get new access token using refresh token.
    """
    try:
        tokens = await AuthService.refresh_tokens(data.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/forgot-password",
    summary="Request password reset"
)
async def forgot_password(data: PasswordReset):
    """
    Request a password reset email.
    """
    token = await AuthService.request_password_reset(data.email)
    
    # In production, send email with token
    # For demo, we just return success
    
    return {
        "status": "success",
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post(
    "/reset-password",
    summary="Reset password with token"
)
async def reset_password(data: PasswordResetConfirm):
    """
    Reset password using the token from email.
    """
    try:
        await AuthService.reset_password(data.token, data.new_password)
        
        return {
            "status": "success",
            "message": "Password reset successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/change-password",
    summary="Change password (logged in)"
)
async def change_password(
    data: ChangePassword,
    user: User = Depends(get_current_user)
):
    """
    Change password for logged-in user.
    """
    try:
        await AuthService.change_password(
            user,
            data.current_password,
            data.new_password
        )
        
        return {
            "status": "success",
            "message": "Password changed successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/verify-email/{token}",
    summary="Verify email address"
)
async def verify_email(token: str):
    """
    Verify email address using the token from email.
    """
    try:
        user = await AuthService.verify_email(token)
        
        # Send welcome email after successful verification
        await EmailService.send_welcome_email(user.email, user.full_name)
        
        return {
            "status": "success",
            "message": "Email verified successfully",
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/resend-verification",
    summary="Resend verification email"
)
async def resend_verification_email(data: ResendVerificationEmail):
    """
    Resend the email verification link.
    """
    try:
        token = await AuthService.resend_verification_email(data.email)
        
        if token:
            # Send verification email
            await EmailService.send_verification_email(data.email, token)
        
        # Always return success to prevent email enumeration
        return {
            "status": "success",
            "message": "If the email exists and is not verified, a new verification link has been sent"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/send-phone-otp",
    summary="Send phone verification OTP"
)
async def send_phone_otp(
    data: SendPhoneOTP,
    user: User = Depends(get_current_user)
):
    """
    Send OTP for phone number verification.
    The OTP will be sent to the user's email for security.
    """
    try:
        otp = await AuthService.send_phone_otp(str(user.id), data.phone)
        
        # Send OTP to user's email
        await EmailService.send_phone_otp_email(
            user.email, 
            otp, 
            data.phone, 
            user.full_name
        )
        
        return {
            "status": "success",
            "message": "Verification code has been sent to your email"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/verify-phone",
    summary="Verify phone number with OTP"
)
async def verify_phone_otp(
    data: VerifyPhoneOTP,
    user: User = Depends(get_current_user)
):
    """
    Verify phone number using the OTP sent to email.
    """
    try:
        verified_user = await AuthService.verify_phone_otp(
            str(user.id), 
            data.phone, 
            data.otp
        )
        
        return {
            "status": "success",
            "message": "Phone number verified successfully",
            "phone": verified_user.phone
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/verification-status",
    response_model=VerificationStatus,
    summary="Get verification status"
)
async def get_verification_status(
    user: User = Depends(get_current_user)
):
    """
    Get the current user's email and phone verification status.
    """
    status_data = await AuthService.get_verification_status(str(user.id))
    return VerificationStatus(**status_data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user"
)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role.value,
        is_verified=user.is_verified,
        is_phone_verified=user.is_phone_verified,
        created_at=user.created_at,
        last_login=user.last_login,
    )


# ============================================================
# GOOGLE OAUTH ROUTES
# ============================================================

@router.get(
    "/google",
    summary="Start Google OAuth flow"
)
async def google_auth():
    """
    Redirect to Google OAuth consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    auth_url = OAuthService.get_google_auth_url()
    return {"auth_url": auth_url}


@router.get(
    "/google/callback",
    summary="Google OAuth callback"
)
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(None, description="State parameter for CSRF protection"),
):
    """
    Handle Google OAuth callback.
    Redirects to frontend with tokens.
    """
    try:
        user, tokens = await OAuthService.authenticate_google(code)
        
        # Redirect to frontend with tokens in URL fragment
        redirect_url = (
            f"{settings.FRONTEND_URL}/login.html"
            f"#access_token={tokens.access_token}"
            f"&refresh_token={tokens.refresh_token}"
            f"&token_type=bearer"
        )
        
        return RedirectResponse(url=redirect_url)
        
    except ValueError as e:
        # Redirect to frontend with error
        error_url = f"{settings.FRONTEND_URL}/login.html?error={str(e)}"
        return RedirectResponse(url=error_url)


@router.post(
    "/google/token",
    response_model=dict,
    summary="Google OAuth with ID token"
)
async def google_token_auth(data: GoogleTokenRequest):
    """
    Authenticate using Google ID token from frontend.
    This is for the Google Sign-In button flow.
    
    - **id_token**: The ID token from Google Sign-In
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    try:
        user, tokens = await OAuthService.authenticate_google_token(data.id_token)
        
        return {
            "status": "success",
            "message": "Google login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role.value,
            },
            "tokens": tokens.model_dump()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/google/code",
    response_model=dict,
    summary="Google OAuth with authorization code"
)
async def google_code_auth(data: GoogleAuthRequest):
    """
    Authenticate using Google authorization code.
    This is for custom OAuth implementations.
    
    - **code**: The authorization code from Google
    - **redirect_uri**: Optional custom redirect URI
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )
    
    try:
        user, tokens = await OAuthService.authenticate_google(
            data.code, 
            data.redirect_uri
        )
        
        return {
            "status": "success",
            "message": "Google login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role.value,
            },
            "tokens": tokens.model_dump()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ============================================================
# GITHUB OAUTH ROUTES
# ============================================================

@router.get(
    "/github",
    summary="Start GitHub OAuth flow"
)
async def github_auth():
    """
    Get GitHub OAuth authorization URL.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured"
        )
    
    auth_url = OAuthService.get_github_auth_url()
    return {"auth_url": auth_url}


@router.get(
    "/github/callback",
    summary="GitHub OAuth callback"
)
async def github_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(None, description="State parameter for CSRF protection"),
):
    """
    Handle GitHub OAuth callback.
    Redirects to frontend with tokens.
    """
    try:
        user, tokens = await OAuthService.authenticate_github(code)
        
        # Redirect to frontend with tokens
        redirect_url = (
            f"{settings.FRONTEND_URL}/login.html"
            f"#access_token={tokens.access_token}"
            f"&refresh_token={tokens.refresh_token}"
            f"&token_type=bearer"
        )
        
        return RedirectResponse(url=redirect_url)
        
    except ValueError as e:
        error_url = f"{settings.FRONTEND_URL}/login.html?error={str(e)}"
        return RedirectResponse(url=error_url)


@router.post(
    "/github/code",
    response_model=dict,
    summary="GitHub OAuth with authorization code"
)
async def github_code_auth(data: GitHubAuthRequest):
    """
    Authenticate using GitHub authorization code.
    
    - **code**: The authorization code from GitHub
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured"
        )
    
    try:
        user, tokens = await OAuthService.authenticate_github(data.code)
        
        return {
            "status": "success",
            "message": "GitHub login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role.value,
            },
            "tokens": tokens.model_dump()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
