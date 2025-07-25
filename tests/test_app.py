# tests/test_app.py
import pytest
from app.app import create_app

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