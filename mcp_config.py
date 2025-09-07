#!/usr/bin/env python3
"""
MCP Configuration Management

Centralized configuration for MCP servers and clients.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    module: str
    port: int
    host: str = "localhost"
    enabled: bool = True
    max_connections: int = 10
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

@dataclass
class MCPClientConfig:
    """Configuration for MCP client connections."""
    connection_timeout: float = 10.0
    read_timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 60.0

class MCPConfig:
    """MCP system configuration."""
    
    def __init__(self):
        self.base_port = int(os.getenv("MCP_BASE_PORT", "8100"))
        self.host = os.getenv("MCP_HOST", "localhost")
        
        # Server configurations
        self.servers = {
            "sql_database": MCPServerConfig(
                name="sql_database",
                module="mcp_servers.sql_database_server",
                port=self.base_port,
                host=self.host
            ),
            "financial_analytics": MCPServerConfig(
                name="financial_analytics", 
                module="mcp_servers.financial_analytics_server",
                port=self.base_port + 1,
                host=self.host
            ),
            "visualization": MCPServerConfig(
                name="visualization",
                module="mcp_servers.visualization_server", 
                port=self.base_port + 2,
                host=self.host
            )
        }
        
        # Client configuration
        self.client = MCPClientConfig()
        
        # Logging configuration
        self.log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        self.log_file = os.getenv("MCP_LOG_FILE", "logs/mcp.log")
        
        # Security settings
        self.enable_auth = os.getenv("MCP_ENABLE_AUTH", "false").lower() == "true"
        self.auth_token = os.getenv("MCP_AUTH_TOKEN")
        
        # Performance settings
        self.enable_caching = os.getenv("MCP_ENABLE_CACHING", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("MCP_CACHE_TTL", "300"))  # 5 minutes
        
    def get_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific server."""
        return self.servers.get(server_name)
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled server configurations."""
        return [config for config in self.servers.values() if config.enabled]
    
    def get_server_url(self, server_name: str) -> Optional[str]:
        """Get WebSocket URL for a server."""
        config = self.get_server_config(server_name)
        if config:
            return f"ws://{config.host}:{config.port}"
        return None
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check port conflicts
        ports = [config.port for config in self.servers.values()]
        if len(ports) != len(set(ports)):
            issues.append("Port conflicts detected between servers")
        
        # Check required environment variables
        required_env_vars = ["DATABASE_URL", "OPENAI_API_KEY"]
        for var in required_env_vars:
            if not os.getenv(var):
                issues.append(f"Required environment variable {var} not set")
        
        # Check log directory
        log_dir = Path(self.log_file).parent
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create log directory {log_dir}: {e}")
        
        return issues

# Global configuration instance
mcp_config = MCPConfig()
