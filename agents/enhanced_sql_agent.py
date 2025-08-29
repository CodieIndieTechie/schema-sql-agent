#!/usr/bin/env python3
"""
Enhanced SQL Agent - Focused on database operations only

This agent handles:
- Database discovery and connection management
- SQL query generation and execution
- Database context management
- Orchestrating the data flow to next agents
"""

import logging
from typing import Dict, List, Optional, Any, Union
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import pandas as pd
import uuid

from settings import settings
from database_discovery import discovery_service
from agent_prompts import get_agent_prompt

logger = logging.getLogger(__name__)


class EnhancedSQLAgent:
    """
    Enhanced SQL Agent focused purely on database operations.
    
    Responsibilities:
    - Database discovery and connection management
    - SQL query generation and execution
    - Context-aware database operations
    - Orchestrating data flow to calculation and visualization agents
    """
    
    def __init__(self, user_email: Optional[str] = None, discovery_mode: str = 'comprehensive'):
        """
        Initialize the Enhanced SQL Agent.
        
        Args:
            user_email: User's email for schema-per-tenant architecture
            discovery_mode: Database discovery mode ('user_specific', 'comprehensive', 'minimal')
        """
        self.user_email = user_email
        self.discovery_mode = discovery_mode
        self.llm = ChatOpenAI(
            model_name=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
            max_tokens=settings.openai_max_tokens
        )
        
        # Database discovery and context
        self.database_info = {}
        self.agent_cache = {}
        self.session_histories = {}
        
        # Initialize database discovery
        self._initialize_database_discovery()
        
        logger.info(f"🤖 Enhanced SQL Agent initialized for user: {user_email or 'system'}")
        logger.info(f"🔍 Discovery mode: {discovery_mode}")
    
    def _initialize_database_discovery(self):
        """Initialize database discovery based on the discovery mode."""
        try:
            if self.discovery_mode == 'user_specific' and self.user_email:
                # Discover user's specific schema and related databases
                from schema_migration import email_to_schema_name
                user_schema = email_to_schema_name(self.user_email)
                
                self.database_info = discovery_service.get_user_specific_database_info(
                    user_email=self.user_email
                )
                logger.info(f"🔍 User-specific discovery completed for schema: {user_schema}")
                
            elif self.discovery_mode == 'comprehensive':
                # Discover all available databases and schemas
                self.database_info = discovery_service.get_comprehensive_database_info(
                    include_columns=False,  # Skip columns for faster discovery
                    max_tables_per_schema=500
                )
                logger.info("🔍 Comprehensive database discovery completed")
                
            elif self.discovery_mode == 'minimal':
                # Minimal discovery - just primary database (fallback to user-specific)
                self.database_info = discovery_service.get_user_specific_database_info(
                    user_email=self.user_email or "default@example.com"
                )
                logger.info("🔍 Minimal database discovery completed")
            
            # Log discovery results
            if self.database_info:
                db_count = len(self.database_info.get('databases', []))
                schema_count = sum(len(db.get('schemas', [])) for db in self.database_info.get('databases', []))
                table_count = self.database_info.get('total_tables', 0)
                
                logger.info(f"📊 Discovery Results: {db_count} databases, {schema_count} schemas, {table_count} tables")
            
        except Exception as e:
            logger.error(f"❌ Database discovery failed: {e}")
            # Fallback to basic discovery
            self.database_info = {"databases": [{"name": settings.portfoliosql_db_name}]}
    
    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get or create a session history for the given session ID."""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()
            logger.info(f"📝 Created new session history for: {session_id}")
        return self.session_histories[session_id]
    
    def clear_session_history(self, session_id: str) -> bool:
        """Clear session history for a given session ID."""
        if session_id in self.session_histories:
            del self.session_histories[session_id]
            logger.info(f"🗑️  Cleared session history for {session_id}")
            return True
        return False
    
    def _create_database_agent(self, database_name: str, schema_name: Optional[str] = None) -> AgentExecutor:
        """
        Create a SQL agent for a specific database and schema.
        
        Args:
            database_name: Name of the database to connect to
            schema_name: Optional schema name for focused operations
            
        Returns:
            Configured AgentExecutor for the specified database/schema
        """
        try:
            # Create database connection
            db_uri = settings.get_database_uri(database_name)
            
            # Add schema to connection if specified
            if schema_name:
                db_uri += f"?options=-csearch_path%3D{schema_name}"
            
            db = SQLDatabase.from_uri(db_uri)
            
            # Create SQL toolkit
            toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
            tools = toolkit.get_tools()
            
            # Generate dynamic prompt based on discovered database structure
            if self.discovery_mode == 'user_specific' and self.user_email:
                system_prompt = get_agent_prompt('dynamic', 
                                                database_info=self.database_info, 
                                                user_schema=schema_name)
            else:
                system_prompt = get_agent_prompt('dynamic', database_info=self.database_info)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent
            agent = create_tool_calling_agent(self.llm, tools, prompt)
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=settings.debug,
                handle_parsing_errors=True,
                max_iterations=25,
                max_execution_time=90,
                return_intermediate_steps=True,
            )
            
            # Wrap with message history
            agent_with_history = RunnableWithMessageHistory(
                agent_executor,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            logger.info(f"✅ Created SQL agent for {database_name}" + (f".{schema_name}" if schema_name else ""))
            return agent_with_history
            
        except Exception as e:
            logger.error(f"❌ Failed to create SQL agent for {database_name}" + (f".{schema_name}" if schema_name else "") + f": {e}")
            raise
    
    def get_agent_for_context(self, database_name: Optional[str] = None, 
                            schema_name: Optional[str] = None) -> AgentExecutor:
        """
        Get or create an agent for the specified database/schema context.
        
        Args:
            database_name: Database name (defaults to primary database)
            schema_name: Schema name (defaults to user schema if available)
            
        Returns:
            AgentExecutor configured for the specified context
        """
        # Determine default context
        if not database_name:
            if self.database_info.get('current_database'):
                database_name = self.database_info['current_database']
            elif self.database_info.get('databases'):
                database_name = self.database_info['databases'][0]['name']
            else:
                database_name = settings.portfoliosql_db_name
        
        if not schema_name and self.user_email:
            from schema_migration import email_to_schema_name
            schema_name = email_to_schema_name(self.user_email)
        
        # Create cache key
        cache_key = f"{database_name}:{schema_name or 'default'}"
        
        # Return cached agent if available
        if cache_key in self.agent_cache:
            logger.info(f"🔄 Using cached agent for: {cache_key}")
            return self.agent_cache[cache_key]
        
        # Create new agent
        agent = self._create_database_agent(database_name, schema_name)
        self.agent_cache[cache_key] = agent
        
        logger.info(f"💾 Cached new agent for: {cache_key}")
        return agent
    
    def _extract_sql_data_from_result(self, result: Dict[str, Any]) -> List[List[Any]]:
        """
        Extract tabular data from SQL agent execution result.
        
        Args:
            result: Result from SQL agent execution
            
        Returns:
            List of rows, where each row is a list of values
        """
        sql_data = []
        
        try:
            # Look for data in intermediate steps
            intermediate_steps = result.get("intermediate_steps", [])
            
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # Check if observation contains SQL query results
                    if observation and isinstance(observation, str):
                        # Try to parse the observation for SQL results
                        if "rows" in observation.lower() or "result" in observation.lower():
                            parsed_data = self._parse_observation_to_data(observation)
                            if parsed_data:
                                sql_data.extend(parsed_data)
                                break
        
        except Exception as e:
            logger.error(f"Error extracting SQL data: {e}")
        
        return sql_data
    
    def _parse_observation_to_data(self, observation: str) -> List[List[Any]]:
        """
        Parse SQL agent observation into structured data.
        
        Args:
            observation: String observation from SQL execution
            
        Returns:
            Parsed data as list of rows
        """
        try:
            # Look for patterns that indicate SQL results
            lines = observation.split('\n')
            data_rows = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and '|' in line:
                    # Looks like table data - split by pipe
                    row_data = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty cells from split
                    if row_data:
                        data_rows.append(row_data)
                elif line.startswith('(') and line.endswith(')'):
                    # Looks like tuple data
                    try:
                        # Simple parsing for tuple-like strings
                        clean_line = line.strip('()')
                        if ',' in clean_line:
                            row_data = [item.strip().strip("'\"") for item in clean_line.split(',')]
                            data_rows.append(row_data)
                    except:
                        continue
            
            return data_rows
            
        except Exception as e:
            logger.error(f"Error parsing observation: {e}")
            return []
    
    def process_query(self, query: str, session_id: Optional[str] = None, 
                     database_name: Optional[str] = None, 
                     schema_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a SQL query and return structured data for next agents.
        
        Args:
            query: Natural language query
            session_id: Optional session ID for conversation tracking
            database_name: Optional specific database to query
            schema_name: Optional specific schema to use
            
        Returns:
            Dictionary containing SQL results and metadata for next agents
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get user schema from email if needed
        user_schema = None
        if self.user_email:
            from schema_migration import email_to_schema_name
            user_schema = email_to_schema_name(self.user_email)
        
        try:
            logger.info(f"🔍 Processing SQL query: {query[:100]}...")
            
            # Get appropriate agent for the context
            agent = self.get_agent_for_context(database_name, schema_name)
            
            # Execute the query
            result = agent.invoke(
                {"input": query},
                config={"configurable": {"session_id": session_id}}
            )
            
            logger.info("✅ SQL query executed successfully")
            
            # Extract SQL data from result
            sql_data = self._extract_sql_data_from_result(result)
            
            # Prepare structured response for next agents
            response_data = {
                'success': True,
                'sql_response': result.get("output", ""),
                'sql_data': sql_data,
                'database': database_name or settings.portfoliosql_db_name,
                'schema': schema_name or user_schema,
                'session_id': session_id,
                'intermediate_steps': result.get("intermediate_steps", []),
                'query': query,
                'data_summary': {
                    'row_count': len(sql_data),
                    'column_count': len(sql_data[0]) if sql_data else 0,
                    'has_data': len(sql_data) > 0
                }
            }
            
            logger.info(f"📊 SQL data extracted: {len(sql_data)} rows")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ SQL query processing failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'sql_response': f"I encountered an error while processing your query: {str(e)}",
                'sql_data': [],
                'database': database_name or settings.portfoliosql_db_name,
                'schema': schema_name or user_schema,
                'session_id': session_id,
                'query': query,
                'data_summary': {
                    'row_count': 0,
                    'column_count': 0,
                    'has_data': False
                }
            }
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get current database discovery information."""
        return self.database_info
    
    def get_available_databases(self) -> List[str]:
        """Get list of available database names."""
        return [db['name'] for db in self.database_info.get('databases', [])]
    
    def get_available_schemas(self, database_name: str) -> List[str]:
        """Get list of available schemas for a database."""
        for db in self.database_info.get('databases', []):
            if db['name'] == database_name:
                return [schema['name'] for schema in db.get('schemas', [])]
        return []
    
    def clear_agent_cache(self):
        """Clear the agent cache to force recreation of agents."""
        self.agent_cache.clear()
        logger.info("🗑️  Agent cache cleared")


# Factory functions for creating SQL agents
def create_enhanced_sql_agent(user_email: str) -> EnhancedSQLAgent:
    """Create an enhanced SQL agent for a specific user."""
    return EnhancedSQLAgent(user_email=user_email, discovery_mode='user_specific')


def create_system_sql_agent() -> EnhancedSQLAgent:
    """Create an enhanced SQL agent for system-wide access."""
    return EnhancedSQLAgent(discovery_mode='comprehensive')


def create_minimal_sql_agent() -> EnhancedSQLAgent:
    """Create an enhanced SQL agent with minimal discovery for performance."""
    return EnhancedSQLAgent(discovery_mode='minimal')
