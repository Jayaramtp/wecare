"""
Permission endpoints for attribute-based authorization
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthorizationError
from app.schemas.permission import PermissionCheck, PermissionResponse
from app.services.permission_service import PermissionService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/check", response_model=PermissionResponse, status_code=status.HTTP_200_OK)
async def check_permission(
    permission_check: PermissionCheck,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check permission endpoint
    
    Checks if the current user has permission to perform an action on a resource.
    Supports attribute-based access control (ABAC).
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Request Body:**
    - resource: Resource name (e.g., "users", "orders")
    - action: Action to perform (e.g., "read", "write", "delete")
    - attributes: (Optional) Dictionary of attributes for ABAC checks
    
    **Response:**
    - allowed: Boolean indicating if permission is granted
    - resource: Resource name
    - action: Action name
    - message: Optional message
    
    **Example:**
    ```json
    {
        "resource": "users",
        "action": "read",
        "attributes": {
            "department": "IT",
            "location": "US"
        }
    }
    ```
    """
    try:
        allowed = PermissionService.check_permission(
            db=db,
            user=current_user,
            resource=permission_check.resource,
            action=permission_check.action,
            attributes=permission_check.attributes
        )
        
        return PermissionResponse(
            allowed=allowed,
            resource=permission_check.resource,
            action=permission_check.action,
            message="Permission granted" if allowed else "Permission denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking permission: {str(e)}"
        )


@router.get("/my-permissions", status_code=status.HTTP_200_OK)
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all permissions for current user
    
    Returns a list of all permissions granted to the current user.
    Superusers will see a wildcard permission.
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Response:**
    - permissions: List of permission objects
    """
    permissions = PermissionService.get_user_permissions(db=db, user=current_user)
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_superuser": current_user.is_superuser,
        "permissions": permissions
    }


