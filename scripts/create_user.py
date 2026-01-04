"""
Utility script to create users with hashed passwords
Usage: python scripts/create_user.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.security import get_password_hash
from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy.exc import IntegrityError

def create_user(username: str, email: str, password: str, full_name: str = None, is_superuser: bool = False):
    """Create a new user in the database"""
    db = SessionLocal()
    try:
        password_hash = get_password_hash(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_superuser=is_superuser,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✓ User created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Superuser: {user.is_superuser}")
        
        return user
        
    except IntegrityError as e:
        db.rollback()
        print(f"✗ Error: User with username '{username}' or email '{email}' already exists")
        return None
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating user: {str(e)}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("User Creation Utility")
    print("=" * 50)
    print()
    
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    full_name = input("Full Name (optional): ").strip() or None
    is_superuser = input("Is Superuser? (y/n): ").strip().lower() == 'y'
    
    if not username or not email or not password:
        print("✗ Error: Username, email, and password are required")
        sys.exit(1)
    
    create_user(username, email, password, full_name, is_superuser)


