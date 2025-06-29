#!/usr/bin/env python3
"""
Database Dependencies for Schema-per-Tenant Architecture

Provides FastAPI dependencies for the schema-per-tenant system.
Each user gets their own schema in the portfoliosql database.
"""

import logging
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from auth_service import get_current_user, User
from schema_migration import schema_db, Tenant
from settings import settings

logger = logging.getLogger(__name__)

def get_portfoliosql_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session for the portfoliosql database.
    This provides access to the public schema tables (tenants, users, chat_history).
    """
    session = schema_db.get_session()
    try:
        yield session
    finally:
        session.close()

def get_db_session_with_schema(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_portfoliosql_db)
) -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session with search_path set to the user's schema.
    
    This is the primary dependency for schema-per-tenant architecture.
    It sets the PostgreSQL search_path to the user's schema, allowing queries to work transparently
    with the user's data in their dedicated schema.
    """
    try:
        
        # Get or create tenant and schema
        tenant = schema_db.get_tenant_by_email(current_user.email)
        if not tenant:
            # Create tenant and schema for new user
            tenant = schema_db.create_tenant_and_schema(current_user.email, current_user.name)
            logger.info(f"Created new tenant and schema for {current_user.email}")
        
        # Create a new session with schema context
        session = schema_db.get_session()
        
        # Set search_path to user's schema first, then public
        schema_name = tenant.schema_name
        session.execute(text(f'SET search_path TO "{schema_name}", public'))
        
        logger.debug(f"Set search_path to {schema_name} for user {current_user.email}")
        
        yield session
        
    except Exception as e:
        logger.error(f"Error in get_db_session_with_schema for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database session error: {str(e)}"
        )
    finally:
        session.close()

def get_user_schema_name(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_portfoliosql_db)
) -> str:
    """
    FastAPI dependency to get the user's schema name.
    Useful for operations that need to know the schema name without creating a full session.
    """
    try:
        # Check if schema-per-tenant is enabled for this user
        if not is_schema_per_tenant_enabled(current_user.email):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Schema-per-tenant not enabled for this user"
            )
        
        tenant = schema_db.get_tenant_by_email(current_user.email)
        if not tenant:
            # Create tenant and schema for new user
            tenant = schema_db.create_tenant_and_schema(current_user.email, current_user.name)
            logger.info(f"Created new tenant and schema for {current_user.email}")
        
        return tenant.schema_name
        
    except Exception as e:
        logger.error(f"Error getting schema name for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user schema: {str(e)}"
        )

def get_tenant_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_portfoliosql_db)
) -> Tenant:
    """
    FastAPI dependency to get the current user's tenant information.
    """
    try:
        tenant = schema_db.get_tenant_by_email(current_user.email)
        if not tenant:
            # Create tenant and schema for new user
            tenant = schema_db.create_tenant_and_schema(current_user.email, current_user.name)
            logger.info(f"Created new tenant for {current_user.email}")
        
        return tenant
        
    except Exception as e:
        logger.error(f"Error getting tenant info for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tenant info: {str(e)}"
        )

# Utility functions for schema management
def ensure_user_schema(user_email: str) -> bool:
    """
    Ensure a user's schema exists in the portfoliosql database.
    This is called automatically when a user first accesses the system.
    """
    try:
        # Create tenant and schema if they don't exist
        tenant = schema_db.create_tenant_and_schema(user_email)
        
        logger.info(f"✅ Successfully ensured schema for {user_email}: {tenant.schema_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to ensure schema for {user_email}: {e}")
        return False

def get_user_schema_info(user_email: str) -> dict:
    """Get schema information for a user."""
    try:
        # Check if tenant exists
        tenant = schema_db.get_tenant_by_email(user_email)
        
        return {
            "user_email": user_email,
            "tenant_exists": tenant is not None,
            "schema_name": tenant.schema_name if tenant else None,
            "tenant_id": tenant.tenant_id if tenant else None,
            "created_at": tenant.created_at.isoformat() if tenant and tenant.created_at else None
        }
        
    except Exception as e:
        logger.error(f"Error getting schema info for {user_email}: {e}")
        return {
            "user_email": user_email,
            "error": str(e),
            "tenant_exists": False
        }

if __name__ == "__main__":
    # Test the dependencies
    from schema_migration import initialize_schema_per_tenant_db
    
    # Initialize database
    initialize_schema_per_tenant_db()
    
    # Test migration status
    test_email = "test@example.com"
    status = get_migration_status(test_email)
    print(f"Migration status for {test_email}:")
    print(status)
