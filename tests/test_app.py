# tests/test_app.py
import pytest
from app import utils, db_utils


def test_index_page(client):
    """Test: home page should show dashboard for authenticated user"""
    # Authenticate user by adding to session
    with client.session_transaction() as session:
        session['user_address'] = '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'
        session['authenticated'] = True

    # Now request home page
    response = client.get('/')
    # Should show dashboard (200 OK)
    assert response.status_code == 200
    # Should return HTML
    assert 'text/html' in response.content_type

def test_login_page_is_accessible(client):
    """Тест: страница логина должна быть доступна"""
    response = client.get('/login')
    assert response.status_code == 200
    # Проверяем, что это HTML
    assert 'text/html' in response.content_type

def test_app_has_secret_key_for_sessions(app):
    """Test: Flask app should have secret key configured for sessions"""
    assert app.secret_key is not None
    assert isinstance(app.secret_key, str)
    assert len(app.secret_key) > 0

def test_private_data_contains_secret_key():
    """Test: private_data.py should contain SECRET_KEY variable"""
    try:
        assert hasattr(utils.private_data, 'SECRET_KEY')
        assert utils.private_data.SECRET_KEY is not None
        assert isinstance(utils.private_data.SECRET_KEY, str)
        # Проверяем минимальную длину для безопасности (рекомендуется 32+ байта)
        assert len(utils.private_data.SECRET_KEY) >= 32
    except ImportError:
        pytest.fail("private_data.py file not found or not accessible")
    except AttributeError:
        pytest.fail("SECRET_KEY variable not found in private_data.py")

def test_create_task_api_endpoint(client):
    """Test: authenticated user can create task via API endpoint"""
    # Сначала аутентифицируем пользователя
    with client.session_transaction() as session:
        session['user_address'] = '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'
        session['user_id'] = 1  # Предположим, что у нас есть пользователь с ID=1
        session['authenticated'] = True
    
    # Отправляем POST запрос на создание задачи
    task_data = {
        'title': 'Test task from browser',
        'description': 'This task was created through browser API',
        'priority': 2,
        'status': 0
    }
    
    response = client.post('/api/tasks', 
                          json=task_data,
                          content_type='application/json')
    
    # Проверяем успешный ответ
    assert response.status_code == 201  # Created
    assert 'application/json' in response.content_type
    
    # Проверяем содержимое ответа
    data = response.get_json()
    assert data['success'] is True
    assert data['task']['title'] == 'Test task from browser'
    assert data['task']['user_id'] == 1

def test_index_page_contains_task_form(client):
    """Test: authenticated user sees task creation form on index page"""
    # Authenticate user by adding to session
    with client.session_transaction() as session:
        session['user_address'] = '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'
        session['authenticated'] = True

    # Request home page
    response = client.get('/')
    
    # Should show dashboard (200 OK)
    assert response.status_code == 200
    # Should return HTML
    assert 'text/html' in response.content_type
    
    # Проверяем, что страница содержит форму для создания задачи
    html_content = response.get_data(as_text=True)
    
    # Проверяем наличие ключевых элементов формы
    assert 'Create New Task' in html_content

def test_index_page_contains_tasks_section(client):
    """Test: authenticated user sees the tasks section on the index page."""
    # Аутентифицируем пользователя, имитируя существующую сессию
    with client.session_transaction() as session:
        session['user_address'] = '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'
        session['authenticated'] = True

    # Запрашиваем главную страницу
    response = client.get('/')
    
    # Проверяем, что страница загрузилась успешно
    assert response.status_code == 200
    assert 'text/html' in response.content_type
    
    # Проверяем, что на странице есть заголовок или упоминание задач
    html_content = response.get_data(as_text=True)
    assert 'your tasks' in html_content.lower()

def test_api_patch_task_status_updates_it(authenticated_client_for_user1, user1, task1):
    """
    Test that an authenticated user can update a task's status via the PATCH /api/tasks/<id> endpoint.
    Specifically, tests updating the status to COMPLETED (1).
    """
    client = authenticated_client_for_user1
    
    user_id = user1.id
    task_id = task1.id

    # --- Setup: Ensure the task starts with a known status (e.g., ACTIVE=0) ---
    # While task1 is likely ACTIVE, explicitly asserting its initial state makes the test clearer.
    assert task1.status == 0, "Test assumes task1 starts as ACTIVE (status=0)"

    # --- Action: Send PATCH request to update task status to COMPLETED (1) ---
    patch_data = {
        "status": 1 # TaskStatus.COMPLETED
    }
    # Use the correct URL scheme for your API endpoint
    # Assuming it's /api/tasks/<task_id>
    response = client.patch(f'/api/tasks/{task_id}', json=patch_data)

    # --- Verification 1: Check HTTP response ---
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response data: {response.get_json()}"

    # Parse JSON response
    data = response.get_json()
    assert data is not None, "Response should contain JSON data"
    assert data.get('success') is True, f"API should return success=True. Got: {data}"

    # --- Verification 2: Check the returned task data ---
    updated_task_data = data.get('task')
    assert updated_task_data is not None, "Response should include 'task' data"
    assert updated_task_data.get('id') == task_id, "Returned task ID should match"
    assert updated_task_data.get('user_id') == user_id, "Returned task user_id should match"
    assert updated_task_data.get('status') == 1, f"Returned task status should be updated to 1 (COMPLETED). Got: {updated_task_data.get('status')}"

    # --- Verification 3: Check persistence by querying the database directly ---
    # We need to access the app context to query the database
    with client.application.app_context(): # client.application gives access to the Flask app instance
        task_from_db, msg = db_utils.get_task_by_id(task_id)
        assert task_from_db is not None, "Task should still exist in the database"
        assert task_from_db.status == 1, f"Task status in DB should be updated to 1 (COMPLETED). Got: {task_from_db.status}"
        assert task_from_db.user_id == user_id, "Task user_id in DB should be unchanged"

def test_api_patch_task_status_updates_to2(authenticated_client_for_user1, user1, task1):
    """
    Test that an authenticated user can update a task's status via the PATCH /api/tasks/<id> endpoint.
    Specifically, tests updating the status to COMPLETED (1).
    """
    client = authenticated_client_for_user1
    
    user_id = user1.id
    task_id = task1.id

    # --- Setup: Ensure the task starts with a known status (e.g., ACTIVE=0) ---
    # While task1 is likely ACTIVE, explicitly asserting its initial state makes the test clearer.
    assert task1.status == 0, "Test assumes task1 starts as ACTIVE (status=0)"

    # --- Action: Send PATCH request to update task status to COMPLETED (1) ---
    patch_data = {
        "status": 2 # TaskStatus.ARCHIVED
    }
    # Use the correct URL scheme for your API endpoint
    response = client.patch(f'/api/tasks/{task_id}', json=patch_data)

    # --- Verification 1: Check HTTP response ---
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response data: {response.get_json()}"

    # Parse JSON response
    data = response.get_json()
    assert data is not None, "Response should contain JSON data"
    assert data.get('success') is True, f"API should return success=True. Got: {data}"

    # --- Verification 2: Check the returned task data ---
    updated_task_data = data.get('task')
    assert updated_task_data is not None, "Response should include 'task' data"
    assert updated_task_data.get('id') == task_id, "Returned task ID should match"
    assert updated_task_data.get('user_id') == user_id, "Returned task user_id should match"
    assert updated_task_data.get('status') == 2, f"Returned task status should be updated to 1 (COMPLETED). Got: {updated_task_data.get('status')}"

    # --- Verification 3: Check persistence by querying the database directly ---
    # We need to access the app context to query the database
    with client.application.app_context(): # client.application gives access to the Flask app instance
        task_from_db, msg = db_utils.get_task_by_id(task_id)
        assert task_from_db is not None, "Task should still exist in the database"
        assert task_from_db.status == 2, f"Task status in DB should be updated to 1 (COMPLETED). Got: {task_from_db.status}"
        assert task_from_db.user_id == user_id, "Task user_id in DB should be unchanged"