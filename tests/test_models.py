# tests/test_models.py
"""
Test suite for database models.
Following TDD methodology - tests first, then implementation.
"""

from datetime import datetime
# Import User model inside test to avoid circular imports
from app import db_utils # pyright: ignore[reportMissingImports]


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

            wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            user, was_created = db_utils.get_or_create_user(wallet_address)

            user_id = user.id

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
    
    def test_get_user_tasks_cursor_sorting_by_priority_and_id(self, app):
        """
        Test that get_user_tasks_cursor sorts tasks by priority (1, 2, 3) first,
        then by ID descending (newest first), when no cursor is provided.
        """
        with app.app_context():
            # 1. Create a user
            wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b7"
            user, was_created = db_utils.get_or_create_user(wallet_address)
            user_id = user.id

            # 2. Create tasks in an order that does NOT match the expected sorting
            # This will verify that sorting happens in the query, not by chance
            
            # Create a task with low priority (should be last)
            task_low_1 = db_utils.create_task(
                user_id=user_id,
                title='Task Low Priority 1',
                priority=3, # Low
                status=0
            )
            
            # Create a task with high priority (should be first)
            task_high_1 = db_utils.create_task(
                user_id=user_id,
                title='Task High Priority 1',
                priority=1, # High
                status=0
            )
            
            # Create a task with medium priority (should be in the middle)
            task_medium_1 = db_utils.create_task(
                user_id=user_id,
                title='Task Medium Priority 1',
                priority=2, # Medium
                status=0
            )
            
            # Create another task with high priority (should be second)
            task_high_2 = db_utils.create_task(
                user_id=user_id,
                title='Task High Priority 2',
                priority=1, # High
                status=0
            )
            
            # Create another task with low priority (should be last)
            task_low_2 = db_utils.create_task(
                user_id=user_id,
                title='Task Low Priority 2',
                priority=3, # Low
                status=0
            )

            
            # Collect IDs to check the order (newer tasks have higher IDs)
            # Creation order: task_low_1(id=1) -> task_high_1(id=2) -> task_medium_1(id=3) -> task_high_2(id=4) -> task_low_2(id=5)
            # Expected order in result (priority ASC, id DESC):
            # 1. task_high_2 (priority=1, id=4) - High Priority, newer ID
            # 2. task_high_1 (priority=1, id=2) - High Priority, older ID
            # 3. task_medium_1 (priority=2, id=3) - Medium Priority
            # 4. task_low_2 (priority=3, id=5) - Low Priority, newer ID
            # 5. task_low_1 (priority=3, id=1) - Low Priority, older ID

            expected_order = [
                task_high_2.id, # High Priority, ID 4
                task_high_1.id, # High Priority, ID 2
                task_medium_1.id, # Medium Priority, ID 3
                task_low_2.id, # Low Priority, ID 5
                task_low_1.id  # Low Priority, ID 1
            ]

            # 3. Call the function under test
            tasks, next_cursor, has_more = db_utils.get_user_tasks_cursor(
                user_id=user_id,
                cursor_id=None, # First page
                limit=10 # Large enough limit
            )

            # 4. Verify the results
            assert len(tasks) == 5, f"Expected 5 tasks, got {len(tasks)}"
            
            # Check the order of task IDs
            returned_task_ids = [task.id for task in tasks]
            assert returned_task_ids == expected_order, f"Tasks are not in expected order. Expected {expected_order}, got {returned_task_ids}"
            
            # Check that tasks have the expected priorities in the correct order
            expected_priorities_in_order = [1, 1, 2, 3, 3] # High, High, Medium, Low, Low
            returned_priorities = [task.priority for task in tasks]
            assert returned_priorities == expected_priorities_in_order, f"Task priorities are not in expected order. Expected {expected_priorities_in_order}, got {returned_priorities}"
            
            # Check that task titles correspond to the expected order
            expected_titles_in_order = [
                'Task High Priority 2', # ID 4
                'Task High Priority 1', # ID 2
                'Task Medium Priority 1', # ID 3
                'Task Low Priority 2', # ID 5
                'Task Low Priority 1' # ID 1
            ]
            returned_titles = [task.title for task in tasks]
            assert returned_titles == expected_titles_in_order, f"Task titles are not in expected order. Expected {expected_titles_in_order}, got {returned_titles}"
            
            # Check pagination for the first (and only) page
            assert next_cursor is None, "next_cursor should be None for the last page"
            assert has_more is False, "has_more should be False if all tasks fit on the first page"
    
    def test_update_task_status(self, app, user1, task1):
        """
        Test updating the status of a task.
        Focuses on the core logic of updating a task's status once access is confirmed.
        Assumes authorization check (is_user_authorized_for_task) is handled separately.
        """
        with app.app_context():
            # --- Setup: Get the initial status of the task ---
            assert task1.status == 0
            task_id = task1.id
            user_id = user1.id

            # --- Action: Update the task status to COMPLETED (1) ---
            # Assumed signature: update_task_status_internal(task_instance, new_status) -> (bool, str)
            # It accepts an already authorized task instance.
            new_status = 1 # COMPLETED
            assert new_status != task1.status
            
            # First, check authorization and get the task (new logic)
            is_authorized, message = db_utils.is_user_authorized_for_task(user_id, task_id)
            
            assert is_authorized
            task_instance = is_authorized # is_authorized is now a Task instance
            # Then call the update function, passing the instance
            success, message = db_utils.update_task_status_internal(task_instance, new_status)

            # --- Verification: Ensure the operation was successful ---
            assert success is True, f"update_task_status_internal should succeed for authorized user. Message: {message}"
            assert message == "Task status updated successfully" # Can check for a specific message

            # --- Verification: Ensure changes are saved to the DB ---
            # Since we passed task_instance, it should be updated already.
            # But for reliability, query directly from the DB.
            task_from_db, msg = db_utils.get_task_by_id(task_id)
            assert task_from_db is not None, "Task should still exist in DB"
            assert task_from_db.status == new_status, f"Task status in DB should be updated to {new_status}"
            # Check that other fields haven't changed
            assert task_from_db.title == task1.title # Or use constant 'Task 1 for User 1'
            assert task_from_db.user_id == user_id


class TestTaskAuthorization:
    """Test cases for authorization checks using db_utils functions."""

    def test_is_user_authorized_for_task(self, app):
        """
        Test the is_user_authorized_for_task helper function for various scenarios:
        - Authorized user accessing their own task.
        - Unauthorized user trying to access someone else's task.
        - Non-existent task ID.
        - Non-existent user ID.
        """
        with app.app_context():
            # --- Setup: Create two users using db_utils ---
            wallet_address_user1 = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
            wallet_address_user2 = "0xAbCdEf123456789012345678901234567890abcd"
            
            user1, was_created_user1 = db_utils.get_or_create_user(wallet_address_user1)
            user2, was_created_user2 = db_utils.get_or_create_user(wallet_address_user2)
            
            user1_id = user1.id
            user2_id = user2.id

            # --- Setup: Create tasks for each user using db_utils ---
            # Create a task for user1
            task_user1 = db_utils.create_task(
                user_id=user1_id,
                title='User1\'s Task',
                description='A task belonging to user1',
                priority=2, # MEDIUM
                status=0    # ACTIVE
            )
            task_id_user1 = task_user1.id
            
            # Create a task for user2
            task_user2 = db_utils.create_task(
                user_id=user2_id,
                title='User2\'s Task',
                description='A task belonging to user2',
                priority=1, # HIGH
                status=1    # COMPLETED
            )
            task_id_user2 = task_user2.id
            
            # Define IDs for non-existent entities
            non_existent_task_id = 999999
            non_existent_user_id = 888888

            # --- Testing the db_utils.is_user_authorized_for_task function ---
            
            # 1. Authorized: User1 tries to access their own task
            is_auth_1, msg_1 = db_utils.is_user_authorized_for_task(user1_id, task_id_user1)
            assert is_auth_1
            assert msg_1 == "Access granted"

            # 2. Unauthorized: User1 tries to access User2's task
            is_auth_2, msg_2 = db_utils.is_user_authorized_for_task(user1_id, task_id_user2)
            assert is_auth_2 is False
            assert msg_2 == "Access denied. Task belongs to another user."

            # 3. Unauthorized: User2 tries to access User1's task
            is_auth_3, msg_3 = db_utils.is_user_authorized_for_task(user2_id, task_id_user1)
            assert is_auth_3 is False
            assert msg_3 == "Access denied. Task belongs to another user."

            # 4. Non-existent task: Any user tries to access a non-existent task
            is_auth_4a, msg_4a = db_utils.is_user_authorized_for_task(user1_id, non_existent_task_id)
            assert is_auth_4a is False
            # Message will be prefixed with "Access denied. " by is_user_authorized_for_task
            assert "Access denied." in msg_4a 
            
            is_auth_4b, msg_4b = db_utils.is_user_authorized_for_task(user2_id, non_existent_task_id)
            assert is_auth_4b is False
            assert "Access denied." in msg_4b

            # 5. Non-existent user tries to access a real task
            # This scenario actually tests if the real task belongs to the non-existent user,
            # which it doesn't. So it should be False with "belongs to another user" message.
            is_auth_5, msg_5 = db_utils.is_user_authorized_for_task(non_existent_user_id, task_id_user1)
            assert is_auth_5 is False
            assert msg_5 == "Access denied. Task belongs to another user."

            # 6. Non-existent user and non-existent task
            is_auth_6, msg_6 = db_utils.is_user_authorized_for_task(non_existent_user_id, non_existent_task_id)
            assert is_auth_6 is False
            assert "Access denied." in msg_6