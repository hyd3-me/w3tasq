# app/models.py
"""
Database models for w3tasq application.
Following TDD - implementing only what's needed for current tests.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class TaskPriority:
    """Task priority levels"""
    HIGH = 1    # 🔴 Important and urgent
    MEDIUM = 2  # 🟡 Important, not urgent  
    LOW = 3     # ⚪ Regular tasks


class TaskStatus:
    """Task completion statuses"""
    ACTIVE = 0      # Active task
    COMPLETED = 1   # Completed task
    ARCHIVED = 2    # Archived task

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
    
    # Relationships
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        """String representation of User instance."""
        return f"<User {self.username} ({self.wallet_address})>"
    
    def to_dict(self):
        """Convert User instance to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Task(db.Model):
    """
    Task model for user tasks.
    Each task belongs to a specific user.
    """
    
    __tablename__ = 'tasks'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Task content
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Priority (1=high, 2=medium, 3=low)
    priority = db.Column(db.Integer, default=TaskPriority.LOW, nullable=False)
    
    # Status (0=active, 1=completed, 2=archived)
    status = db.Column(db.Integer, default=TaskStatus.ACTIVE, nullable=False)
    
    # Deadline (optional)
    deadline = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation of Task instance."""
        return f"<Task {self.title} (Priority: {self.priority}, Status: {self.status})>"
    
    def to_dict(self):
        """Convert Task instance to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }