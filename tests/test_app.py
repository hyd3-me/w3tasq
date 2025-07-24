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

def test_home_page(client):
    """Тест: главная страница должна возвращать 'Привет'"""
    # Отправляем GET-запрос к главной странице
    response = client.get('/')
    
    # Проверяем статус код
    assert response.status_code == 200
    
    # Проверяем содержимое ответа
    assert 'text/html' in response.content_type