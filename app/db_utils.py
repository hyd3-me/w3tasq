from app.models import db, User, Task # pyright: ignore[reportMissingImports]
from sqlalchemy import or_, and_


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
    query = Task.query.filter_by(user_id=user_id)

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