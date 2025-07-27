# app/models.py
"""
Database models for w3tasq application.
Following TDD - implementing only what's needed for current tests.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class User(db.Model):
    """
    User model representing a Web3 wallet user.
    Each user is identified by their unique wallet address.
    """
    
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Web3 wallet address - required
    wallet_address = db.Column(db.String(42), nullable=False)
    
    # Username - required
    username = db.Column(db.String(80), nullable=False)
    
    # User status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        """String representation of User instance."""
        return f"<User {self.username} ({self.wallet_address})>"