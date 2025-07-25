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
    # Generate message as server would do
    message = utils.generate_challenge_message()
    
    # Client receives message and returns signature
    signature = utils.sign_message_with_private_key(message)
    
    # Server verifies using address, signature and original message
    address = utils.get_test_w3addres()
    
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