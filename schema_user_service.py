#!/usr/bin/env python3
"""
Schema-per-Tenant User Service

Manages users in the schema-per-tenant architecture.
Each user gets their own schema in the portfoliosql database.
"""

import logging
import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from settings import settings
from auth_service import User
from schema_migration import schema_db, Tenant, email_to_schema_name

logger = logging.getLogger(__name__)


class SchemaUserSession:
    """Represents a user session with schema context in the portfoliosql database."""
    
    def __init__(self, email: str, name: str = None):
        self.email = email
        self.name = name or email.split('@')[0]
        self.schema_name = email_to_schema_name(email)
        self.uploaded_tables = []  # Track uploaded tables
        
        # Ensure tenant and schema exist
        self._ensure_tenant_and_schema_exist()
        
        logger.info(f"SchemaUserSession created for {self.email} with schema {self.schema_name}")
    
    @classmethod
    def from_user(cls, user: User) -> 'SchemaUserSession':
        """Create a SchemaUserSession from an authenticated User."""
        return cls(
            email=user.email,
            name=user.name
        )
    
    def _ensure_tenant_and_schema_exist(self):
        """Ensure the user's tenant and schema exist in portfoliosql database."""
        try:
            # Create tenant and schema if they don't exist
            schema_db.create_tenant_and_schema(self.email, self.name)
            logger.info(f"✅ Tenant and schema ensured for {self.email}")
            
        except Exception as e:
            logger.error(f"❌ Error ensuring tenant/schema for {self.email}: {e}")
            raise
    
    def get_db_session_with_schema(self) -> Session:
        """Get a database session with search_path set to the user's schema."""
        return schema_db.get_db_session_with_schema(self.schema_name)
    
    def list_tables(self) -> List[str]:
        """List all tables in the user's schema."""
        try:
            session = self.get_db_session_with_schema()
            try:
                # Use inspect to get table names from the user's schema
                inspector = inspect(session.bind)
                tables = inspector.get_table_names(schema=self.schema_name)
                logger.info(f"📊 Found {len(tables)} tables in schema {self.schema_name}: {tables}")
                return tables
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"❌ Error listing tables for {self.email}: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table."""
        try:
            session = self.get_db_session_with_schema()
            try:
                # Get table row count
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar()
                
                # Get column information
                inspector = inspect(session.bind)
                columns = inspector.get_columns(table_name, schema=self.schema_name)
                
                return {
                    "table_name": table_name,
                    "row_count": result,
                    "columns": [col["name"] for col in columns],
                    "schema": self.schema_name
                }
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"❌ Error getting table info for {table_name}: {e}")
            return {}
    
    @property
    def db_uri(self) -> str:
        """Get database URI with schema search path for this user."""
        return schema_db.get_schema_db_uri(self.schema_name)
    
    def add_uploaded_table(self, table_name: str, source_file: str = None, sheet_name: str = None):
        """Track uploaded table for this session."""
        table_info = {
            "table_name": table_name,
            "source_file": source_file,
            "sheet_name": sheet_name,
            "uploaded_at": datetime.now().isoformat()
        }
        self.uploaded_tables.append(table_info)
        logger.info(f"📝 Tracked uploaded table: {table_name} from {source_file}")
    
    def cleanup_expired_data(self):
        """Clean up any expired data in the user's schema."""
        # This can be implemented later for maintenance tasks
        pass


class SchemaUserService:
    """Service for managing user sessions in schema-per-tenant architecture."""
    
    def __init__(self):
        self.active_sessions: Dict[str, SchemaUserSession] = {}
        logger.info("📝 SchemaUserService initialized")
    
    def create_session_from_email(self, email: str, name: str = None) -> SchemaUserSession:
        """Create or get a user session from email address."""
        if email in self.active_sessions:
            return self.active_sessions[email]
        
        session = SchemaUserSession(email, name)
        self.active_sessions[email] = session
        
        logger.info(f"✅ Created session for {email}")
        return session
    
    def create_session_from_user(self, user: User) -> SchemaUserSession:
        """Create or get a user session from authenticated User object."""
        return self.create_session_from_email(user.email, user.name)
    
    def get_session_by_email(self, email: str) -> Optional[SchemaUserSession]:
        """Get user session by email address."""
        return self.active_sessions.get(email)
    
    def get_user_session(self, email: str) -> Optional[SchemaUserSession]:
        """Get user session by email (alias for backward compatibility)."""
        return self.get_session_by_email(email)
    
    def list_user_tables(self, email: str) -> List[str]:
        """List tables for a specific user."""
        session = self.get_session_by_email(email)
        if session:
            return session.list_tables()
        
        # Create session if it doesn't exist
        session = self.create_session_from_email(email)
        return session.list_tables()
    
    def get_user_schema_name(self, email: str) -> str:
        """Get schema name for a user by email."""
        return email_to_schema_name(email)
    
    def remove_session(self, email: str) -> bool:
        """Remove a user session."""
        if email in self.active_sessions:
            del self.active_sessions[email]
            logger.info(f"🗑️ Removed session for {email}")
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
        stats = {
            "active_sessions": self.get_session_count(),
            "session_emails": self.list_active_sessions()
        }
        
        # Add table counts for each session
        for email, session in self.active_sessions.items():
            try:
                table_count = len(session.list_tables())
                stats[f"tables_{email}"] = table_count
            except Exception as e:
                logger.warning(f"⚠️ Error getting table count for {email}: {e}")
                stats[f"tables_{email}"] = 0
        
        return stats
    
    def list_user_schemas(self) -> List[str]:
        """List all user schemas (active and inactive)."""
        try:
            return settings.list_user_schemas()
        except Exception as e:
            logger.error(f"❌ Error listing user schemas: {e}")
            return []


# Global schema user service instance
schema_user_service = SchemaUserService()

# Convenience functions for backward compatibility
def get_or_create_session_from_email(email: str, name: str = None) -> SchemaUserSession:
    """Get or create a user session from email address."""
    return schema_user_service.create_session_from_email(email, name)

def get_or_create_session_from_user(user: User) -> SchemaUserSession:
    """Get or create a user session from authenticated User object."""
    return schema_user_service.create_session_from_user(user)


if __name__ == "__main__":
    # Test the schema user service
    service = SchemaUserService()
    
    # Test session creation
    test_email = "test@example.com"
    session = service.create_session_from_email(test_email, "Test User")
    
    print(f"📊 Session created: {session.email} -> {session.schema_name}")
    print(f"📊 Tables: {session.list_tables()}")
    print(f"📊 Service stats: {service.get_session_stats()}")
