# app/config.py
from app import utils # Предполагаем, что utils доступны

class Config:
    """Base configuration class."""
    SECRET_KEY = utils.get_secret_key()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TASKS_PER_PAGE = 12

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
    # Для разработки используем путь к файлу БД из utils
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{utils.get_database_path()}"
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # Для тестов используем in-memory базу
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TASKS_PER_PAGE = 5 # Меньше для скорости тестов

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # В production лучше явно задать URI или получить из env
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{utils.get_database_path()}"
    

config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}