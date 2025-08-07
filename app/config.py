from app import utils

FLASK_ENV = 'development'

class Config:
    """Base configuration class."""
    SECRET_KEY = utils.get_secret_key()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TASKS_PER_PAGE = 12
    # Base logging settings
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Use database file path from utils for development
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{utils.get_database_path()}"
    # Logging settings for development
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(levelname)s: %(message)s'  # Simple format for console
    LOG_TO_FILE = False  # Output to console only
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TASKS_PER_PAGE = 5 # Smaller for faster tests
    # Logging settings for testing
    LOG_LEVEL = 'ERROR'  # Minimal logs to avoid cluttering test output
    LOG_TO_FILE = True
    LOG_FILE = utils.join_path(utils.get_source_dir(), 'logs', 'tests.log')
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # In production, explicitly set URI or get from environment
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{utils.get_database_path()}"
    # Logging settings for production
    LOG_LEVEL = 'INFO'
    LOG_TO_FILE = True
    LOG_FILE = utils.join_path(utils.get_source_dir(), 'logs', 'w3tasq.log')
    LOG_MAX_BYTES = 1 * 1024 * 1024  # 1 MB per log file
    LOG_BACKUP_COUNT = 3  # Keep 5 backup files

config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}