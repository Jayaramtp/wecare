"""
User Resource Permission model for attribute-based access control
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserResourcePermission(Base):
    """User Resource Permission model for attribute-based authorization"""
    __tablename__ = "user_resource_permission"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    resource = Column(String(255), nullable=False, index=True)  # e.g., "users", "orders", "reports"
    action = Column(String(100), nullable=False)  # e.g., "read", "write", "delete", "admin"
    attributes = Column(Text, nullable=True)  # JSON string for attribute-based conditions
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="permissions")
    
    def __repr__(self):
        return f"<UserResourcePermission(id={self.id}, user_id={self.user_id}, resource={self.resource}, action={self.action})>"


