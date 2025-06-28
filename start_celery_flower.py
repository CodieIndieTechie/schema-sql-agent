#!/usr/bin/env python3
"""
Start Celery Flower Dashboard
Web-based monitoring tool for Celery tasks
"""
import os
import sys
import subprocess
from pathlib import Path

def start_celery_flower():
    """Start Celery Flower web dashboard"""
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Celery Flower command using venv
    celery_path = os.path.join(os.getcwd(), 'venv', 'bin', 'celery')
    cmd = [
        celery_path,
        '-A', 'celery_config', 'flower',
        "--port=5555",
        "--address=0.0.0.0",
        "--basic_auth=admin:password",  # Change in production
        "--url_prefix=flower",
    ]
    
    print("🌸 Starting Celery Flower Dashboard...")
    print(f"📍 Working directory: {project_dir}")
    print(f"🌐 Dashboard URL: http://localhost:5555")
    print(f"🔐 Login: admin / password")
    print(f"🔧 Command: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        # Start flower
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery Flower stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery Flower failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_flower()
