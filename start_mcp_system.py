#!/usr/bin/env python3
"""
Complete MCP System Startup Script

Starts MCP servers and the main FastAPI application with MCP integration.
"""

import asyncio
import logging
import subprocess
import sys
import time
import signal
from pathlib import Path

from mcp_config import mcp_config

# Setup logging
logging.basicConfig(
    level=getattr(logging, mcp_config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPSystemManager:
    """Manages the complete MCP system startup."""
    
    def __init__(self):
        self.mcp_process = None
        self.api_process = None
        self.running = False
    
    async def start_mcp_servers(self) -> bool:
        """Start MCP servers."""
        try:
            logger.info("Starting MCP servers...")
            
            # Start MCP server manager
            self.mcp_process = subprocess.Popen([
                sys.executable, "start_mcp_servers.py"
            ])
            
            # Wait for servers to start
            await asyncio.sleep(5)
            
            if self.mcp_process.poll() is None:
                logger.info("MCP servers started successfully")
                return True
            else:
                logger.error("MCP servers failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP servers: {e}")
            return False
    
    async def start_api_server(self) -> bool:
        """Start FastAPI server with MCP integration."""
        try:
            logger.info("Starting FastAPI server with MCP integration...")
            
            # Start FastAPI server
            self.api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "multitenant_api:app",
                "--host", "0.0.0.0",
                "--port", "8001",
                "--reload"
            ])
            
            # Wait for API server to start
            await asyncio.sleep(3)
            
            if self.api_process.poll() is None:
                logger.info("FastAPI server started successfully on http://localhost:8001")
                return True
            else:
                logger.error("FastAPI server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start FastAPI server: {e}")
            return False
    
    async def start_system(self) -> bool:
        """Start the complete MCP system."""
        logger.info("Starting MCP-based SQL Agent System...")
        
        # Validate configuration
        issues = mcp_config.validate_config()
        if issues:
            logger.error("Configuration validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        # Start MCP servers first
        if not await self.start_mcp_servers():
            logger.error("Failed to start MCP servers")
            return False
        
        # Wait a bit for servers to fully initialize
        logger.info("Waiting for MCP servers to initialize...")
        await asyncio.sleep(5)
        
        # Start API server
        if not await self.start_api_server():
            logger.error("Failed to start API server")
            await self.stop_system()
            return False
        
        self.running = True
        logger.info("MCP system started successfully!")
        logger.info("Available endpoints:")
        logger.info("  - API Server: http://localhost:8001")
        logger.info("  - API Docs: http://localhost:8001/docs")
        logger.info("  - Health Check: http://localhost:8001/health")
        logger.info("  - MCP Servers: ports 8100-8102")
        
        return True
    
    async def stop_system(self):
        """Stop the complete MCP system."""
        logger.info("Stopping MCP system...")
        
        # Stop API server
        if self.api_process:
            logger.info("Stopping FastAPI server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
            self.api_process = None
        
        # Stop MCP servers
        if self.mcp_process:
            logger.info("Stopping MCP servers...")
            self.mcp_process.terminate()
            try:
                self.mcp_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.mcp_process.kill()
            self.mcp_process = None
        
        self.running = False
        logger.info("MCP system stopped")
    
    async def monitor_system(self):
        """Monitor system health."""
        while self.running:
            try:
                # Check if processes are still running
                if self.mcp_process and self.mcp_process.poll() is not None:
                    logger.error("MCP servers stopped unexpectedly")
                    break
                
                if self.api_process and self.api_process.poll() is not None:
                    logger.error("API server stopped unexpectedly")
                    break
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                break
        
        if self.running:
            logger.error("System monitoring detected failure, shutting down...")
            await self.stop_system()

# Global system manager
system_manager = MCPSystemManager()

async def main():
    """Main function."""
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(system_manager.stop_system())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start system
    if await system_manager.start_system():
        # Monitor system
        try:
            await system_manager.monitor_system()
        except asyncio.CancelledError:
            pass
    else:
        logger.error("Failed to start MCP system")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"System startup failed: {e}")
        sys.exit(1)
