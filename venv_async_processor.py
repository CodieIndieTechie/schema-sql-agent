#!/usr/bin/env python3
"""
Virtual Environment Async File Processor

Uses virtual environment to avoid dependency conflicts.
"""

import os
import json
import uuid
import time
import threading
import tempfile
import logging
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime
from threading import Lock
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Task storage directory
TASK_DIR = os.path.join(tempfile.gettempdir(), "sql_agent_tasks")
QUEUE_DIR = os.path.join(TASK_DIR, "queue")
STATUS_DIR = os.path.join(TASK_DIR, "status")
PROCESSING_DIR = os.path.join(TASK_DIR, "processing")

os.makedirs(TASK_DIR, exist_ok=True)
os.makedirs(QUEUE_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)
os.makedirs(PROCESSING_DIR, exist_ok=True)

# Thread-safe lock for file operations
file_lock = Lock()

class TaskStatus:
    """Task status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success" 
    FAILURE = "failure"
    TIMEOUT = "timeout"

class VenvAsyncProcessor:
    """Async processor that uses virtual environment to avoid dependency issues"""
    
    def __init__(self):
        self.queue_dir = QUEUE_DIR
        self.status_dir = STATUS_DIR
        self.processing_dir = PROCESSING_DIR
        
        # Find virtual environment
        self.venv_python = self._find_venv_python()
        self.worker_active = False
        self.worker_thread = None
    
    def _find_venv_python(self) -> str:
        """Find the virtual environment Python executable"""
        current_dir = Path.cwd()
        
        # Check for venv in current directory
        venv_paths = [
            current_dir / "venv" / "bin" / "python",
            current_dir / "venv" / "bin" / "python3",
            current_dir / ".venv" / "bin" / "python",
            current_dir / ".venv" / "bin" / "python3",
        ]
        
        for venv_path in venv_paths:
            if venv_path.exists():
                logger.info(f"Found virtual environment: {venv_path}")
                return str(venv_path)
        
        # Fallback to system python
        logger.warning("No virtual environment found, using system python")
        return "python3"
    
    def create_task(self, files: List[str], email: str, database_name: str) -> str:
        """Create a new file processing task with email-based session."""
        task_id = str(uuid.uuid4())
        
        # Validate required parameters
        if not email:
            raise ValueError("Email is required for task creation")
        if not database_name:
            raise ValueError("Database name is required for task creation")
        
        # Create task data with email and database info
        task_data = {
            "task_id": task_id,
            "files": files,
            "email": email,  # Use email instead of user_id
            "database_name": database_name,
            "created_at": datetime.now().isoformat(),
            "state": "PENDING"
        }
        
        # Save to queue
        task_file = os.path.join(self.queue_dir, f"{task_id}.json")
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        logger.info(f"Created task {task_id} for email {email} with database {database_name}")
        return task_id
    
    def update_task_status(self, task_id: str, status: str, message: str = None,
                          progress: int = None, total: int = None, result: Any = None, error: Any = None):
        """Update task status"""
        try:
            status_file = os.path.join(self.status_dir, f"{task_id}.json")
            
            # Read existing status or create new
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
            else:
                status_data = {
                    'task_id': task_id,
                    'created_at': datetime.now().isoformat()
                }
            
            # Update fields
            status_data['status'] = str(status) if status is not None else ''
            status_data['updated_at'] = datetime.now().isoformat()
            status_data['message'] = str(message) if message is not None else ''
            status_data['progress'] = str(int(progress)) if progress is not None else '0'
            status_data['total'] = str(int(total)) if total is not None else '0'
            if result is not None:
                status_data['result'] = result
            status_data['error'] = error if error is not None else []
            
            # Write updated status
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update task status {task_id}: {e}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        try:
            status_file = os.path.join(self.status_dir, f"{task_id}.json")
            
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    task_data = json.load(f)
                
                # Map internal status to API response format
                status = task_data.get('status', 'unknown')
                
                # Map status to state for API compatibility
                state_mapping = {
                    'pending': 'PENDING',
                    'processing': 'PROCESSING', 
                    'success': 'SUCCESS',
                    'failure': 'FAILURE',
                    'not_found': 'NOT_FOUND',
                    'error': 'FAILURE'
                }
                
                return {
                    'task_id': task_id,
                    'state': state_mapping.get(status, 'UNKNOWN'),
                    'status': status,
                    'result': task_data.get('result'),
                    'error': task_data.get('error'),
                    'current': task_data.get('progress', 0),
                    'total': task_data.get('total', 0),
                    'files_processed': task_data.get('progress', 0),
                    'sheets_processed': task_data.get('progress', 0)
                }
            else:
                return {
                    'task_id': task_id,
                    'state': 'NOT_FOUND',
                    'status': 'not_found',
                    'result': None,
                    'error': 'Task not found',
                    'current': 0,
                    'total': 0,
                    'files_processed': 0,
                    'sheets_processed': 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return {
                'task_id': task_id,
                'state': 'FAILURE',
                'status': 'error',
                'result': None,
                'error': f'Status retrieval failed: {str(e)}',
                'current': 0,
                'total': 0,
                'files_processed': 0,
                'sheets_processed': 0
            }
    
    def get_queued_tasks(self) -> List[str]:
        """Get list of queued task IDs"""
        try:
            queue_files = [f for f in os.listdir(self.queue_dir) if f.endswith('.json')]
            return [f.replace('.json', '') for f in queue_files]
        except Exception as e:
            logger.error(f"Failed to get queued tasks: {e}")
            return []
    
    def process_task(self, task_id: str):
        """Process a single task"""
        logger.info(f"🚨🚨🚨 PROCESS_TASK CALLED FOR {task_id} 🚨🚨🚨")
        try:
            # Move task from queue to processing
            queue_file = os.path.join(self.queue_dir, f"{task_id}.json")
            processing_file = os.path.join(self.processing_dir, f"{task_id}.json")
            
            if not os.path.exists(queue_file):
                logger.warning(f"Task {task_id} not found in queue")
                return
            
            # Read task data
            logger.info(f"🔍 DEBUG: Reading task data from {queue_file}")
            with open(queue_file, 'r') as f:
                task_data = json.load(f)
            
            logger.info(f"🔍 DEBUG: Task data loaded: {task_data}")
            logger.info(f"🔍 DEBUG: Task data keys: {list(task_data.keys())}")
            
            # Move to processing
            shutil.move(queue_file, processing_file)
            
            # Update status
            self.update_task_status(task_id, TaskStatus.PROCESSING, "Processing files...")
            
            # Process files
            logger.info(f"🔍 DEBUG: About to access task_data['files']")
            if 'files' not in task_data:
                logger.error(f"🔍 DEBUG: 'files' key missing from task_data! Available keys: {list(task_data.keys())}")
                raise KeyError("'files' key missing from task data")
            
            file_paths = task_data['files']
            logger.info(f"🔍 DEBUG: file_paths = {file_paths}")
            
            email = task_data['email']
            database_name = task_data.get('database_name')  # Get database name from task data
            
            logger.info(f"🔍 DEBUG: email = {email}, database_name = {database_name}")
            
            results = []
            total_files = len(file_paths)
            
            for i, file_path in enumerate(file_paths):
                try:
                    self.update_task_status(task_id, TaskStatus.PROCESSING,
                                          f"Processing file {i+1} of {total_files}",
                                          progress=i, total=total_files)
                    
                    # Process file using virtual environment
                    logger.info(f"🚨🚨🚨 ABOUT TO CALL process_single_file({file_path}, {email}) 🚨🚨🚨")
                    result = self.process_single_file(file_path, email, database_name)
                    logger.info(f"🚨🚨🚨 process_single_file RETURNED: {result} 🚨🚨🚨")
                    
                    # Check if the processing was successful
                    if result.get('success'):
                        results.append({
                            'file': os.path.basename(file_path),
                            'success': True,
                            'result': result
                        })
                    else:
                        results.append({
                            'file': os.path.basename(file_path),
                            'success': False,
                            'result': result
                        })
                    
                    # Clean up temp file
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        
                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {e}")
                    results.append({
                        'file': os.path.basename(file_path),
                        'success': False,
                        'result': {'success': False, 'error': str(e)}
                    })
                    
                    # Clean up temp file
                    if os.path.exists(file_path):
                        os.unlink(file_path)
        
            # Final status
            success_count = len([r for r in results if r['success'] == True])
            failed_count = len([r for r in results if r['success'] == False])
            
            if success_count == total_files:
                final_status = TaskStatus.SUCCESS
                message = f"Successfully processed all {total_files} files"
            elif success_count > 0:
                final_status = TaskStatus.SUCCESS  
                message = f"Processed {success_count} of {total_files} files successfully, {failed_count} failed"
            else:
                final_status = TaskStatus.FAILURE
                message = f"Failed to process all {total_files} files"
            
            # Always include error details in the status
            error_details = [r['result'].get('error') for r in results if not r['success']]
            self.update_task_status(task_id, final_status, message,
                                  progress=total_files, total=total_files, result=results, error=error_details)
            
            # Remove from processing
            if os.path.exists(processing_file):
                os.unlink(processing_file)
                
            logger.info(f"Task {task_id} completed: {message}")
            
        except Exception as e:
            logger.error(f"Task {task_id} processing failed: {e}")
            logger.error(f"🔍 DEBUG: Full exception details:", exc_info=True)
            logger.error(f"🔍 DEBUG: Exception type: {type(e).__name__}")
            logger.error(f"🔍 DEBUG: Exception args: {e.args}")
            
            # Add specific handling for KeyError
            if isinstance(e, KeyError):
                logger.error(f"🔍 DEBUG: KeyError - missing key: {e}")
                logger.error(f"🔍 DEBUG: This suggests a dictionary access issue")
            
            self.update_task_status(task_id, TaskStatus.FAILURE, f"Processing failed: {str(e)}", error=str(e))
            
            # Clean up processing file
            processing_file = os.path.join(self.processing_dir, f"{task_id}.json")
            if os.path.exists(processing_file):
                os.unlink(processing_file)
    
    def process_single_file(self, file_path: str, email: str, database_name: str) -> Dict[str, Any]:
        """
        Process a single file using the virtual environment.
        
        Args:
            file_path: Path to the file to process
            email: Email for the session
            database_name: Database name for the session
            
        Returns:
            Dict with success status and results
        """
        logger.info(f"🚨🚨🚨 PROCESS_SINGLE_FILE CALLED - THIS IS THE RIGHT METHOD 🚨🚨🚨")
        
        try:
            if not database_name:
                return {
                    'success': False,
                    'error': f'No database_name provided for email {email}'
                }
            
            logger.info(f"🔍 Processing file: {file_path}")
            logger.info(f"🔍 Email: {email}")
            logger.info(f"🔍 Database name: {database_name}")
            
            # Create a self-contained processing script
            script_content = f'''
import sys
import os

# Add current directory to path
current_dir = "{os.getcwd()}"
sys.path.insert(0, current_dir)

def process_file():
    try:
        # Direct imports
        from multi_sheet_uploader import MultiSheetExcelUploader
        from user_service import UserSession
        
        # Create session object directly - NO LOOKUP ANYWHERE
        email = "{email}"
        database_name = "{database_name}"
        file_path = "{file_path}"
        
        print(f"SUBPROCESS_DEBUG: email={{email}}")
        print(f"SUBPROCESS_DEBUG: database_name={{database_name}}")
        print(f"SUBPROCESS_DEBUG: file_path={{file_path}}")
        
        # Create UserSession directly with provided data
        user_session = UserSession(email, database_name)
        print(f"SUBPROCESS_DEBUG: Created session - email={{user_session.email}}, db={{user_session.database_name}}")
        
        # Create uploader and process file
        uploader = MultiSheetExcelUploader()
        print("SUBPROCESS_DEBUG: Uploader created")
        
        result = uploader.upload_file_with_sheets(file_path, user_session)
        print("SUBPROCESS_DEBUG: upload_file_with_sheets completed")
        
        if result.get("success"):
            print("SUCCESS")
            print("Tables created:", result.get("tables_created", []))
            print("Rows inserted:", result.get("total_rows", 0))
            print("Sheets processed:", result.get("sheets_processed", 0))
        else:
            print("ERROR")
            print(f"Upload failed: {{result.get('error', 'Unknown error')}}")
        
    except Exception as e:
        print("ERROR")
        print(f"Exception in subprocess: {{str(e)}}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_file()
'''
            
            # Write script to temp file
            script_file = os.path.join(tempfile.gettempdir(), f"process_{uuid.uuid4().hex}.py")
            logger.info(f"🔍 Writing script to: {script_file}")
            
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            try:
                # Set up environment
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'
                env['PYTHONIOENCODING'] = 'utf-8'
                
                # Run script with virtual environment
                python_exe = self.find_python_executable()
                logger.info(f"🔍 Using Python executable: {python_exe}")
                
                result = subprocess.run(
                    [python_exe, script_file],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=os.getcwd(),
                    env=env,
                    stdin=subprocess.PIPE,
                    close_fds=True
                )
                
                logger.info(f"🔍 Subprocess exit code: {result.returncode}")
                logger.info(f"🔍 Subprocess stdout: {result.stdout}")
                if result.stderr:
                    logger.warning(f"🔍 Subprocess stderr: {result.stderr}")
                
                # Parse output
                success = False
                error_messages = []
                tables_created = []
                total_rows = 0
                sheets_processed = 0
                
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line == "SUCCESS":
                        success = True
                    elif line == "ERROR":
                        success = False
                    elif line.startswith("Tables created:"):
                        try:
                            tables_str = line.replace("Tables created:", "").strip()
                            tables_created = eval(tables_str) if tables_str else []
                        except:
                            pass
                    elif line.startswith("Rows inserted:"):
                        try:
                            total_rows = int(line.replace("Rows inserted:", "").strip())
                        except:
                            pass
                    elif line.startswith("Sheets processed:"):
                        try:
                            sheets_processed = int(line.replace("Sheets processed:", "").strip())
                        except:
                            pass
                    elif line and not line.startswith("SUBPROCESS_DEBUG:") and not line.startswith("✅") and not line.startswith("INFO:"):
                        error_messages.append(line)
                
                if result.returncode != 0:
                    success = False
                    if result.stderr:
                        error_messages.append(result.stderr)
                
                return {
                    'success': success,
                    'error': '; '.join(error_messages) if error_messages else None,
                    'tables_created': tables_created,
                    'total_rows': total_rows,
                    'sheets_processed': sheets_processed
                }
                
            finally:
                # Clean up script file
                try:
                    os.unlink(script_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in process_single_file: {e}")
            return {
                'success': False,
                'error': f'Process error: {str(e)}'
            }
    
    def start_worker(self):
        """Start the worker in a separate thread"""
        if self.worker_active:
            logger.info("Worker already running")
            return
        
        self.worker_active = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Worker started")
    
    def stop_worker(self):
        """Stop the worker"""
        if self.worker_active:
            self.worker_active = False
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            logger.info("Worker stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        logger.info("Worker loop started")
        
        while self.worker_active:
            try:
                # Get queued tasks
                queued_tasks = self.get_queued_tasks()
                
                if queued_tasks:
                    # Process the first task
                    task_id = queued_tasks[0]
                    logger.info(f"Processing task: {task_id}")
                    self.process_task(task_id)
                else:
                    # Wait a bit before checking again
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(5)
        
        logger.info("Worker loop ended")

    def get_processor_version(self):
        """Return a unique identifier to verify this is the correct file being imported."""
        return "VENV_ASYNC_PROCESSOR_V2_UNIQUE_ID_12345"

    def find_python_executable(self):
        return self.venv_python

# Global processor instance
processor = VenvAsyncProcessor()

# Export functions for compatibility
def create_file_processing_task(files: List[str], email: str, database_name: str) -> str:
    """Create and queue a file processing task"""
    return processor.create_task(files, email, database_name)

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get task status"""
    return processor.get_task_status(task_id)

def get_processor_version():
    """Return a unique identifier to verify this is the correct file being imported."""
    return processor.get_processor_version()

def start_worker():
    """Start the worker process"""
    processor.start_worker()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        processor.stop_worker()
        logger.info("Worker stopped by user")

if __name__ == "__main__":
    start_worker()
