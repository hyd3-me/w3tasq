# tests/test_models.py
"""
Test suite for database models.
Following TDD methodology - tests first, then implementation.
"""

from datetime import datetime
# Import User model inside test to avoid circular imports
from app import db_utils


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, app, _db):
        """Test basic user creation with required fields."""
        
        with app.app_context():
            wallet_address="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            # Create a new user
            user, was_created = db_utils.get_or_create_user(wallet_address)
            
            # Add to database
            _db.session.add(user)
            _db.session.commit()
            
            # Verify user was saved
            assert user.id is not None
            assert user.wallet_address == wallet_address
            assert isinstance(user.created_at, datetime)
            assert user.is_active is True
    
    def test_user_indb(self, app):
        """Test basic user creation with required fields."""
        
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

    def test_task_creation(self, app):
        """Test basic task creation with required fields."""
        
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
    
    def test_get_user_tasks_utility(self, app):
        """Test retrieving all tasks for a user using db_utils function."""
        with app.app_context():

            # 1. Создаем пользователя
            wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            user, was_created = db_utils.get_or_create_user(wallet_address)

            user_id = user.id

            # 2. Создаем 3 задачи для этого пользователя, используя существующую (или будущую) утилиту
            # Предположим, что db_utils.create_task уже существует или будет создана
            task1_data = {
                'user_id': user_id,
                'title': 'Task 1',
                'description': 'First test task',
                'priority': 1,
                'status': 0
            }
            task2_data = {
                'user_id': user_id,
                'title': 'Task 2',
                'description': 'Second test task',
                'priority': 2,
                'status': 0
            }
            task3_data = {
                'user_id': user_id,
                'title': 'Task 3',
                'description': 'Third test task',
                'priority': 3,
                'status': 1 # Completed
            }
            
            # Создаем задачи напрямую через модель, так как утилита create_task еще не реализована
            # Create a new task using db_utils function
            task1 = db_utils.create_task(**task1_data)
            task2 = db_utils.create_task(**task2_data)
            task3 = db_utils.create_task(**task3_data)

            tasks = db_utils.get_user_tasks(user_id)
            
            # Проверяем, что задачи принадлежат правильному пользователю
            for task in tasks:
                assert task.user_id == user_id
                
            # Проверяем, что все созданные задачи присутствуют (по title)
            task_titles = {task.title for task in tasks}
            assert 'Task 1' in task_titles
            assert 'Task 2' in task_titles
            assert 'Task 3' in task_titles
