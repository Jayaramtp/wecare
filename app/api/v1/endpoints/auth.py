"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, TokenError
from app.schemas.auth import LoginRequest, RefreshTokenRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    User login endpoint
    
    Authenticates user with username/email and password.
    Returns access token and refresh token for persistent login.
    
    **Request Body:**
    - username: Username or email
    - password: User password
    - device_id: (Optional) Unique device identifier for persistent login
    
    **Response:**
    - access_token: JWT access token (expires in 30 minutes)
    - refresh_token: JWT refresh token (expires in 30 days)
    - token_type: "bearer"
    - expires_in: Access token expiration in seconds
    """
    try:
        token = AuthService.login(
            db=db,
            username=login_data.username,
            password=login_data.password,
            device_id=login_data.device_id
        )
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token endpoint
    
    Generates new access and refresh tokens using a valid refresh token.
    Enables persistent login on devices.
    
    **Request Body:**
    - refresh_token: Valid refresh token
    - device_id: (Optional) Device identifier
    
    **Response:**
    - access_token: New JWT access token
    - refresh_token: New JWT refresh token
    - token_type: "bearer"
    - expires_in: Access token expiration in seconds
    """
    try:
        token = AuthService.refresh_access_token(
            db=db,
            refresh_token=refresh_data.refresh_token,
            device_id=refresh_data.device_id
        )
        return token
    except (TokenError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    device_id: Optional[str] = Header(None, alias="X-Device-ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    User logout endpoint
    
    Invalidates refresh token for the current user.
    If device_id is provided, only logs out from that device.
    Otherwise, logs out from all devices.
    
    **Headers:**
    - Authorization: Bearer {access_token}
    - X-Device-ID: (Optional) Device identifier
    
    **Response:**
    - message: Logout confirmation
    """
    AuthService.logout(
        db=db,
        user_id=current_user.id,
        device_id=device_id
    )
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Returns information about the currently authenticated user.
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Response:**
    - User information (id, username, email, full_name, etc.)
    """
    return current_user


@router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify token endpoint
    
    Verifies if the current access token is valid.
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Response:**
    - valid: true
    - user_id: Current user ID
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username
    }



