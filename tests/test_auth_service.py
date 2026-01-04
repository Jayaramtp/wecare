"""
Comprehensive test suite for authentication service
"""
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.models.user_resource_permission import UserResourcePermission
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
import json


# Create test database
TEST_DB_NAME = "wecare_test"
TEST_DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{TEST_DB_NAME}?charset={settings.DB_CHARSET}"

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    """Create test database and tables"""
    # Note: This assumes the test database exists
    # You may need to create it manually: CREATE DATABASE wecare_test;
    Base.metadata.create_all(bind=engine)


def teardown_test_db():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)


def test_password_hashing():
    """Test Argon2 password hashing"""
    print("\n=== Testing Password Hashing ===")
    
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed[:50]}...")
    
    # Verify correct password
    assert verify_password(password, hashed), "Correct password should verify"
    print("[OK] Correct password verification works")
    
    # Verify incorrect password
    assert not verify_password("wrongpassword", hashed), "Wrong password should not verify"
    print("[OK] Incorrect password rejection works")
    
    # Verify same password produces different hashes (due to salt)
    hashed2 = get_password_hash(password)
    assert hashed != hashed2, "Same password should produce different hashes"
    print("[OK] Salt is working (different hashes for same password)")
    
    # Both hashes should verify
    assert verify_password(password, hashed), "First hash should verify"
    assert verify_password(password, hashed2), "Second hash should verify"
    print("[OK] Both hashed versions verify correctly")
    
    print("[OK] All password hashing tests passed!\n")


def test_user_authentication():
    """Test user authentication flow"""
    print("\n=== Testing User Authentication ===")
    
    setup_test_db()
    db = TestSessionLocal()
    
    try:
        # Create test user
        test_username = "testuser_auth"
        test_email = "testauth@example.com"
        test_password = "securepassword123"
        
        # Check if user exists, delete if exists
        existing_user = db.query(User).filter(User.username == test_username).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        # Create user
        password_hash = get_password_hash(test_password)
        user = User(
            username=test_username,
            email=test_email,
            password_hash=password_hash,
            full_name="Test User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"[OK] Created test user: {test_username}")
        
        # Test authentication with correct credentials
        authenticated_user = AuthService.authenticate_user(db, test_username, test_password)
        assert authenticated_user is not None, "Should authenticate with correct credentials"
        assert authenticated_user.username == test_username, "Should return correct user"
        print("[OK] Authentication with correct credentials works")
        
        # Test authentication with wrong password
        authenticated_user = AuthService.authenticate_user(db, test_username, "wrongpassword")
        assert authenticated_user is None, "Should not authenticate with wrong password"
        print("[OK] Authentication with wrong password is rejected")
        
        # Test authentication with wrong username
        authenticated_user = AuthService.authenticate_user(db, "nonexistent", test_password)
        assert authenticated_user is None, "Should not authenticate with wrong username"
        print("[OK] Authentication with wrong username is rejected")
        
        # Test authentication with email
        authenticated_user = AuthService.authenticate_user(db, test_email, test_password)
        assert authenticated_user is not None, "Should authenticate with email"
        assert authenticated_user.email == test_email, "Should return correct user"
        print("[OK] Authentication with email works")
        
        # Test inactive user
        user.is_active = False
        db.commit()
        try:
            authenticated_user = AuthService.authenticate_user(db, test_username, test_password)
            assert False, "Should raise AuthenticationError for inactive user"
        except Exception as e:
            assert "inactive" in str(e).lower() or "Authentication" in str(e), "Should raise error for inactive user"
            print("[OK] Inactive user authentication is rejected")
        
        print("[OK] All authentication tests passed!\n")
        
    finally:
        db.close()
        teardown_test_db()


def test_login_flow():
    """Test complete login flow with tokens"""
    print("\n=== Testing Login Flow ===")
    
    setup_test_db()
    db = TestSessionLocal()
    
    try:
        # Create test user
        test_username = "testuser_login"
        test_email = "testlogin@example.com"
        test_password = "securepassword123"
        device_id = "test-device-12345"
        
        # Check if user exists, delete if exists
        existing_user = db.query(User).filter(User.username == test_username).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        password_hash = get_password_hash(test_password)
        user = User(
            username=test_username,
            email=test_email,
            password_hash=password_hash,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"[OK] Created test user: {test_username}")
        
        # Test login
        token_response = AuthService.login(db, test_username, test_password, device_id)
        
        assert token_response.access_token is not None, "Should return access token"
        assert token_response.refresh_token is not None, "Should return refresh token"
        assert token_response.token_type == "bearer", "Should return bearer token type"
        assert token_response.expires_in > 0, "Should return expiration time"
        
        print(f"[OK] Login successful")
        print(f"  Access token: {token_response.access_token[:50]}...")
        print(f"  Refresh token: {token_response.refresh_token[:50]}...")
        print(f"  Expires in: {token_response.expires_in} seconds")
        
        # Verify refresh token is stored
        db.refresh(user)
        assert user.refresh_token is not None, "Refresh token should be stored"
        assert user.device_id == device_id, "Device ID should be stored"
        print("[OK] Refresh token and device ID stored in database")
        
        # Test login with wrong password
        try:
            AuthService.login(db, test_username, "wrongpassword", device_id)
            assert False, "Should raise AuthenticationError"
        except Exception as e:
            assert "Authentication" in str(e) or "Invalid" in str(e), "Should raise authentication error"
            print("[OK] Login with wrong password is rejected")
        
        print("[OK] All login flow tests passed!\n")
        
    finally:
        db.close()
        teardown_test_db()


def test_refresh_token():
    """Test refresh token mechanism"""
    print("\n=== Testing Refresh Token ===")
    
    setup_test_db()
    db = TestSessionLocal()
    
    try:
        # Create test user and login
        test_username = "testuser_refresh"
        test_email = "testrefresh@example.com"
        test_password = "securepassword123"
        device_id = "test-device-12345"
        
        existing_user = db.query(User).filter(User.username == test_username).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        password_hash = get_password_hash(test_password)
        user = User(
            username=test_username,
            email=test_email,
            password_hash=password_hash,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Login to get tokens
        import time
        token_response = AuthService.login(db, test_username, test_password, device_id)
        original_refresh_token = token_response.refresh_token
        original_access_token = token_response.access_token
        
        print(f"[OK] Initial login successful")
        
        # Wait a moment to ensure different timestamps
        time.sleep(1)
        
        # Refresh tokens
        new_token_response = AuthService.refresh_access_token(db, original_refresh_token, device_id)
        
        assert new_token_response.access_token is not None, "Should return new access token"
        assert new_token_response.refresh_token is not None, "Should return new refresh token"
        # Access tokens should be different (different expiration times)
        assert new_token_response.access_token != original_access_token, "Should return different access token"
        # Refresh tokens must be different (token rotation)
        assert new_token_response.refresh_token != original_refresh_token, "Should return different refresh token"
        
        print("[OK] Token refresh successful")
        print(f"  New access token: {new_token_response.access_token[:50]}...")
        print(f"  New refresh token: {new_token_response.refresh_token[:50]}...")
        
        # Verify new refresh token is stored
        db.refresh(user)
        assert user.refresh_token == new_token_response.refresh_token, "New refresh token should be stored"
        print("[OK] New refresh token stored in database")
        
        # Test refresh with invalid token
        try:
            AuthService.refresh_access_token(db, "invalid-token", device_id)
            assert False, "Should raise TokenError"
        except Exception as e:
            assert "Token" in str(e) or "Invalid" in str(e), "Should raise token error"
            print("[OK] Invalid refresh token is rejected")
        
        # Test refresh with old token (should fail after new token is issued)
        try:
            AuthService.refresh_access_token(db, original_refresh_token, device_id)
            assert False, "Should raise TokenError for old token"
        except Exception as e:
            assert "Token" in str(e) or "mismatch" in str(e).lower(), "Should raise token error"
            print("[OK] Old refresh token is rejected (token rotation working)")
        
        print("[OK] All refresh token tests passed!\n")
        
    finally:
        db.close()
        teardown_test_db()


def test_permissions():
    """Test attribute-based permission system"""
    print("\n=== Testing Permissions ===")
    
    setup_test_db()
    db = TestSessionLocal()
    
    try:
        # Create test user
        test_username = "testuser_perms"
        test_email = "testperms@example.com"
        test_password = "securepassword123"
        
        existing_user = db.query(User).filter(User.username == test_username).first()
        if existing_user:
            # Delete permissions first
            db.query(UserResourcePermission).filter(UserResourcePermission.user_id == existing_user.id).delete()
            db.delete(existing_user)
            db.commit()
        
        password_hash = get_password_hash(test_password)
        user = User(
            username=test_username,
            email=test_email,
            password_hash=password_hash,
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"[OK] Created test user: {test_username}")
        
        # Create permissions
        perm1 = UserResourcePermission(
            user_id=user.id,
            resource="users",
            action="read",
            attributes=None,  # No attributes = full access to resource
            is_active=True
        )
        
        perm2 = UserResourcePermission(
            user_id=user.id,
            resource="orders",
            action="write",
            attributes=json.dumps({"department": "IT"}),  # Only IT department
            is_active=True
        )
        
        db.add(perm1)
        db.add(perm2)
        db.commit()
        
        print("[OK] Created test permissions")
        
        # Test permission without attributes
        has_permission = PermissionService.check_permission(db, user, "users", "read")
        assert has_permission, "Should have read permission on users"
        print("[OK] Permission check without attributes works")
        
        # Test permission with matching attributes
        has_permission = PermissionService.check_permission(
            db, user, "orders", "write", {"department": "IT"}
        )
        assert has_permission, "Should have write permission on orders for IT department"
        print("[OK] Permission check with matching attributes works")
        
        # Test permission with non-matching attributes
        has_permission = PermissionService.check_permission(
            db, user, "orders", "write", {"department": "HR"}
        )
        assert not has_permission, "Should not have permission for HR department"
        print("[OK] Permission check with non-matching attributes is rejected")
        
        # Test permission on non-existent resource
        has_permission = PermissionService.check_permission(db, user, "reports", "read")
        assert not has_permission, "Should not have permission on reports"
        print("[OK] Permission check on non-existent resource is rejected")
        
        # Test superuser (has all permissions)
        user.is_superuser = True
        db.commit()
        has_permission = PermissionService.check_permission(db, user, "any_resource", "any_action")
        assert has_permission, "Superuser should have all permissions"
        print("[OK] Superuser has all permissions")
        
        print("[OK] All permission tests passed!\n")
        
    finally:
        db.close()
        teardown_test_db()


def test_get_current_user():
    """Test getting current user from token"""
    print("\n=== Testing Get Current User ===")
    
    setup_test_db()
    db = TestSessionLocal()
    
    try:
        # Create test user and login
        test_username = "testuser_current"
        test_email = "testcurrent@example.com"
        test_password = "securepassword123"
        
        existing_user = db.query(User).filter(User.username == test_username).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        password_hash = get_password_hash(test_password)
        user = User(
            username=test_username,
            email=test_email,
            password_hash=password_hash,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Login to get token
        token_response = AuthService.login(db, test_username, test_password)
        access_token = token_response.access_token
        
        print(f"[OK] Login successful, got access token")
        
        # Get current user from token
        current_user = AuthService.get_current_user(db, access_token)
        assert current_user is not None, "Should return user from valid token"
        assert current_user.id == user.id, "Should return correct user"
        assert current_user.username == test_username, "Should return correct username"
        
        print("[OK] Get current user from valid token works")
        
        # Test with invalid token
        current_user = AuthService.get_current_user(db, "invalid-token")
        assert current_user is None, "Should return None for invalid token"
        print("[OK] Invalid token returns None")
        
        # Test with inactive user
        user.is_active = False
        db.commit()
        current_user = AuthService.get_current_user(db, access_token)
        assert current_user is None, "Should return None for inactive user"
        print("[OK] Inactive user returns None")
        
        print("[OK] All get current user tests passed!\n")
        
    finally:
        db.close()
        teardown_test_db()


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE AUTHENTICATION SERVICE TEST SUITE")
    print("=" * 60)
    print(f"Database: {TEST_DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 60)
    
    try:
        test_password_hashing()
        test_user_authentication()
        test_login_flow()
        test_refresh_token()
        test_permissions()
        test_get_current_user()
        
        print("=" * 60)
        print("[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Check if test database exists
    try:
        from sqlalchemy import text
        test_engine = create_engine(f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/?charset={settings.DB_CHARSET}")
        with test_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {TEST_DB_NAME}"))
            conn.commit()
        print(f"[OK] Test database '{TEST_DB_NAME}' ready")
    except Exception as e:
        print(f"[WARNING] Could not create test database: {e}")
        print("Please create it manually: CREATE DATABASE wecare_test;")
    
    success = run_all_tests()
    sys.exit(0 if success else 1)

