# tests/test_auth.py
import pytest
from app.app import create_app
import app.utils as utils


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-testing'
    
    with app.test_client() as client:
        yield client

def test_user_session_authentication(client):
    """Test: application should authenticate user via session"""
    # Сначала проверим, что пользователь не авторизован
    response = client.get('/')
    # В сессии пока нет данных о пользователе
    with client.session_transaction() as session:
        assert 'user_address' not in session
        assert session.get('authenticated') is not True
    
    # Теперь симулируем аутентификацию пользователя
    with client.session_transaction() as session:
        session['user_address'] = '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'
        session['authenticated'] = True
    
    # Проверим, что теперь пользователь считается авторизованным
    with client.session_transaction() as session:
        assert 'user_address' in session
        assert session['user_address'] == '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'
        assert session.get('authenticated') is True

def test_signature_verification_valid():
    """Test: valid signature should pass verification"""
    # Server verifies using address, signature and original message
    address = utils.get_test_w3addres()
    
    # Generate message as server would do
    message = utils.generate_challenge_message(address)
    
    # Client receives message and returns signature
    signature = utils.sign_message_with_private_key(message)
    
    # Verify the signature
    result = utils.verify_signature(address, f"0x{signature}", message)
    assert result is True

def test_signature_verification_invalid():
    """Test: invalid signature should not pass verification"""
    message = "Sign this message to authenticate: abc123"
    address = "0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6"
    signature = "0xinvalidsignature"
    
    result = utils.verify_signature(address, signature, message)
    assert result is False

def test_unauthenticated_user_redirected_to_login(client):
    """Test: unauthenticated user should be redirected to login page"""
    # Отправляем запрос к главной странице без аутентификации
    response = client.get('/', follow_redirects=False)  # Не следуем редиректу
    
    # Проверяем, что был возвращен код редиректа
    assert response.status_code == 302
    
    # Проверяем, что редирект ведет на страницу логина
    assert 'Location' in response.headers
    assert '/login' in response.headers['Location']

# tests/test_auth.py (добавить)
def test_challenge_generation_endpoint(client):
    """Test: POST /api/auth/challenge should generate challenge message"""
    response = client.post('/api/auth/challenge', 
                          json={'address': '0x742d35Cc6634C0532925a3b8D4C7d26990d0f7f6'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'message' in data
    assert isinstance(data['message'], str)
    assert len(data['message']) > 0

def test_challenge_generation_without_address(client):
    """Test: POST /api/auth/challenge without address should return error"""
    # Отправляем POST запрос без адреса
    response = client.post('/api/auth/challenge', json={})
    
    # Проверяем, что получили ошибку
    assert response.status_code == 400
    
    # Парсим JSON ответ
    data = response.get_json()
    
    # Проверяем сообщение об ошибке
    assert 'error' in data
    assert 'Address is required' in data['error']

def test_challenge_generation_with_invalid_address(client):
    """Test: POST /api/auth/challenge with invalid address should return error"""
    # Отправляем POST запрос с невалидным адресом
    response = client.post('/api/auth/challenge', 
                          json={'address': 'invalid-address'})
    
    # Проверяем, что получили ошибку
    assert response.status_code == 400
    
    # Парсим JSON ответ
    data = response.get_json()
    
    # Проверяем сообщение об ошибке
    assert 'error' in data
    assert 'Invalid Ethereum address' in data['error']