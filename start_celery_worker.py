#!/usr/bin/env python3
"""
Start Celery Worker
Production-ready script to start Celery workers
"""
import os
import sys
import subprocess
from pathlib import Path

def start_celery_worker():
    """Start Celery worker with optimal configuration"""
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Celery worker command using venv
    celery_path = os.path.join(os.getcwd(), 'venv', 'bin', 'celery')
    cmd = [
        celery_path,
        '-A', 'celery_config',
        'worker',
        "--loglevel=info",
        "--concurrency=4",  # Adjust based on CPU cores
        "--queues=default,file_processing,query_processing,maintenance",
        "--hostname=worker@%h",
        "--max-tasks-per-child=1000",
        "--time-limit=600",  # 10 minutes hard limit
        "--soft-time-limit=300",  # 5 minutes soft limit
    ]
    
    print("🚀 Starting Celery Worker...")
    print(f"📍 Working directory: {project_dir}")
    print(f"🔧 Command: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        # Start the worker
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery worker failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_worker()
