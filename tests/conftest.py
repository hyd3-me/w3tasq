import pytest
from app.app import create_app
from app.models import db


@pytest.fixture(scope='session')
def app():
    """
    Create Flask application instance for testing.
    Session scope - one app instance per test session.
    """
    # Создаем приложение с тестовой конфигурацией
    app = create_app(config_name='testing')
    
    yield app

@pytest.fixture(scope='session')
def _db(app):
    """
    Database fixture for pytest-flask-sqlalchemy plugin.
    Session scope for efficiency.
    """
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        yield db
        # Удаляем все таблицы после тестов
        db.drop_all()