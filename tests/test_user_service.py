"""
Tests for UserService create/update/delete
"""
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.services.user_service import UserService

# Test DB (same pattern as other tests)
TEST_DB_NAME = "wecare_test"
TEST_DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{TEST_DB_NAME}?charset={settings.DB_CHARSET}"

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    Base.metadata.create_all(bind=engine)


def teardown_test_db():
    Base.metadata.drop_all(bind=engine)


def test_user_crud():
    setup_test_db()
    db = TestSessionLocal()

    try:
        # Create user
        user_in = type('X', (), {
            'username': 'testuser_api',
            'email': 'testuser_api@example.com',
            'password': 'supersecret',
            'full_name': 'API Test'
        })

        user = UserService.create_user(db=db, user_in=user_in)
        assert user is not None
        assert user.username == 'testuser_api'

        # Update user
        update_in = type('Y', (), {
            'email': 'updated@example.com',
            'full_name': 'Updated Name',
            'password': 'newsupersecret',
            'is_active': False
        })

        updated = UserService.update_user(db=db, user_id=user.id, user_in=update_in)
        assert updated is not None
        assert updated.email == 'updated@example.com'
        assert updated.full_name == 'Updated Name'
        assert updated.is_active is False

        # Delete
        ok = UserService.delete_user(db=db, user_id=user.id)
        assert ok is True

        # Ensure deleted
        deleted = db.query(User).filter(User.id == user.id).first()
        assert deleted is None

    finally:
        db.close()
        teardown_test_db()
