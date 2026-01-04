"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, permissions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])


