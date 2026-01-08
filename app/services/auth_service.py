"""
Authentication service
"""
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import json

from app.models.user import User
from app.models.user_resource_permission import UserResourcePermission
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.config import settings
from app.core.exceptions import AuthenticationError, TokenError
from app.schemas.auth import Token, TokenData


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username/email and password
        
        Args:
            db: Database session
            username: Username or email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
        
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def login(db: Session, username: str, password: str, device_id: Optional[str] = None) -> Token:
        """
        Perform user login and generate tokens
        
        Args:
            db: Database session
            username: Username or email
            password: Plain text password
            device_id: Optional device identifier for persistent login
            
        Returns:
            Token object with access and refresh tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        user = AuthService.authenticate_user(db, username, password)
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        # Update last login and device_id
        from datetime import datetime
        user.last_login = datetime.utcnow()
        if device_id:
            user.device_id = device_id
        
        # Create tokens
        token_data = TokenData(
            user_id=user.id,
            username=user.username,
            email=user.email,
            is_superuser=user.is_superuser
        )
        
        access_token = create_access_token(data=token_data.model_dump())
        refresh_token = create_refresh_token(data={"user_id": user.id, "username": user.username})
        
        # Store refresh token in database for device-based persistent login
        user.refresh_token = refresh_token
        
        db.commit()
        db.refresh(user)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str, device_id: Optional[str] = None) -> Token:
        """
        Refresh access token using refresh token
        
        Args:
            db: Database session
            refresh_token: Refresh token string
            device_id: Optional device identifier
            
        Returns:
            Token object with new access and refresh tokens
            
        Raises:
            TokenError: If refresh token is invalid
            AuthenticationError: If user not found or inactive
        """
        try:
            # Verify refresh token
            payload = verify_token(refresh_token, token_type="refresh")
            user_id = payload.get("user_id")
            username = payload.get("username")
            
            if not user_id or not username:
                raise TokenError("Invalid token payload")
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise AuthenticationError("User not found")
            
            if not user.is_active:
                raise AuthenticationError("User account is inactive")
            
            # Verify device_id if provided (for persistent login)
            if device_id and user.device_id and user.device_id != device_id:
                # Allow refresh if device_id matches or if no device_id was set
                pass
            
            # Verify stored refresh token matches (for security)
            if user.refresh_token != refresh_token:
                raise TokenError("Refresh token mismatch")
            
            # Create new tokens
            token_data = TokenData(
                user_id=user.id,
                username=user.username,
                email=user.email,
                is_superuser=user.is_superuser
            )
            
            new_access_token = create_access_token(data=token_data.model_dump())
            new_refresh_token = create_refresh_token(data={"user_id": user.id, "username": user.username})
            
            # Update refresh token in database
            user.refresh_token = new_refresh_token
            if device_id:
                user.device_id = device_id
            
            db.commit()
            
            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except Exception as e:
            if isinstance(e, (TokenError, AuthenticationError)):
                raise
            raise TokenError(f"Token refresh failed: {str(e)}")
    
    @staticmethod
    def logout(db: Session, user_id: int, device_id: Optional[str] = None) -> bool:
        """
        Logout user by invalidating refresh token
        
        Args:
            db: Database session
            user_id: User ID
            device_id: Optional device identifier
            
        Returns:
            True if logout successful
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Clear refresh token (device-specific logout)
            if device_id and user.device_id == device_id:
                user.refresh_token = None
                user.device_id = None
            elif not device_id:
                # Logout from all devices
                user.refresh_token = None
                user.device_id = None
            
            db.commit()
        
        return True
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        Get current user from access token
        
        Args:
            db: Database session
            token: JWT access token
            
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            payload = verify_token(token, token_type="access")
            user_id = payload.get("user_id")
            
            if not user_id:
                return None
            
            user = db.query(User).filter(User.id == user_id).first()
            
            if user and user.is_active:
                return user
            
            return None
            
        except Exception:
            return None



