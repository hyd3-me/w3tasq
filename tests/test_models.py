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
from app import db_utils


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, db_app):
        """Test basic user creation with required fields."""
        app, db = db_app
        
        with app.app_context():
            wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            # Create a new user
            user, was_created = db_utils.get_or_create_user(wallet_address)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            # Verify user was saved
            assert user.id is not None
            assert user.wallet_address == wallet_address
            assert isinstance(user.created_at, datetime)
            assert user.is_active is True
    
    def test_user_indb(self, db_app):
        """Test basic user creation with required fields."""
        app, db = db_app
        
        with app.app_context():
            wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            # Create a new user
            user, was_created = db_utils.get_or_create_user(wallet_address)
            
            #getuser
            user_db, was_created = db_utils.get_or_create_user(wallet_address)
            assert was_created is False

            # Verify user was saved
            assert user.id == user_db.id
            assert user.wallet_address == user_db.wallet_address

class TestTaskModel:
    """Test cases for Task model."""

    def test_task_creation(self, db_app):
        """Test basic task creation with required fields."""
        app, db = db_app
        
        with app.app_context():
            # First create a user (tasks belong to users)
            wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            user, was_created = db_utils.get_or_create_user(wallet_address)
            
            # Create a new task using db_utils function
            task = db_utils.create_task(
                user_id=user.id,
                title="Test task",
                description="This is a test task",
                priority=2,  # MEDIUM priority
                status=0     # ACTIVE status
            )
            
            # Verify task was saved
            assert task.id is not None
            assert task.user_id == user.id
            assert task.title == "Test task"
            assert task.description == "This is a test task"
            assert task.priority == 2
            assert task.status == 0
            assert isinstance(task.created_at, datetime)
            assert isinstance(task.updated_at, datetime)