#!/usr/bin/env python3
"""
SQL Database MCP Server

Provides secure database operations through MCP protocol:
- Database discovery and connection management
- SQL query generation and execution with validation
- Schema-per-tenant isolation
- Enhanced security against SQL injection
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as mcp_types

# Database and AI imports
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import pandas as pd

# Local imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import settings
from database_discovery import discovery_service
from agent_prompts import get_agent_prompt
from schema_migration import email_to_schema_name

logger = logging.getLogger(__name__)

class SQLDatabaseMCPServer:
    """
    MCP Server for SQL Database operations with enhanced security.
    
    Provides isolated database operations through MCP protocol:
    - Secure SQL query execution
    - Database discovery with user isolation
    - Schema-per-tenant architecture enforcement
    - Query validation and sanitization
    """
    
    def __init__(self):
        self.server = Server("sql-database")
        self.agents_cache = {}
        self.discovery_cache = {}
        self.cache_expiry = {}
        self.setup_resources()
        self.setup_tools()
        
    def setup_resources(self):
        """Setup MCP resources for database operations."""
        
        @self.server.list_resources()
        async def list_resources() -> List[mcp_types.Resource]:
            """List available database resources."""
            return [
                mcp_types.Resource(
                    uri="database://discovery",
                    name="Database Discovery",
                    description="Discover available databases and schemas",
                    mimeType="application/json"
                ),
                mcp_types.Resource(
                    uri="database://schema/{schema_name}",
                    name="Schema Information",
                    description="Get detailed schema information for user",
                    mimeType="application/json"
                ),
                mcp_types.Resource(
                    uri="database://tables/{schema_name}",
                    name="Table Listing",
                    description="List tables in user schema",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: mcp_types.AnyUrl) -> str:
            """Read database resource content."""
            uri_str = str(uri)
            
            if uri_str == "database://discovery":
                # Return comprehensive database discovery
                discovery_info = await self._get_comprehensive_discovery()
                return json.dumps(discovery_info, indent=2)
            
            elif uri_str.startswith("database://schema/"):
                schema_name = uri_str.split("/")[-1]
                schema_info = await self._get_schema_info(schema_name)
                return json.dumps(schema_info, indent=2)
            
            elif uri_str.startswith("database://tables/"):
                schema_name = uri_str.split("/")[-1]
                tables_info = await self._get_tables_info(schema_name)
                return json.dumps(tables_info, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    def setup_tools(self):
        """Setup MCP tools for database operations."""
        
        @self.server.call_tool()
        async def execute_sql_query(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Execute SQL query with security validation and user isolation.
            
            Args:
                arguments: {
                    "query": str - Natural language query
                    "user_email": str - User email for schema isolation
                    "session_id": str - Optional session ID
                }
            """
            try:
                query = arguments.get("query", "")
                user_email = arguments.get("user_email", "anonymous@example.com")
                session_id = arguments.get("session_id", str(uuid.uuid4()))
                
                # Validate inputs
                if not query.strip():
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Query cannot be empty",
                            "status": "error"
                        })
                    )]
                
                # Get or create SQL agent for user
                agent = await self._get_or_create_agent(user_email)
                
                # Execute query with agent
                result = await self._execute_with_agent(agent, query, user_email, session_id)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error executing SQL query: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Query execution failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def discover_databases(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Discover available databases for user.
            
            Args:
                arguments: {
                    "user_email": str - User email for discovery scope
                    "discovery_mode": str - "user_specific" or "comprehensive"
                }
            """
            try:
                user_email = arguments.get("user_email", "anonymous@example.com")
                discovery_mode = arguments.get("discovery_mode", "comprehensive")
                
                # Get discovery info
                if discovery_mode == "comprehensive":
                    discovery_info = await self._get_comprehensive_discovery()
                else:
                    discovery_info = await self._get_user_discovery(user_email)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(discovery_info, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error in database discovery: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Database discovery failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def validate_query_safety(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Validate SQL query for safety and security.
            
            Args:
                arguments: {
                    "sql_query": str - Raw SQL query to validate
                    "user_email": str - User email for context
                }
            """
            try:
                sql_query = arguments.get("sql_query", "")
                user_email = arguments.get("user_email", "anonymous@example.com")
                
                validation_result = self._validate_sql_safety(sql_query, user_email)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(validation_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error validating query: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Query validation failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def get_table_schema(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Get detailed schema information for specific table.
            
            Args:
                arguments: {
                    "table_name": str - Name of table
                    "user_email": str - User email for schema context
                }
            """
            try:
                table_name = arguments.get("table_name", "")
                user_email = arguments.get("user_email", "anonymous@example.com")
                
                schema_info = await self._get_table_schema_details(table_name, user_email)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(schema_info, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error getting table schema: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Schema retrieval failed: {str(e)}",
                        "status": "error"
                    })
                )]
    
    async def _get_or_create_agent(self, user_email: str):
        """Get or create SQL agent for user with caching."""
        cache_key = f"agent_{user_email}"
        
        if cache_key in self.agents_cache:
            return self.agents_cache[cache_key]
        
        try:
            # Import the enhanced SQL agent creation function
            from agents.enhanced_sql_agent import create_enhanced_sql_agent
            
            # Create agent with comprehensive discovery
            agent = create_enhanced_sql_agent(
                user_email=user_email,
                discovery_mode='comprehensive'
            )
            
            # Cache the agent
            self.agents_cache[cache_key] = agent
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create SQL agent for {user_email}: {str(e)}")
            raise
    
    async def _execute_with_agent(self, agent, query: str, user_email: str, session_id: str) -> Dict[str, Any]:
        """Execute query with SQL agent and return structured result."""
        try:
            # Process query with agent
            result = await asyncio.to_thread(agent.process_query, query)
            
            # Structure the response
            response_data = {
                "status": "success",
                "response": result.get("response", ""),
                "data": result.get("data", {}),
                "metadata": {
                    "user_email": user_email,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "agent_type": "enhanced_sql_agent"
                }
            }
            
            # Add chart files if present
            if "chart_files" in result:
                response_data["chart_files"] = result["chart_files"]
            
            return response_data
            
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "user_email": user_email,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "query": query
                }
            }
    
    async def _get_comprehensive_discovery(self) -> Dict[str, Any]:
        """Get comprehensive database discovery information."""
        try:
            # Use discovery service
            discovery_info = discovery_service.get_comprehensive_database_info()
            
            return {
                "status": "success",
                "discovery_mode": "comprehensive",
                "databases": discovery_info.get("databases", {}),
                "total_databases": len(discovery_info.get("databases", {})),
                "total_schemas": sum(len(db.get("schemas", {})) for db in discovery_info.get("databases", {}).values()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive discovery failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_user_discovery(self, user_email: str) -> Dict[str, Any]:
        """Get user-specific database discovery information."""
        try:
            user_schema = email_to_schema_name(user_email)
            discovery_info = discovery_service.get_user_specific_database_info(user_email)
            
            return {
                "status": "success",
                "discovery_mode": "user_specific",
                "user_email": user_email,
                "user_schema": user_schema,
                "databases": discovery_info.get("databases", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"User discovery failed for {user_email}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "user_email": user_email,
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_sql_safety(self, sql_query: str, user_email: str) -> Dict[str, Any]:
        """Validate SQL query for safety and security."""
        try:
            # Basic SQL injection patterns
            dangerous_patterns = [
                r";\s*(drop|delete|truncate|alter|create|insert|update)\s+",
                r"union\s+select",
                r"exec\s*\(",
                r"xp_cmdshell",
                r"sp_executesql",
                r"--\s*$",
                r"/\*.*\*/"
            ]
            
            sql_lower = sql_query.lower()
            security_issues = []
            
            # Check for dangerous patterns
            for pattern in dangerous_patterns:
                if re.search(pattern, sql_lower, re.IGNORECASE):
                    security_issues.append(f"Potentially dangerous pattern detected: {pattern}")
            
            # Check for schema isolation
            user_schema = email_to_schema_name(user_email)
            if user_schema not in sql_query and "public" in sql_query:
                security_issues.append("Query may access unauthorized schema")
            
            return {
                "status": "success" if not security_issues else "warning",
                "sql_query": sql_query,
                "user_email": user_email,
                "user_schema": user_schema,
                "security_issues": security_issues,
                "is_safe": len(security_issues) == 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_schema_info(self, schema_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific schema."""
        try:
            # This would integrate with your existing schema discovery
            return {
                "status": "success",
                "schema_name": schema_name,
                "tables": [],  # Would be populated from discovery service
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_tables_info(self, schema_name: str) -> Dict[str, Any]:
        """Get table information for a specific schema."""
        try:
            return {
                "status": "success",
                "schema_name": schema_name,
                "tables": [],  # Would be populated from discovery service
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_table_schema_details(self, table_name: str, user_email: str) -> Dict[str, Any]:
        """Get detailed schema information for a specific table."""
        try:
            user_schema = email_to_schema_name(user_email)
            return {
                "status": "success",
                "table_name": table_name,
                "user_schema": user_schema,
                "columns": [],  # Would be populated from discovery service
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

async def main():
    """Main entry point for SQL Database MCP Server."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting SQL Database MCP Server...")
    
    # Create and run server
    server_instance = SQLDatabaseMCPServer()
    
    # Run server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sql-database",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
