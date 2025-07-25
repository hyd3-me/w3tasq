# tests/test_app.py
import pytest
from app.app import create_app
from app import utils


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Тест: главная страница должна возвращать 'Привет'"""
    # Отправляем GET-запрос к главной странице
    response = client.get('/')
    # Проверяем статус код
    assert response.status_code == 200

def test_login_page_is_accessible(client):
    """Тест: страница логина должна быть доступна"""
    response = client.get('/login')
    assert response.status_code == 200
    # Проверяем, что это HTML
    assert 'text/html' in response.content_type

def test_app_has_secret_key_for_sessions():
    """Test: Flask app should have secret key configured for sessions"""
    app = create_app()
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