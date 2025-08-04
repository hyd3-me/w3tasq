from app.models import db, User, Task # pyright: ignore[reportMissingImports]


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

# --- НОВАЯ ФУНКЦИЯ: Получение задач с cursor-based пагинацией ---
def get_user_tasks_cursor(user_id, cursor_id=None, limit=12):
    """
    Get a page of tasks for a user using cursor-based pagination.
    Assumes tasks are ordered by ID descending (newest first).
    
    Args:
        user_id: ID of the user whose tasks to retrieve
        cursor_id: ID of the last task seen (for pagination). 
                   If None, get the first page.
        limit: Maximum number of tasks to retrieve.
    
    Returns:
        tuple: (list of Task instances, next_cursor_id, has_more)
               - list of tasks
               - ID of the last task in the result set (to use as next cursor)
               - boolean indicating if there are more tasks available
    """
    query = Task.query.filter_by(user_id=user_id)
    
    # Если курсор задан, фильтруем по ID < cursor_id
    # Это работает, если мы сортируем по ID по убыванию
    if cursor_id is not None:
        query = query.filter(Task.id < cursor_id)
    
    # Сортируем по ID по убыванию (новые первые)
    # Предполагаем, что ID - это автоинкрементное поле, 
    # поэтому новые записи имеют больший ID
    query = query.order_by(Task.id.desc())
    
    # Получаем на одну запись больше, чтобы понять, есть ли еще данные
    tasks = query.limit(limit + 1).all()
    
    has_more = len(tasks) > limit
    if has_more:
        # Убираем лишнюю запись
        tasks_to_return = tasks[:-1]
        # Курсор для следующей страницы - ID последней возвращенной записи
        next_cursor = tasks_to_return[-1].id if tasks_to_return else None
    else:
        tasks_to_return = tasks
        next_cursor = None # Больше записей нет
        
    return tasks_to_return, next_cursor, has_more