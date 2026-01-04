"""
Permission schemas for attribute-based authorization
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PermissionCheck(BaseModel):
    """Permission check request schema"""
    resource: str = Field(..., description="Resource name (e.g., 'users', 'orders')")
    action: str = Field(..., description="Action to perform (e.g., 'read', 'write', 'delete')")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Additional attributes for attribute-based checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource": "users",
                "action": "read",
                "attributes": {
                    "department": "IT",
                    "location": "US"
                }
            }
        }


class PermissionResponse(BaseModel):
    """Permission check response schema"""
    allowed: bool = Field(..., description="Whether the action is allowed")
    resource: str
    action: str
    message: Optional[str] = None


