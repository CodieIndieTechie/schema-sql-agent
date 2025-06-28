#!/usr/bin/env python3
"""
Multi-Tenant SQL Agent Startup Script

Launches the multi-tenant FastAPI backend and Next.js frontend servers.
Note: Celery workers should be started separately for production.
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path


# Import settings for dynamic URLs
from settings import Settings

# Initialize settings
settings = Settings()

# Note: Celery workers should be started separately
# Use: python start_celery_worker.py
print("ℹ️ Note: Start Celery workers separately with 'python start_celery_worker.py'")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import pandas
        import sqlalchemy
        import psycopg2
        print("✅ Backend dependencies verified")
    except ImportError as e:
        print(f"❌ Missing backend dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    return True


def check_frontend_dependencies():
    """Check if frontend dependencies are installed."""
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(
                ["npm", "install"], 
                cwd=frontend_dir, 
                check=True,
                capture_output=True
            )
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            return False
    else:
        print("✅ Frontend dependencies verified")
    
    return True


def start_backend():
    """Start the multi-tenant FastAPI backend server."""
    print("🚀 Starting Multi-Tenant Backend Server (port 8001)...")
    
    backend_process = subprocess.Popen([
        sys.executable, "multitenant_api.py"
    ], cwd=Path(__file__).parent)
    
    return backend_process


def start_frontend():
    """Start the Next.js frontend server."""
    print("🌐 Starting Frontend Server (port 3001)...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Set custom port for multi-tenant frontend
    env = os.environ.copy()
    env["PORT"] = "3001"
    
    frontend_process = subprocess.Popen([
        "npm", "run", "dev"
    ], cwd=frontend_dir, env=env)
    
    return frontend_process


def wait_for_servers():
    """Wait for servers to start up."""
    print("⏳ Waiting for servers to start...")
    time.sleep(5)
    
    print("\n" + "="*60)
    print("🎉 Multi-Tenant SQL Agent is ready!")
    print("="*60)
    print(f"🌐 Frontend:     {settings.frontend_base_url}")
    print(f"🔗 API Docs:     {settings.api_docs_url}")
    print(f"📊 Health:       {settings.api_health_url}")
    print(f"👥 Admin Stats:  {settings.api_base_url}/admin/sessions")
    print("="*60)
    print("\nFeatures:")
    print("• 👤 Individual user sessions with unique databases")
    print("• 📊 Excel/CSV multi-sheet upload (each sheet = table)")
    print("• 💬 Conversation history per user")
    print("• 🔄 Session persistence and management")
    print("• 🎯 Multi-tenant isolation")
    print("\nPress Ctrl+C to stop all servers")
    print("="*60)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Shutting down servers...")
    sys.exit(0)





def main():
    """Main function to start the multi-tenant application."""
    print("🚀 Multi-Tenant SQL Agent Startup")
    print("="*50)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if not check_frontend_dependencies():
        sys.exit(1)
    
    # Celery workers should be started separately
    
    # Start servers
    backend_process = start_backend()
    time.sleep(2)  # Give backend time to start
    
    frontend_process = start_frontend()
    
    # Wait and show info
    wait_for_servers()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process died")
                break
                
            if frontend_process.poll() is not None:
                print("❌ Frontend process died")
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 Stopping servers...")
        
        # Terminate processes
        try:
            # Stop backend and frontend
            if backend_process and backend_process.poll() is None:
                backend_process.terminate()
                backend_process.wait(timeout=5)
                
            if frontend_process and frontend_process.poll() is None:
                frontend_process.terminate()
                frontend_process.wait(timeout=5)
                
            # Stop RabbitMQ worker if running
            if worker_process:
                worker_process.terminate()
                worker_process.join(timeout=5)
                if worker_process.is_alive():
                    worker_process.kill()
            
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"⚠️ Error during shutdown: {e}")
            # Force kill if needed
            if backend_process and backend_process.poll() is None:
                backend_process.kill()
            if frontend_process and frontend_process.poll() is None:
                frontend_process.kill()
        
        print("✅ All servers stopped")


if __name__ == "__main__":
    main()
