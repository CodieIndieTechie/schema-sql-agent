#!/usr/bin/env python3
"""
Production Deployment Script for Multi-Tenant SQL Agent
Starts all services: Redis, API, Frontend, Celery Workers, and Monitoring
"""
import subprocess
import sys
import time
import os
import signal
from pathlib import Path
from multiprocessing import Process
import threading

class ProductionManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_redis(self):
        """Start Redis using Docker Compose"""
        print("🔴 Starting Redis server...")
        try:
            subprocess.run(["docker-compose", "up", "-d", "redis"], check=True)
            print("✅ Redis started successfully")
            time.sleep(2)  # Wait for Redis to be ready
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start Redis: {e}")
            return False
        return True
    
    def start_api_server(self):
        """Start FastAPI backend server"""
        print("🚀 Starting API server...")
        cmd = [
            "uvicorn", "multitenant_api:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--workers", "2",
            "--log-level", "info"
        ]
        process = subprocess.Popen(cmd)
        self.processes.append(("API Server", process))
        return True
    
    def start_frontend(self):
        """Start Next.js frontend"""
        print("🌐 Starting frontend server...")
        frontend_dir = Path(__file__).parent / "frontend"
        
        # Build frontend first
        build_process = subprocess.run(
            ["npm", "run", "build"], 
            cwd=frontend_dir,
            capture_output=True
        )
        
        if build_process.returncode != 0:
            print("❌ Frontend build failed")
            return False
        
        # Start frontend
        cmd = ["npm", "run", "start"]
        process = subprocess.Popen(cmd, cwd=frontend_dir)
        self.processes.append(("Frontend", process))
        return True
    
    def start_celery_worker(self):
        """Start Celery worker"""
        print("👷 Starting Celery worker...")
        celery_path = os.path.join(os.getcwd(), 'venv', 'bin', 'celery')
        cmd = [
            celery_path, "-A", "celery_config", "worker",
            "--loglevel=info",
            "--concurrency=4",
            "--queues=default,file_processing,query_processing,maintenance",
            "--hostname=worker@%h"
        ]
        process = subprocess.Popen(cmd)
        self.processes.append(("Celery Worker", process))
        return True
    
    def start_celery_beat(self):
        """Start Celery beat scheduler"""
        print("⏰ Starting Celery beat scheduler...")
        celery_path = os.path.join(os.getcwd(), 'venv', 'bin', 'celery')
        cmd = [
            celery_path, "-A", "celery_config", "beat",
            "--loglevel=info"
        ]
        process = subprocess.Popen(cmd)
        self.processes.append(("Celery Beat", process))
        return True
    
    def start_flower_monitoring(self):
        """Start Flower monitoring dashboard"""
        print("🌸 Starting Flower monitoring...")
        celery_path = os.path.join(os.getcwd(), 'venv', 'bin', 'celery')
        cmd = [
            celery_path, "-A", "celery_config", "flower",
            "--port=5555",
            "--address=0.0.0.0"
        ]
        process = subprocess.Popen(cmd)
        self.processes.append(("Flower Monitor", process))
        return True
    
    def check_health(self):
        """Check health of all services"""
        print("\n🔍 Checking service health...")
        
        # Check Redis
        try:
            result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
            redis_status = "✅ Running" if result.stdout.strip() == "PONG" else "❌ Down"
        except:
            redis_status = "❌ Down"
        
        print(f"Redis: {redis_status}")
        
        # Check API (simple version)
        try:
            import requests
            response = requests.get("http://localhost:8001/health", timeout=5)
            api_status = "✅ Running" if response.status_code == 200 else "❌ Down"
        except:
            api_status = "❌ Down"
        
        print(f"API Server: {api_status}")
        
        # Check processes
        for name, process in self.processes:
            if process.poll() is None:
                print(f"{name}: ✅ Running (PID: {process.pid})")
            else:
                print(f"{name}: ❌ Stopped")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signal"""
        print("\n🛑 Shutting down services...")
        self.running = False
        
        # Stop all processes
        for name, process in self.processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        
        # Stop Redis
        try:
            subprocess.run(["docker-compose", "down"], check=True)
            print("Redis stopped")
        except:
            pass
        
        print("👋 All services stopped")
        sys.exit(0)
    
    def start_all_services(self):
        """Start all services in production mode"""
        print("🚀 Starting Multi-Tenant SQL Agent in Production Mode")
        print("=" * 60)
        
        # Register signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start services in order
        if not self.start_redis():
            return False
        
        if not self.start_celery_worker():
            return False
        
        if not self.start_celery_beat():
            return False
        
        if not self.start_flower_monitoring():
            return False
        
        time.sleep(2)  # Wait for Celery to be ready
        
        if not self.start_api_server():
            return False
        
        if not self.start_frontend():
            return False
        
        # Wait for services to start
        print("\n⏳ Waiting for services to start...")
        time.sleep(10)
        
        # Health check
        self.check_health()
        
        # Service URLs
        print("\n🌐 Service URLs:")
        print("Frontend:     http://localhost:3001")
        print("API:          http://localhost:8001")
        print("API Docs:     http://localhost:8001/docs")
        print("Flower:       http://localhost:5555")
        print("Redis GUI:    http://localhost:8081 (if enabled)")
        
        print("\n✅ All services started successfully!")
        print("Press Ctrl+C to stop all services")
        
        # Keep running
        try:
            while self.running:
                time.sleep(60)
                # Periodic health check
                if not self.running:
                    break
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        
        return True

def main():
    """Main function"""
    manager = ProductionManager()
    
    # Check if running as root (not recommended)
    if os.geteuid() == 0:
        print("⚠️ Warning: Running as root is not recommended")
    
    # Start all services
    success = manager.start_all_services()
    
    if not success:
        print("❌ Failed to start services")
        sys.exit(1)

if __name__ == "__main__":
    main()
