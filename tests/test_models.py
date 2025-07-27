# tests/test_models.py
"""
Test suite for database models.
Following TDD methodology - tests first, then implementation.
"""

import pytest
from datetime import datetime
# Import fixture from existing test file
from tests.test_database import db_app
# Import User model inside test to avoid circular imports
from app.models import User


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, db_app):
        """Test basic user creation with required fields."""
        app, db = db_app
        
        with app.app_context():
            # Create a new user
            user = User(
                wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                username="testuser"
            )
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            # Verify user was saved
            assert user.id is not None
            assert user.wallet_address == "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            assert user.username == "testuser"
            assert isinstance(user.created_at, datetime)
            assert user.is_active is True