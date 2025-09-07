#!/usr/bin/env python3
"""
MCP Servers Package

This package contains the Model Context Protocol (MCP) servers for the SQL Agent system:
- sql_database_server.py: Database operations with enhanced security
- financial_analytics_server.py: Financial analysis and calculations
- visualization_server.py: Chart generation and data formatting
"""

__version__ = "1.0.0"
__author__ = "SQL Agent Team"

# MCP Server registry
MCP_SERVERS = {
    "sql_database": {
        "name": "SQL Database Server",
        "description": "Handles database discovery, connections, and SQL query execution",
        "port": 8010,
        "module": "sql_database_server"
    },
    "financial_analytics": {
        "name": "Financial Analytics Server", 
        "description": "Performs financial calculations and portfolio analysis",
        "port": 8011,
        "module": "financial_analytics_server"
    },
    "visualization": {
        "name": "Visualization Server",
        "description": "Generates charts and formats data presentations",
        "port": 8012,
        "module": "visualization_server"
    }
}
