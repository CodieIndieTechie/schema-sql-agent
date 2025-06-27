#!/usr/bin/env python3
"""
User Service for Multi-Tenant SQL Agent

Handles user session management, database creation, and multi-tenant isolation.
Now uses email-based authentication instead of UUID sessions.
"""

import hashlib
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from settings import settings
from auth_service import User, email_to_database_name


logger = logging.getLogger(__name__)


class UserSession:
    """Represents a user session with database context."""
    
    def __init__(self, email: str, database_name: str = None, name: str = None):
        self.email = email
        self.name = name or email.split('@')[0]
        self.database_name = database_name or email_to_database_name(email)
        self.uploaded_tables = []  # Track uploaded tables
        
        # Ensure database exists
        self._ensure_database_exists()
        
        logger.info(f"UserSession created for {self.email} with database {self.database_name}")
    
    @classmethod
    def from_user(cls, user: User) -> 'UserSession':
        """Create a UserSession from an authenticated User."""
        return cls(
            email=user.email,
            database_name=user.database_name,
            name=user.name
        )
    
    def _ensure_database_exists(self):
        """Ensure the user's database exists."""
        try:
            # Connect to default database to create user database
            default_engine = create_engine(settings.default_database_uri)
            
            with default_engine.connect() as conn:
                # Set autocommit mode for database creation
                conn.execute(text("COMMIT"))
                
                # Check if database exists
                result = conn.execute(text(
                    "SELECT 1 FROM pg_database WHERE datname = :db_name"
                ), {"db_name": self.database_name})
                
                if not result.fetchone():
                    # Create database
                    conn.execute(text(f"CREATE DATABASE \"{self.database_name}\""))
                    logger.info(f"Created database: {self.database_name}")
                else:
                    logger.info(f"Database already exists: {self.database_name}")
                    
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database {self.database_name}: {str(e)}")
            raise
    
    def get_database_engine(self):
        """Get SQLAlchemy engine for user's database."""
        user_db_uri = settings.get_database_uri(self.database_name)
        return create_engine(user_db_uri)
    
    def get_database_connection_info(self) -> Dict[str, Any]:
        """Get database connection information for tools."""
        return {
            "host": settings.db_host,
            "port": settings.db_port,
            "database": self.database_name,
            "username": settings.db_user,
            "password": settings.db_password
        }
    
    def list_tables(self) -> List[str]:
        """List all tables in the user's database."""
        try:
            engine = self.get_database_engine()
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            return tables
        except SQLAlchemyError as e:
            logger.error(f"Failed to list tables for {self.email}: {str(e)}")
            return []
    
    def add_uploaded_table(self, table_name: str, source_file: str, sheet_name: str = None):
        """Add a table to the list of uploaded tables."""
        table_info = {
            'table_name': table_name,
            'source_file': source_file,
            'sheet_name': sheet_name,
            'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Use standard datetime format
        }
        self.uploaded_tables.append(table_info)
        logger.info(f"Added uploaded table {table_name} from {source_file}")


class UserService:
    """Service for managing user sessions and databases."""
    
    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
    
    def create_session_from_email(self, email: str, name: str = None) -> UserSession:
        """Create or get a user session from email address."""
        # Use email as session key
        if email in self.active_sessions:
            logger.info(f"Retrieved existing session for {email}")
            return self.active_sessions[email]
        
        # Create new session
        session = UserSession(email=email, name=name)
        self.active_sessions[email] = session
        
        logger.info(f"Created new session for {email} with database {session.database_name}")
        return session
    
    def create_session_from_user(self, user: User) -> UserSession:
        """Create or get a user session from authenticated User object."""
        return self.create_session_from_email(user.email, user.name)
    
    def get_session_by_email(self, email: str) -> Optional[UserSession]:
        """Get user session by email address."""
        return self.active_sessions.get(email)
    
    def get_user_session(self, email: str) -> Optional[UserSession]:
        """Get user session by email (alias for backward compatibility)."""
        return self.get_session_by_email(email)
    
    def list_user_tables(self, email: str) -> List[str]:
        """List tables for a specific user."""
        session = self.get_session_by_email(email)
        if session:
            return session.list_tables()
        return []
    
    def get_user_database_name(self, email: str) -> str:
        """Get database name for a user by email."""
        return email_to_database_name(email)
    
    def remove_session(self, email: str) -> bool:
        """Remove a user session."""
        if email in self.active_sessions:
            del self.active_sessions[email]
            logger.info(f"Removed session for {email}")
            return True
        return False
    
    def list_active_sessions(self) -> List[str]:
        """List all active session emails."""
        return list(self.active_sessions.keys())
    
    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.active_sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics for health check."""
        return {
            "active_sessions": len(self.active_sessions),
            "session_emails": list(self.active_sessions.keys())
        }
    
    def list_user_databases(self) -> List[str]:
        """List all user databases (based on active sessions)."""
        databases = []
        for email, session in self.active_sessions.items():
            databases.append(session.database_name)
        return databases


# Global user service instance
main_user_service = UserService()


def get_or_create_session_from_email(email: str, name: str = None) -> UserSession:
    """Get or create a user session from email address."""
    return main_user_service.create_session_from_email(email, name)


def get_or_create_session_from_user(user: User) -> UserSession:
    """Get or create a user session from authenticated User object."""
    return main_user_service.create_session_from_user(user)


# DEPRECATED: Keep for backward compatibility but log warnings
def get_or_create_session(user_id: str) -> UserSession:
    """DEPRECATED: Use email-based session creation instead."""
    logger.warning(f"DEPRECATED: get_or_create_session called with user_id {user_id}. Use email-based methods instead.")
    # Try to find existing session or create a temporary one
    if '@' in user_id:  # If it looks like an email
        return get_or_create_session_from_email(user_id)
    else:
        # For backward compatibility, create a temporary session
        fake_email = f"user_{user_id}@temp.local"
        return get_or_create_session_from_email(fake_email)


if __name__ == "__main__":
    # Test the user service
    service = UserService()
    
    # Test email-based session creation
    test_email = "test@example.com"
    session = service.create_session_from_email(test_email, "Test User")
    
    print(f"Created session for: {session.email}")
    print(f"Database name: {session.database_name}")
    print(f"Active sessions: {service.list_active_sessions()}")
    
    # Test table listing
    tables = session.list_tables()
    print(f"Tables in database: {tables}")
