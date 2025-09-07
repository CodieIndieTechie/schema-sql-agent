#!/usr/bin/env python3
"""
MCP Servers Startup Script

Starts all MCP servers for the SQL Agent system.
"""

import asyncio
import logging
import signal
import sys
import subprocess
import time
from typing import Dict, List, Optional
from pathlib import Path

from mcp_config import mcp_config

# Setup logging
logging.basicConfig(
    level=getattr(logging, mcp_config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(mcp_config.log_file)
    ]
)
logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manages MCP server processes."""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
    async def start_server(self, server_config) -> bool:
        """Start a single MCP server."""
        try:
            logger.info(f"Starting MCP server: {server_config.name}")
            
            # Build command to start server
            cmd = [
                sys.executable, "-m", server_config.module,
                "--port", str(server_config.port),
                "--host", server_config.host
            ]
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[server_config.name] = process
            
            # Wait a moment to check if process started successfully
            await asyncio.sleep(1)
            
            if process.poll() is None:
                logger.info(f"MCP server {server_config.name} started successfully on port {server_config.port}")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"MCP server {server_config.name} failed to start:")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP server {server_config.name}: {e}")
            return False
    
    async def start_all_servers(self) -> bool:
        """Start all enabled MCP servers."""
        logger.info("Starting MCP servers...")
        
        # Validate configuration
        issues = mcp_config.validate_config()
        if issues:
            logger.error("Configuration validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        # Start each enabled server
        enabled_servers = mcp_config.get_enabled_servers()
        success_count = 0
        
        for server_config in enabled_servers:
            if await self.start_server(server_config):
                success_count += 1
            else:
                logger.error(f"Failed to start server: {server_config.name}")
        
        if success_count == len(enabled_servers):
            logger.info(f"Successfully started all {success_count} MCP servers")
            self.running = True
            return True
        else:
            logger.error(f"Only {success_count}/{len(enabled_servers)} servers started successfully")
            return False
    
    async def stop_server(self, server_name: str):
        """Stop a specific MCP server."""
        if server_name in self.processes:
            process = self.processes[server_name]
            logger.info(f"Stopping MCP server: {server_name}")
            
            try:
                process.terminate()
                await asyncio.sleep(2)
                
                if process.poll() is None:
                    logger.warning(f"Force killing MCP server: {server_name}")
                    process.kill()
                
                del self.processes[server_name]
                logger.info(f"MCP server {server_name} stopped")
                
            except Exception as e:
                logger.error(f"Error stopping MCP server {server_name}: {e}")
    
    async def stop_all_servers(self):
        """Stop all MCP servers."""
        logger.info("Stopping all MCP servers...")
        
        for server_name in list(self.processes.keys()):
            await self.stop_server(server_name)
        
        self.running = False
        logger.info("All MCP servers stopped")
    
    async def health_check(self) -> Dict[str, str]:
        """Check health of all running servers."""
        health_status = {}
        
        for server_name, process in self.processes.items():
            if process.poll() is None:
                health_status[server_name] = "running"
            else:
                health_status[server_name] = "stopped"
                logger.warning(f"MCP server {server_name} is not running")
        
        return health_status
    
    async def monitor_servers(self):
        """Monitor server health and restart if needed."""
        while self.running:
            try:
                health_status = await self.health_check()
                
                # Restart any stopped servers
                for server_name, status in health_status.items():
                    if status == "stopped":
                        logger.warning(f"Restarting stopped server: {server_name}")
                        server_config = mcp_config.get_server_config(server_name)
                        if server_config:
                            await self.start_server(server_config)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in server monitoring: {e}")
                await asyncio.sleep(30)

# Global server manager
server_manager = MCPServerManager()

async def main():
    """Main startup function."""
    logger.info("MCP Server Manager starting...")
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start all servers
    if await server_manager.start_all_servers():
        logger.info("MCP servers started successfully")
        
        # Start monitoring
        monitor_task = asyncio.create_task(server_manager.monitor_servers())
        
        try:
            # Keep running until interrupted
            await monitor_task
        except asyncio.CancelledError:
            logger.info("Monitoring cancelled")
    else:
        logger.error("Failed to start MCP servers")
        sys.exit(1)

async def shutdown():
    """Graceful shutdown."""
    logger.info("Shutting down MCP servers...")
    await server_manager.stop_all_servers()
    logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)
