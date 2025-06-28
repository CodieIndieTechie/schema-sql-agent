#!/usr/bin/env python3
"""
Start Celery Beat Scheduler
For periodic tasks like cleanup and health checks
"""
import os
import sys
import subprocess
from pathlib import Path

def start_celery_beat():
    """Start Celery beat scheduler for periodic tasks"""
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Celery beat command using venv
    celery_path = os.path.join(os.getcwd(), 'venv', 'bin', 'celery')
    cmd = [
        celery_path,
        "-A", "celery_config",
        "beat",
        "--loglevel=info",
        "--schedule-filename=celerybeat-schedule",
    ]
    
    print("⏰ Starting Celery Beat Scheduler...")
    print(f"📍 Working directory: {project_dir}")
    print(f"🔧 Command: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        # Start the beat scheduler
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery beat stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery beat failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_beat()
