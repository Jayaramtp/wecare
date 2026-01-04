"""
Permission service for attribute-based authorization
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import json

from app.models.user import User
from app.models.user_resource_permission import UserResourcePermission
from app.core.exceptions import AuthorizationError


class PermissionService:
    """Service for attribute-based authorization operations"""
    
    @staticmethod
    def check_permission(
        db: Session,
        user: User,
        resource: str,
        action: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has permission to perform action on resource
        
        This implements attribute-based access control (ABAC) where permissions
        can be restricted based on attributes/conditions.
        
        Args:
            db: Database session
            user: User object
            resource: Resource name (e.g., "users", "orders")
            action: Action to perform (e.g., "read", "write", "delete")
            attributes: Optional attributes for attribute-based checks
            
        Returns:
            True if permission is granted, False otherwise
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True
        
        # Get all active permissions for the user and resource
        permissions = db.query(UserResourcePermission).filter(
            UserResourcePermission.user_id == user.id,
            UserResourcePermission.resource == resource,
            UserResourcePermission.action == action,
            UserResourcePermission.is_active == True
        ).all()
        
        if not permissions:
            return False
        
        # If no attributes specified, check if any permission exists
        if not attributes:
            return len(permissions) > 0
        
        # Check attribute-based permissions
        for permission in permissions:
            if not permission.attributes:
                # Permission without attributes allows all
                return True
            
            try:
                # Parse attributes from JSON string
                permission_attrs = json.loads(permission.attributes) if isinstance(permission.attributes, str) else permission.attributes
                
                # Check if all permission attributes match request attributes
                if PermissionService._match_attributes(permission_attrs, attributes):
                    return True
                    
            except (json.JSONDecodeError, TypeError):
                # Invalid JSON, skip this permission
                continue
        
        return False
    
    @staticmethod
    def _match_attributes(permission_attrs: Dict[str, Any], request_attrs: Dict[str, Any]) -> bool:
        """
        Match permission attributes with request attributes
        
        Args:
            permission_attrs: Attributes defined in permission
            request_attrs: Attributes from request
            
        Returns:
            True if attributes match, False otherwise
        """
        for key, value in permission_attrs.items():
            if key not in request_attrs:
                return False
            
            request_value = request_attrs[key]
            
            # Handle list values (e.g., ["IT", "HR"] means user must be in IT or HR)
            if isinstance(value, list):
                if request_value not in value:
                    return False
            # Handle exact match
            elif value != request_value:
                return False
        
        return True
    
    @staticmethod
    def get_user_permissions(db: Session, user: User) -> List[Dict[str, Any]]:
        """
        Get all permissions for a user
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            List of permission dictionaries
        """
        if user.is_superuser:
            return [{"resource": "*", "action": "*", "attributes": None}]
        
        permissions = db.query(UserResourcePermission).filter(
            UserResourcePermission.user_id == user.id,
            UserResourcePermission.is_active == True
        ).all()
        
        result = []
        for perm in permissions:
            attrs = None
            if perm.attributes:
                try:
                    attrs = json.loads(perm.attributes) if isinstance(perm.attributes, str) else perm.attributes
                except (json.JSONDecodeError, TypeError):
                    attrs = None
            
            result.append({
                "resource": perm.resource,
                "action": perm.action,
                "attributes": attrs
            })
        
        return result
    
    @staticmethod
    def require_permission(
        db: Session,
        user: User,
        resource: str,
        action: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Require permission or raise AuthorizationError
        
        Args:
            db: Database session
            user: User object
            resource: Resource name
            action: Action to perform
            attributes: Optional attributes
            
        Raises:
            AuthorizationError: If permission is not granted
        """
        if not PermissionService.check_permission(db, user, resource, action, attributes):
            raise AuthorizationError(
                f"Permission denied: {action} on {resource}"
            )


