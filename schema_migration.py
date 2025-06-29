#!/usr/bin/env python3
"""
Schema-per-Tenant Migration Implementation

This module handles the migration from database-per-tenant to schema-per-tenant architecture.
Implements a phased approach with feature flagging for zero-downtime migration.
"""

import os
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    create_engine, text, Column, String, DateTime, Integer, 
    ForeignKey, UniqueConstraint, Index, MetaData, Table, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from settings import settings

logger = logging.getLogger(__name__)

# Database models for the new schema-per-tenant architecture
Base = declarative_base()

class Tenant(Base):
    """Tenant table in public schema - stores tenant information and schema mapping."""
    __tablename__ = 'tenants'
    
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_name = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(tenant_id={self.tenant_id}, email='{self.email}', schema='{self.schema_name}')>"

class User(Base):
    """User table in public schema - stores user authentication information."""
    __tablename__ = 'users'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.tenant_id'), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, email='{self.email}', tenant_id={self.tenant_id})>"

class ChatHistory(Base):
    """Chat history table in public schema - stores LangChain agent's persistent memory."""
    __tablename__ = 'chat_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)  # user email or unique session ID
    message_type = Column(String(50), nullable=False)  # 'human', 'ai', 'system'
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    message_metadata = Column(String, nullable=True)  # JSON string for additional metadata
    
    # Index for efficient session retrieval
    __table_args__ = (
        Index('idx_chat_history_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_chat_history_session_type', 'session_id', 'message_type'),
    )
    
    def __repr__(self):
        return f"<ChatHistory(session_id='{self.session_id}', type='{self.message_type}', timestamp={self.timestamp})>"

# Pydantic models for API responses
class TenantResponse(BaseModel):
    tenant_id: str
    schema_name: str
    email: str
    name: Optional[str]
    created_at: datetime
    is_active: bool

class UserResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

def email_to_schema_name(email: str) -> str:
    """
    Convert email to a valid PostgreSQL schema name.
    Similar to email_to_database_name but for schemas.
    """
    # Create a hash of the email for uniqueness and brevity
    email_hash = hashlib.sha256(email.encode()).hexdigest()[:8]
    
    # Extract the local part (before @) and clean it
    local_part = email.split('@')[0]
    
    # Clean the local part: remove invalid characters, convert to lowercase
    clean_local = ''.join(c for c in local_part if c.isalnum() or c in ['_']).lower()
    
    # Ensure it starts with a letter (PostgreSQL requirement)
    if not clean_local or not clean_local[0].isalpha():
        clean_local = 'tenant_' + clean_local
    
    # Combine clean local part with hash, ensuring max length of 63 chars (PostgreSQL limit)
    schema_name = f"{clean_local}_{email_hash}"
    
    # Ensure it doesn't exceed PostgreSQL's 63 character limit for identifiers
    if len(schema_name) > 63:
        schema_name = schema_name[:55] + email_hash[:8]
    
    return schema_name

class SchemaPerTenantDB:
    """Database manager for schema-per-tenant architecture."""
    
    def __init__(self):
        # Portfolio SQL database connection (central database)
        self.portfoliosql_uri = self._get_portfoliosql_uri()
        self.engine = create_engine(self.portfoliosql_uri, echo=settings.debug)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Default PostgreSQL connection for admin operations
        self.default_engine = create_engine(settings.get_database_uri('postgres'))
        
    def _get_portfoliosql_uri(self) -> str:
        """Get the portfoliosql database URI."""
        return settings.get_database_uri(settings.portfoliosql_db_name)
    
    def create_portfoliosql_database(self):
        """Create the portfoliosql database if it doesn't exist."""
        try:
            # Connect to default database to create portfoliosql
            conn = psycopg2.connect(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database='postgres'  # Connect to postgres db to create portfoliosql
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cursor:
                # Check if portfoliosql database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    ('portfoliosql',)
                )
                
                if not cursor.fetchone():
                    cursor.execute('CREATE DATABASE portfoliosql')
                    logger.info("✅ Created portfoliosql database")
                else:
                    logger.info("✅ portfoliosql database already exists")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating portfoliosql database: {e}")
            raise
    
    def create_public_schema_tables(self):
        """Create all public schema tables in portfoliosql database."""
        try:
            # Ensure portfoliosql database exists
            self.create_portfoliosql_database()
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Created public schema tables in portfoliosql database")
            
        except Exception as e:
            logger.error(f"❌ Error creating public schema tables: {e}")
            raise
    
    def create_tenant_schema(self, schema_name: str):
        """Create a new schema for a tenant."""
        try:
            with self.engine.begin() as conn:
                # Create the schema
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                logger.info(f"✅ Created schema: {schema_name}")
                # Transaction is automatically committed when using begin()
                
        except Exception as e:
            logger.error(f"❌ Error creating schema {schema_name}: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session for the portfoliosql database."""
        return self.SessionLocal()
    
    def get_schema_db_uri(self, schema_name: str) -> str:
        """Get database URI with search_path set to the specified schema."""
        base_uri = self.portfoliosql_uri
        # Add schema to search_path as a connection parameter
        if '?' in base_uri:
            return f"{base_uri}&options=-csearch_path={schema_name},public"
        else:
            return f"{base_uri}?options=-csearch_path={schema_name},public"
    
    def get_db_session_with_schema(self, schema_name: str):
        """
        Get a database session with search_path set to the specified schema.
        This will be used as a FastAPI dependency.
        """
        session = self.SessionLocal()
        try:
            # Set search_path to user schema first, then public
            session.execute(text(f'SET search_path TO "{schema_name}", public'))
            yield session
        finally:
            session.close()
    
    def create_tenant_and_schema(self, email: str, name: Optional[str] = None) -> Tenant:
        """Create a new tenant with associated schema."""
        session = self.get_session()
        try:
            # Check if tenant already exists
            existing_tenant = session.query(Tenant).filter(Tenant.email == email).first()
            if existing_tenant:
                logger.info(f"✅ Tenant already exists for {email}")
                return existing_tenant
            
            # Generate schema name
            schema_name = email_to_schema_name(email)
            
            # Create schema
            self.create_tenant_schema(schema_name)
            
            # Create tenant record
            tenant = Tenant(
                email=email,
                name=name,
                schema_name=schema_name
            )
            session.add(tenant)
            session.flush()  # Get the tenant_id before creating user
            
            # Create user record
            user = User(
                tenant_id=tenant.tenant_id,
                email=email,
                name=name
            )
            session.add(user)
            
            session.commit()
            session.refresh(tenant)  # Refresh to ensure it's bound to session
            logger.info(f"✅ Created tenant and schema for {email}: {schema_name}")
            return tenant
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error creating tenant for {email}: {e}")
            raise
        finally:
            session.close()
    
    def get_tenant_by_email(self, email: str) -> Optional[Tenant]:
        """Get tenant by email address."""
        session = self.get_session()
        try:
            return session.query(Tenant).filter(Tenant.email == email).first()
        finally:
            session.close()
    
    def get_user_schema_name(self, email: str) -> Optional[str]:
        """Get the schema name for a user by email."""
        tenant = self.get_tenant_by_email(email)
        return tenant.schema_name if tenant else None
    
    def list_tenant_schemas(self) -> List[str]:
        """List all tenant schemas in the database."""
        session = self.get_session()
        try:
            tenants = session.query(Tenant).filter(Tenant.is_active == True).all()
            return [tenant.schema_name for tenant in tenants]
        finally:
            session.close()

# Global instance
schema_db = SchemaPerTenantDB()

def initialize_schema_per_tenant_db():
    """Initialize the schema-per-tenant database setup."""
    try:
        schema_db.create_public_schema_tables()
        logger.info("✅ Schema-per-tenant database initialization completed")
    except Exception as e:
        logger.error(f"❌ Failed to initialize schema-per-tenant database: {e}")
        raise

if __name__ == "__main__":
    # Test the schema creation
    initialize_schema_per_tenant_db()
    
    # Test tenant creation
    test_email = "test@example.com"
    tenant = schema_db.create_tenant_and_schema(test_email, "Test User")
    print(f"Created tenant: {tenant}")
    
    # Test schema lookup
    schema_name = schema_db.get_user_schema_name(test_email)
    print(f"Schema for {test_email}: {schema_name}")
