# tests/test_database.py
import os
import pytest
from app.app import create_app
from app import utils


def test_database_file_exists_at_path():
    """Test: database file should exist at the configured path"""
    # Get database path from utils
    db_path = utils.get_database_path()
    
    # Check that the path is not empty
    assert db_path is not None
    assert isinstance(db_path, str)
    assert len(db_path) > 0
    
    assert os.path.exists(db_path)

    # Check that path ends with correct filename
    assert db_path.endswith('tasks_notes.db')
    
    # Check that the directory exists or can be created
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        # If directory doesn't exist, check that we can create it
        parent_dir = os.path.dirname(db_dir)
        assert os.access(parent_dir, os.W_OK), f"Cannot write to parent directory {parent_dir}"
    else:
        # If directory exists, check write permissions
        assert os.access(db_dir, os.W_OK), f"Cannot write to database directory {db_dir}"
    
    # Test actual database connection with real file
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    with app.app_context():
        from app.app import db
        # Test connection
        db.engine.connect()
        assert True  # If no exception, connection works

def test_database_file_exists_or_can_be_created():
    """Test: database file should be accessible at returned path"""
    # Get database path
    db_path = utils.get_database_path()
    
    # Check that directory exists or can be created
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        # Directory doesn't exist, but we should be able to create it
        assert os.access(os.path.dirname(db_dir), os.W_OK)
    else:
        # Directory exists, check write permissions
        assert os.access(db_dir, os.W_OK)