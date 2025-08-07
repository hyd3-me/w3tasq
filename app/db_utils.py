import logging
from app.models import db, User, Task # pyright: ignore[reportMissingImports]
from sqlalchemy import or_, and_


# Set up logger
logger = logging.getLogger('w3tasq.db_utils')

def get_or_create_user(wallet_address):
    """
    Find existing user by wallet address or create new user.
    Args:
        wallet_address: Ethereum wallet address
    Returns:
        tuple: (user_instance, was_created)
    """
    # Find existing user
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if user:
        return user, False
    # If user doesn't exist, create new one
    user = User(
        wallet_address=wallet_address,
        username=f"user_{wallet_address[:10]}"  # Temporary username
    )
    db.session.add(user)
    db.session.commit()
    return user, True  # True means user was created

def create_task(user_id, title, description=None, priority=3, status=0):
    """
    Create a new task for a user.
    Args:
        user_id: ID of the user who owns the task
        title: Task title (required)
        description: Task description (optional)
        priority: Task priority (1=HIGH, 2=MEDIUM, 3=LOW, default=LOW)
        status: Task status (0=ACTIVE, 1=COMPLETED, 2=ARCHIVED, default=ACTIVE)
    Returns:
        Task instance
    """
    # Create a new task
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        priority=priority,
        status=status
    )
    
    # Add to database
    db.session.add(task)
    db.session.commit()
    # logger.debug(f"task created. id: {task.id}")
    
    return task

def get_user_tasks(user_id):
    """
    Get all tasks for a specific user.
    Args:
        db: SQLAlchemy database instance
        Task: Task model class
        user_id: ID of the user whose tasks to retrieve
    Returns:
        list: List of Task instances
    """
    return Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all() # Сортировка по дате создания, новые первые

# --- UPDATED FUNCTION: Get tasks with cursor-based pagination and sorting ---
def get_user_tasks_cursor(user_id, cursor_id=None, limit=12):
    """
    Get a page of tasks for a user using cursor-based pagination.
    Tasks are sorted by priority (High=1, Medium=2, Low=3) first, 
    then by ID descending (newest first).

    Args:
        user_id: ID of the user whose tasks to retrieve
        cursor_id: ID of the last task seen (for pagination). 
                   If None, get the first page.
        limit: Maximum number of tasks to retrieve.

    Returns:
        tuple: (list of Task instances, next_cursor_id, has_more)
               - list of tasks sorted by (priority ASC, id DESC)
               - ID of the last task in the result set (to use as next cursor)
               - boolean indicating if there are more tasks available
    """
    query = Task.query.filter_by(user_id=user_id, status=0)

    # If cursor is provided, filter tasks that come after the cursor task
    # in the sorted list (priority ASC, id DESC)
    if cursor_id is not None:
        # 1. Find the cursor task to get its priority and id
        cursor_task = db.session.get(Task, cursor_id)
        if cursor_task:
            # 2. Filter tasks that:
            #    - Have a lower priority (higher number) OR
            #    - Have the same priority, but ID is less (i.e., it's older)
            query = query.filter(
                or_(
                    Task.priority > cursor_task.priority,
                    and_(Task.priority == cursor_task.priority, Task.id < cursor_task.id)
                )
            )

    # Sort by priority (1, 2, 3) ascending, then by ID descending
    # This gives priority sorting, and within each priority - from new to old
    query = query.order_by(Task.priority.asc(), Task.id.desc())

    # Get one extra record to determine if there are more records
    tasks = query.limit(limit + 1).all()

    has_more = len(tasks) > limit
    if has_more:
        # Remove the extra record
        tasks_to_return = tasks[:-1]
        # Cursor for the next page is the ID of the last returned record
        next_cursor = tasks_to_return[-1].id if tasks_to_return else None
    else:
        tasks_to_return = tasks
        next_cursor = None  # No more records

    return tasks_to_return, next_cursor, has_more

# --- NEW FUNCTION: Retrieve a task by its ID ---
def get_task_by_id(task_id):
    """
    Retrieve a task instance by its ID.

    Args:
        task_id (int): The ID of the task to retrieve.

    Returns:
        tuple: (Task instance or None, message string).
               - If task is found: (Task instance, "Task found").
               - If task is not found: (None, "Task not found").
               - If an error occurs: (None, "Error retrieving task").
    """
    try:
        
        # Query the database for the task with the given ID
        task = Task.query.filter_by(id=task_id).first()
        
        if task:
            return task, "Task found"
        else:
            return None, "Task not found"
            
    except Exception as e:
        # In case of any unexpected database error
        # Logging the error might be useful in production.
        # print(f"Error retrieving task {task_id}: {e}")
        return None, "Error retrieving task"

# --- UPDATED FUNCTION: Authorization check for task ownership ---
def is_user_authorized_for_task(user_id, task_id):
    """
    Check if a user is authorized to access (modify/delete) a specific task.
    Authorization is granted if the task exists and belongs to the user.

    Args:
        user_id (int): The ID of the user making the request.
        task_id (int): The ID of the task to check access for.

    Returns:
        tuple: (result: Task instance or bool, message: str)
               - (Task instance, "Access granted") if the user owns the task.
               - (False, "Access denied. Task not found") if the task does not exist.
               - (False, "Access denied. Task belongs to another user.") if user_id does not match.
               - (False, "Error checking authorization") if an exception occurs.
    """
    try:
        # Use the helper function to get the task
        task, message = get_task_by_id(task_id)
        
        # If task is not found, deny access
        if task is None:
            # message from get_task_by_id will be "Task not found" or "Error retrieving task"
            # We can refine the message here if needed, or pass it through.
            # Let's pass a more specific message for the authorization context.
            return False, f"Access denied. {message}"
            
        # If task is found, check if the user_id matches
        if task.user_id == user_id:
            return task, "Access granted"
        else:
            return False, "Access denied. Task belongs to another user."
            
    except Exception as e:
        # In case of any unexpected error during the check
        # Logging the error might be useful in production.
        # print(f"Error checking authorization for task {task_id} by user {user_id}: {e}")
        return False, "Error checking authorization"

# --- NEW FUNCTION: Update the status of a task ---
def update_task_status_internal(task_instance, new_status):
    """
    Update the status of a task instance.
    This function assumes the task_instance is already authorized for modification.
    It also assumes new_status has been validated by the caller.

    Args:
        task_instance (Task): An authorized Task model instance to update.
        new_status (int): The new status value (0=ACTIVE, 1=COMPLETED, 2=ARCHIVED).

    Returns:
        tuple: (success: bool, message: str)
               - (True, "Task status updated successfully") if the update succeeds.
               - (False, "Invalid task instance provided") if task_instance is not a Task instance.
               - (False, "Invalid status value") if new_status is not in [0, 1, 2].
               - (False, "Error updating task status") if a database error occurs.
    """
    try:
        # 1. Validate inputs
        # Check if task_instance is a valid Task model instance
        if not isinstance(task_instance, Task):
            return False, "Invalid task instance provided"
        
        # Assume new_status is validated at the API level or by the caller.
        # However, an additional check can be added here for extra safety.
        # Valid status values (according to your Task model)
        VALID_STATUSES = {0, 1, 2} # ACTIVE, COMPLETED, ARCHIVED
        if new_status not in VALID_STATUSES:
            return False, f"Invalid status value. Must be one of {VALID_STATUSES}. Got {new_status}."

        # 2. Update the task instance
        # Update the status field
        task_instance.status = new_status
        # SQLAlchemy will automatically update the updated_at field on commit,
        # if it has default=datetime.utcnow or server_default.
        # But we can explicitly update it here if required by business logic.
        # from datetime import datetime
        # task_instance.updated_at = datetime.utcnow() # If the model does not do this automatically
        
        # 3. Commit changes to the database
        # We use db.session, which is imported into the module.
        
        db.session.add(task_instance) # Not strictly necessary if the object is already tracked
        db.session.commit()
        
        # 4. Return success
        return True, "Task status updated successfully"
        
    except Exception as e:
        # 5. Rollback on error and return failure
        # print(f"Error updating task status: {e}") # For debugging
        db.session.rollback()
        return False, "Error updating task status"