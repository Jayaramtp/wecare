"""
User service for creating, updating and deleting users
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """Service for user CRUD operations"""

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        password_hash = get_password_hash(user_in.password)

        user = User(
            username=user_in.username,
            email=user_in.email,
            password_hash=password_hash,
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False,
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise

    @staticmethod
    def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        if user_in.email is not None:
            user.email = user_in.email
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.is_active is not None:
            user.is_active = user_in.is_active
        if user_in.password is not None:
            user.password_hash = get_password_hash(user_in.password)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True
