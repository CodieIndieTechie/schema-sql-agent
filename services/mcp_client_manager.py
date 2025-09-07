#!/usr/bin/env python3
"""
MCP Client Manager

Manages connections to MCP servers and provides unified interface for:
- SQL Database MCP Server
- Financial Analytics MCP Server  
- Visualization MCP Server

Handles connection pooling, error recovery, and load balancing.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import subprocess
import os

# MCP client imports
try:
    from mcp.client.session import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

logger = logging.getLogger(__name__)

class MCPClientManager:
    """
    Manages MCP client connections to all agent servers.
    
    Provides unified interface for communicating with:
    - SQL Database Server
    - Financial Analytics Server
    - Visualization Server
    """
    
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.clients = {}
        self.server_processes = {}
        self.connection_status = {}
        self.load_config()
        
    def load_config(self):
        """Load MCP server configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Default configuration
                self.config = {
                    "servers": {
                        "sql_database": {
                            "command": "python",
                            "args": ["mcp_servers/sql_database_server.py"],
                            "env": {}
                        },
                        "financial_analytics": {
                            "command": "python",
                            "args": ["mcp_servers/financial_analytics_server.py"],
                            "env": {}
                        },
                        "visualization": {
                            "command": "python",
                            "args": ["mcp_servers/visualization_server.py"],
                            "env": {}
                        }
                    }
                }
                # Save default config
                self.save_config()
                
        except Exception as e:
            logger.error(f"Failed to load MCP config: {str(e)}")
            self.config = {"servers": {}}
    
    def save_config(self):
        """Save MCP server configuration."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save MCP config: {str(e)}")
    
    async def initialize_clients(self):
        """Initialize all MCP client connections."""
        if not MCP_AVAILABLE:
            logger.error("MCP not available - cannot initialize clients")
            return False
        
        success_count = 0
        
        for server_name, server_config in self.config["servers"].items():
            try:
                success = await self._initialize_client(server_name, server_config)
                if success:
                    success_count += 1
                    self.connection_status[server_name] = "connected"
                else:
                    self.connection_status[server_name] = "failed"
                    
            except Exception as e:
                logger.error(f"Failed to initialize {server_name} client: {str(e)}")
                self.connection_status[server_name] = "error"
        
        logger.info(f"Initialized {success_count}/{len(self.config['servers'])} MCP clients")
        return success_count > 0
    
    async def _initialize_client(self, server_name: str, server_config: dict) -> bool:
        """Initialize individual MCP client connection."""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config["args"],
                env=server_config.get("env", {})
            )
            
            # Start stdio client
            stdio_transport = stdio_client(server_params)
            
            # Create client session
            async with stdio_transport as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize session
                    await session.initialize()
                    
                    # Store client session
                    self.clients[server_name] = session
                    
                    logger.info(f"Successfully initialized {server_name} MCP client")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to initialize {server_name}: {str(e)}")
            return False
    
    async def call_sql_tool(self, tool_name: str, arguments: dict) -> Dict[str, Any]:
        """Call tool on SQL Database MCP Server."""
        return await self._call_server_tool("sql_database", tool_name, arguments)
    
    async def call_analytics_tool(self, tool_name: str, arguments: dict) -> Dict[str, Any]:
        """Call tool on Financial Analytics MCP Server."""
        return await self._call_server_tool("financial_analytics", tool_name, arguments)
    
    async def call_visualization_tool(self, tool_name: str, arguments: dict) -> Dict[str, Any]:
        """Call tool on Visualization MCP Server."""
        return await self._call_server_tool("visualization", tool_name, arguments)
    
    async def _call_server_tool(self, server_name: str, tool_name: str, arguments: dict) -> Dict[str, Any]:
        """Call tool on specific MCP server."""
        try:
            if not MCP_AVAILABLE:
                return {
                    "status": "error",
                    "error": "MCP not available",
                    "server": server_name,
                    "tool": tool_name
                }
            
            if server_name not in self.clients:
                return {
                    "status": "error", 
                    "error": f"No client connection for {server_name}",
                    "server": server_name,
                    "tool": tool_name
                }
            
            client = self.clients[server_name]
            
            # Call tool
            result = await client.call_tool(tool_name, arguments)
            
            # Parse result
            if result and hasattr(result, 'content') and result.content:
                content = result.content[0]
                if hasattr(content, 'text'):
                    response_data = json.loads(content.text)
                    response_data["server"] = server_name
                    response_data["tool"] = tool_name
                    return response_data
            
            return {
                "status": "error",
                "error": "No valid response from server",
                "server": server_name,
                "tool": tool_name
            }
            
        except Exception as e:
            logger.error(f"Error calling {server_name}.{tool_name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "server": server_name,
                "tool": tool_name
            }
    
    async def get_server_resources(self, server_name: str) -> Dict[str, Any]:
        """Get available resources from MCP server."""
        try:
            if not MCP_AVAILABLE or server_name not in self.clients:
                return {
                    "status": "error",
                    "error": f"No client connection for {server_name}"
                }
            
            client = self.clients[server_name]
            resources = await client.list_resources()
            
            return {
                "status": "success",
                "server": server_name,
                "resources": [
                    {
                        "uri": str(resource.uri),
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": resource.mimeType
                    }
                    for resource in resources.resources
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting resources from {server_name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "server": server_name
            }
    
    async def get_server_tools(self, server_name: str) -> Dict[str, Any]:
        """Get available tools from MCP server."""
        try:
            if not MCP_AVAILABLE or server_name not in self.clients:
                return {
                    "status": "error",
                    "error": f"No client connection for {server_name}"
                }
            
            client = self.clients[server_name]
            tools = await client.list_tools()
            
            return {
                "status": "success",
                "server": server_name,
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools.tools
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting tools from {server_name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "server": server_name
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all MCP server connections."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "servers": {},
            "summary": {
                "total_servers": len(self.config["servers"]),
                "connected": 0,
                "failed": 0,
                "errors": 0
            }
        }
        
        for server_name in self.config["servers"].keys():
            try:
                if server_name in self.clients:
                    # Try to list tools as health check
                    tools_result = await self.get_server_tools(server_name)
                    if tools_result.get("status") == "success":
                        health_status["servers"][server_name] = {
                            "status": "healthy",
                            "connection": "active",
                            "tools_count": len(tools_result.get("tools", []))
                        }
                        health_status["summary"]["connected"] += 1
                    else:
                        health_status["servers"][server_name] = {
                            "status": "unhealthy",
                            "connection": "failed",
                            "error": tools_result.get("error", "Unknown error")
                        }
                        health_status["summary"]["failed"] += 1
                else:
                    health_status["servers"][server_name] = {
                        "status": "disconnected",
                        "connection": "none",
                        "error": "No client connection"
                    }
                    health_status["summary"]["failed"] += 1
                    
            except Exception as e:
                health_status["servers"][server_name] = {
                    "status": "error",
                    "connection": "error",
                    "error": str(e)
                }
                health_status["summary"]["errors"] += 1
        
        # Overall status
        if health_status["summary"]["failed"] > 0 or health_status["summary"]["errors"] > 0:
            health_status["status"] = "degraded" if health_status["summary"]["connected"] > 0 else "unhealthy"
        
        return health_status
    
    async def reconnect_server(self, server_name: str) -> bool:
        """Reconnect to specific MCP server."""
        try:
            if server_name not in self.config["servers"]:
                logger.error(f"Unknown server: {server_name}")
                return False
            
            # Close existing connection if any
            if server_name in self.clients:
                try:
                    await self.clients[server_name].close()
                except:
                    pass
                del self.clients[server_name]
            
            # Reinitialize
            server_config = self.config["servers"][server_name]
            success = await self._initialize_client(server_name, server_config)
            
            if success:
                self.connection_status[server_name] = "connected"
                logger.info(f"Successfully reconnected to {server_name}")
            else:
                self.connection_status[server_name] = "failed"
                logger.error(f"Failed to reconnect to {server_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error reconnecting to {server_name}: {str(e)}")
            self.connection_status[server_name] = "error"
            return False
    
    async def shutdown(self):
        """Shutdown all MCP client connections."""
        for server_name, client in self.clients.items():
            try:
                await client.close()
                logger.info(f"Closed connection to {server_name}")
            except Exception as e:
                logger.error(f"Error closing {server_name}: {str(e)}")
        
        self.clients.clear()
        self.connection_status.clear()
    
    def get_connection_status(self) -> Dict[str, str]:
        """Get current connection status for all servers."""
        return self.connection_status.copy()
    
    def is_server_available(self, server_name: str) -> bool:
        """Check if specific server is available."""
        return (server_name in self.clients and 
                self.connection_status.get(server_name) == "connected")

# Global MCP client manager instance
mcp_client_manager = None

def get_mcp_client_manager() -> MCPClientManager:
    """Get global MCP client manager instance."""
    global mcp_client_manager
    if mcp_client_manager is None:
        mcp_client_manager = MCPClientManager()
    return mcp_client_manager

async def initialize_mcp_clients():
    """Initialize global MCP client manager."""
    manager = get_mcp_client_manager()
    return await manager.initialize_clients()

async def shutdown_mcp_clients():
    """Shutdown global MCP client manager."""
    global mcp_client_manager
    if mcp_client_manager:
        await mcp_client_manager.shutdown()
        mcp_client_manager = None
