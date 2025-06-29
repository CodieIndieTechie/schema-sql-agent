"""
Celery Tasks for Multi-Tenant SQL Agent
Production-ready task queue implementation
"""
import os
import json
import uuid
import time
import logging
import tempfile
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import shutil

from celery import Task
from celery.exceptions import Retry, WorkerLostError
from celery_config import celery_app
from multi_sheet_uploader import MultiSheetExcelUploader
from auth_service import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallbackTask(Task):
    """Base task class with callbacks"""
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed with exception: {exc}")
        logger.error(f"Traceback: {einfo}")

@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='celery_tasks.process_file_upload'
)
def process_file_upload(self, files: List[str], email: str) -> Dict[str, Any]:
    """
    Process uploaded files and create database tables in user's schema.
    
    Args:
        files: List of file paths to process
        email: User email
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Starting file processing task for user {email}")
        
        # Initialize services for schema-per-tenant architecture
        from schema_user_service import SchemaUserService
        from schema_migration import SchemaPerTenantDB
        
        schema_user_service = SchemaUserService()
        schema_manager = SchemaPerTenantDB()
        uploader = MultiSheetExcelUploader()
        
        # Ensure user schema exists and get user info
        schema_manager.create_tenant_and_schema(email, email.split('@')[0])
        user_session_obj = schema_user_service.create_session_from_email(email, email.split('@')[0])
        user_id = user_session_obj.email  # Use email as user identifier
        
        schema_name = f"user_{email.replace('@', '_').replace('.', '_')}"
        
        result = {
            'task_id': self.request.id,
            'status': 'processing',
            'email': email,
            'schema': schema_name,
            'files_processed': [],
            'tables_created': [],
            'total_rows': 0,
            'errors': [],
            'started_at': datetime.utcnow().isoformat(),
        }
        
        # Process each file
        for file_path in files:
            try:
                if not os.path.exists(file_path):
                    error_msg = f"File not found: {file_path}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
                    continue
                
                logger.info(f"Processing file: {file_path}")
                
                # Process the file using MultiSheetExcelUploader
                # Create user session using SchemaUserSession
                from schema_user_service import SchemaUserSession
                try:
                    user_session = SchemaUserSession(email=email)
                    logger.info(f"Created user session for: {email} with schema: {user_session.schema_name}")
                    
                    file_result = uploader.upload_file_with_sheets(
                        file_path=file_path,
                        user_session=user_session
                    )
                except Exception as session_error:
                    error_msg = f"Failed to create user session for {email}: {str(session_error)}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
                    continue
                
                if file_result.get('success'):
                    result['files_processed'].append(file_path)
                    if 'tables' in file_result:
                        result['tables_created'].extend(file_result['tables'])
                    if 'total_rows' in file_result:
                        result['total_rows'] += file_result['total_rows']
                    
                    logger.info(f"Successfully processed file: {file_path}")
                else:
                    error_msg = f"Failed to process file {file_path}: {file_result.get('error', 'Unknown error')}"
                    result['errors'].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                error_msg = f"Error processing file {file_path}: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        # Update final status
        result['status'] = 'success' if not result['errors'] else 'partial_success'
        result['completed_at'] = datetime.utcnow().isoformat()
        
        # Cleanup temp files
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
        
        logger.info(f"File processing completed for user {email}. Status: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"File processing task failed: {str(e)}", exc_info=True)
        result = {
            'task_id': self.request.id,
            'status': 'failure',
            'email': email,
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat()
        }
        return result

@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30},
    name='celery_tasks.process_sql_query'
)
def process_sql_query(self, query: str, email: str, database_name: str, session_id: str) -> Dict[str, Any]:
    """
    Process SQL query using the agent
    
    Args:
        query: Natural language query
        email: User email
        database_name: Database name
        session_id: Session identifier
        
    Returns:
        Dict with query results
    """
    try:
        logger.info(f"Processing SQL query for user {email}: {query[:100]}...")
        
        # Import here to avoid circular imports
        from multitenant_api import MultitenanSQLAgent
        
        # Initialize agent
        agent = MultitenanSQLAgent()
        
        # Process the query
        result = agent.process_query(
            query=query,
            email=email,
            database_name=database_name,
            session_id=session_id
        )
        
        logger.info(f"SQL query processed successfully for user {email}")
        return {
            'task_id': self.request.id,
            'status': 'success',
            'result': result,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"SQL query processing failed: {str(e)}", exc_info=True)
        return {
            'task_id': self.request.id,
            'status': 'failure',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='celery_tasks.cleanup_user_session'
)
def cleanup_user_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Cleanup user session data
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Cleaning up session {session_id} for user {user_id}")
        
        user_service = UserService()
        result = user_service.cleanup_session(user_id, session_id)
        
        logger.info(f"Session cleanup completed for user {user_id}")
        return {
            'task_id': self.request.id,
            'status': 'success',
            'result': result,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}", exc_info=True)
        return {
            'task_id': self.request.id,
            'status': 'failure',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='celery_tasks.cleanup_expired_sessions'
)
def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Periodic task to cleanup expired sessions
    
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info("Starting periodic cleanup of expired sessions")
        
        user_service = UserService()
        
        # Get expired sessions (older than 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        expired_sessions = user_service.get_expired_sessions(cutoff_time)
        
        cleanup_count = 0
        for session in expired_sessions:
            try:
                user_service.cleanup_session(session['user_id'], session['session_id'])
                cleanup_count += 1
            except Exception as e:
                logger.error(f"Failed to cleanup session {session['session_id']}: {e}")
        
        logger.info(f"Cleaned up {cleanup_count} expired sessions")
        return {
            'task_id': self.request.id,
            'status': 'success',
            'cleaned_sessions': cleanup_count,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Expired sessions cleanup failed: {str(e)}", exc_info=True)
        return {
            'task_id': self.request.id,
            'status': 'failure',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='celery_tasks.health_check'
)
def health_check(self) -> Dict[str, Any]:
    """
    Health check task to monitor system status
    
    Returns:
        Dict with health status
    """
    try:
        # Check database connectivity
        user_service = UserService()
        db_healthy = user_service.check_database_health()
        
        # Check Redis connectivity
        redis_healthy = celery_app.control.ping()
        
        status = 'healthy' if db_healthy and redis_healthy else 'unhealthy'
        
        return {
            'task_id': self.request.id,
            'status': status,
            'database_healthy': db_healthy,
            'redis_healthy': bool(redis_healthy),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            'task_id': self.request.id,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# Compatibility functions for existing code
def create_file_processing_task(files: List[str], email: str) -> str:
    """
    Create a file processing task.
    """
    logger.info(f"Creating file processing task for {len(files)} files for user {email}")
    task = process_file_upload.delay(files, email)
    return task.id

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get task status and result
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Dict with task status and result
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return {
                'task_id': task_id,
                'status': 'pending',
                'message': 'Task is waiting to be processed'
            }
        elif task.state == 'PROGRESS':
            return {
                'task_id': task_id,
                'status': 'processing',
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'message': task.info.get('message', 'Processing...')
            }
        elif task.state == 'SUCCESS':
            return {
                'task_id': task_id,
                'status': 'success',
                'result': task.result
            }
        else:  # FAILURE
            return {
                'task_id': task_id,
                'status': 'failure',
                'error': str(task.info)
            }
            
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return {
            'task_id': task_id,
            'status': 'error',
            'error': f'Error retrieving task status: {str(e)}'
        }

def get_processor_version() -> str:
    """Return processor version identifier"""
    return "celery-v1.0.0"
