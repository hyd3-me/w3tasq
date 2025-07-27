from app.models import db, User, Task


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