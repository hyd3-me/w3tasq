import pytest
from app.app import create_app
from app.models import db, User, Task
from app import db_utils


@pytest.fixture(scope='session')
def app():
    """
    Create Flask application instance for testing.
    Session scope - one app instance per test session.
    """
    # Create application with test configuration
    app = create_app(config_name='testing')
    
    yield app

@pytest.fixture(scope='session')
def _db(app):
    """
    Database fixture for pytest-flask-sqlalchemy plugin.
    Session scope for efficiency.
    """
    with app.app_context():
        # Create all tables
        db.create_all()
        yield db
        # Drop all tables after tests
        db.drop_all()

@pytest.fixture
def client(app):
    """
    Flask test client for making HTTP requests.
    Function scope - new client for each test.
    """
    with app.test_client() as client:
        yield client

@pytest.fixture
def user1(_db):
    """
    Fixture for creating the first test user.
    Provides a User instance that is cleaned up after the test.
    """
    wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
    user = User(
        wallet_address=wallet_address,
        username=f"user_{wallet_address[:10]}"
    )
    _db.session.add(user)
    _db.session.commit()
    yield user
    # Teardown: Ensure cleanup happens in the same context
    try:
        # Get the user by ID to ensure we have a managed instance for deletion
        user_to_delete = _db.session.get(User, user.id)
        if user_to_delete:
            _db.session.delete(user_to_delete)
            _db.session.commit()
    except Exception:
        # If something goes wrong during teardown, rollback
        _db.session.rollback()
        pass # Silent ignore is common in test teardowns

@pytest.fixture
def user2(app, _db):
    """
    Fixture for creating the first test user.
    Provides a User instance that is cleaned up after the test.
    """
    wallet_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b2"
    user = User(
        wallet_address=wallet_address,
        username=f"user_{wallet_address[:10]}"
    )
    _db.session.add(user)
    _db.session.commit()
    yield user
    # Teardown: Ensure cleanup happens in the same context
    try:
        # Get the user by ID to ensure we have a managed instance for deletion
        user_to_delete = _db.session.get(User, user.id)
        if user_to_delete:
            _db.session.delete(user_to_delete)
            _db.session.commit()
    except Exception:
        # If something goes wrong during teardown, rollback
        _db.session.rollback()
        pass # Silent ignore is common in test teardowns

@pytest.fixture
def task1(app, _db, user1):
    """
    Fixture for creating the first test task, belonging to user1.
    Provides a Task instance that is cleaned up after the test.
    Depends on the user1 fixture.
    """
    with app.app_context():
        task = Task(
            user_id=user1.id,
            title='Task 1 for User 1',
            description='First task belonging to user1',
            priority=2, # MEDIUM
            status=0    # ACTIVE
        )
        # Add to database
        _db.session.add(task)
        _db.session.commit()
        yield task
        # Teardown: Ensure cleanup happens in the same context
        try:
            # Get the task by ID to ensure we have a managed instance for deletion
            task_to_delete = _db.session.get(Task, task.id)
            if task_to_delete:
                _db.session.delete(task_to_delete)
                _db.session.commit()
        except Exception:
            # If something goes wrong during teardown, rollback
            _db.session.rollback()
            pass # Silent ignore is common in test teardowns

@pytest.fixture
def authenticated_client_for_user1(client, user1):
    """
    Fixture to provide a test client with an active session for user1.
    Simulates the manual authentication logic used in the w3tasq app.
    Yields a Flask test client that is 'logged in' as user1.
    """
    # Use session_transaction to modify the session before making requests
    with client.session_transaction() as sess:
        # Set the session variables exactly as the app expects them
        sess['user_id'] = user1.id
        sess['user_address'] = user1.wallet_address
        sess['authenticated'] = True
        # Any other session variables your app relies on can be set here too
        # sess['some_other_key'] = 'some_value'
        
    # At this point, `client` has the session set.
    # Yield the modified client for use in tests.
    yield client
    
    # Teardown: Clear the session after the test to ensure isolation.
    # This is often handled by the test client itself between requests,
    # but explicitly clearing can be good practice depending on test setup.
    # However, modifying session in session_transaction after yield is tricky.
    # The client fixture itself handles session isolation quite well for new requests.
    # So, often no explicit teardown is needed here for session clearing.
    # If needed, a more complex teardown could involve another session_transaction.