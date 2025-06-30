#!/usr/bin/env python3
"""
Enhanced Multi-Database SQL Agent

An enhanced SQL agent that can dynamically connect to multiple databases,
schemas, and tables with comprehensive discovery capabilities.
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

from settings import settings
from database_discovery import discovery_service
from agent_prompts import get_agent_prompt

logger = logging.getLogger(__name__)


class EnhancedMultiDatabaseSQLAgent:
    """
    Enhanced SQL Agent with dynamic multi-database capabilities.
    
    Features:
    - Dynamic database discovery
    - Multi-database access
    - Schema-aware operations  
    - Intelligent prompt generation
    - User-specific context
    """
    
    def __init__(self, user_email: Optional[str] = None, discovery_mode: str = 'user_specific'):
        """
        Initialize the enhanced SQL agent.
        
        Args:
            user_email: User's email for schema-per-tenant architecture
            discovery_mode: 'user_specific', 'comprehensive', or 'minimal'
        """
        self.user_email = user_email
        self.discovery_mode = discovery_mode
        self.database_info = {}
        self.agents_cache = {}  # Cache agents per database/schema combination
        self.session_histories = {}
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Perform initial discovery
        self._discover_databases()
        
        logger.info(f"✅ Enhanced SQL Agent initialized for {user_email or 'system'} in {discovery_mode} mode")
    
    def _discover_databases(self):
        """Discover database structures based on the configured mode."""
        try:
            if self.discovery_mode == 'user_specific' and self.user_email:
                logger.info(f"🔍 Performing user-specific discovery for {self.user_email}")
                self.database_info = discovery_service.get_user_specific_database_info(self.user_email)
                
            elif self.discovery_mode == 'comprehensive':
                logger.info("🔍 Performing comprehensive database discovery")
                self.database_info = discovery_service.get_comprehensive_database_info(include_columns=True)
                
            elif self.discovery_mode == 'minimal':
                logger.info("🔍 Performing minimal database discovery")
                self.database_info = discovery_service.get_comprehensive_database_info(include_columns=False)
                
            else:
                logger.warning("⚠️  Unknown discovery mode, falling back to minimal")
                self.database_info = discovery_service.get_comprehensive_database_info(include_columns=False)
                
            logger.info(f"✅ Database discovery complete: {len(self.database_info.get('databases', []))} databases discovered")
            
        except Exception as e:
            logger.error(f"❌ Database discovery failed: {e}")
            self.database_info = {'databases': [], 'error': str(e)}
    
    def refresh_discovery(self):
        """Refresh database discovery information."""
        logger.info("🔄 Refreshing database discovery...")
        self.database_info = {}
        self.agents_cache = {}  # Clear agent cache to rebuild with new info
        self._discover_databases()
    
    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Get or create session history for a given session ID."""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = ChatMessageHistory()
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
                max_iterations=15,
                max_execution_time=60,
                early_stopping_method="generate",
                return_intermediate_steps=True,
            )
            
            # Wrap with message history
            agent_with_history = RunnableWithMessageHistory(
                agent_executor,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            logger.info(f"✅ Created agent for {database_name}" + (f".{schema_name}" if schema_name else ""))
            return agent_with_history
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent for {database_name}" + (f".{schema_name}" if schema_name else "") + f": {e}")
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
            schema_name = self.database_info.get('user_schema') or self.database_info.get('current_schema')
        
        # Create cache key
        cache_key = f"{database_name}:{schema_name or 'default'}"
        
        # Get or create agent
        if cache_key not in self.agents_cache:
            self.agents_cache[cache_key] = self._create_database_agent(database_name, schema_name)
        
        return self.agents_cache[cache_key]
    
    def process_query(self, query: str, database_name: Optional[str] = None, 
                     schema_name: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a natural language query using the appropriate database agent.
        
        Args:
            query: Natural language query
            database_name: Optional database name
            schema_name: Optional schema name  
            session_id: Session ID for conversation history
            
        Returns:
            Query result dictionary
        """
        try:
            # Get appropriate agent
            agent = self.get_agent_for_context(database_name, schema_name)
            
            # Use user email as session ID if not provided
            if not session_id:
                session_id = self.user_email or "default_session"
            
            # Process query
            logger.info(f"🤖 Processing query for session {session_id}")
            result = agent.invoke(
                {"input": query},
                config={"configurable": {"session_id": session_id}}
            )
            
            # Get user schema from email if needed
            user_schema = None
            if self.user_email:
                from schema_migration import email_to_schema_name
                user_schema = email_to_schema_name(self.user_email)
            
            return {
                'success': True,
                'response': result.get("output", ""),
                'database': database_name,
                'schema': schema_name or user_schema,
                'session_id': session_id,
                'intermediate_steps': result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            
            # Get user schema from email if needed
            user_schema = None
            if self.user_email:
                from schema_migration import email_to_schema_name
                user_schema = email_to_schema_name(self.user_email)
            
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error while processing your query: {str(e)}",
                'database': database_name,
                'schema': schema_name or user_schema,
                'session_id': session_id
            }
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get a summary of discovered database structures."""
        if not self.database_info.get('databases'):
            return {'error': 'No database information available'}
        
        summary = {
            'total_databases': len(self.database_info['databases']),
            'databases': [],
            'discovery_mode': self.discovery_mode,
            'user_email': self.user_email
        }
        
        for db in self.database_info['databases']:
            db_summary = {
                'name': db['name'],
                'schema_count': len(db.get('schemas', [])),
                'accessible': db.get('accessible', True)
            }
            
            total_tables = 0
            for schema in db.get('schemas', []):
                total_tables += len(schema.get('tables', []))
            
            db_summary['total_tables'] = total_tables
            summary['databases'].append(db_summary)
        
        return summary
    
    def list_available_contexts(self) -> List[Dict[str, str]]:
        """
        List all available database/schema contexts for querying.
        
        Returns:
            List of available contexts with database and schema names
        """
        contexts = []
        
        for db in self.database_info.get('databases', []):
            if not db.get('accessible', True):
                continue
                
            db_name = db['name']
            
            for schema in db.get('schemas', []):
                schema_name = schema['name']
                table_count = len(schema.get('tables', []))
                
                contexts.append({
                    'database': db_name,
                    'schema': schema_name,
                    'table_count': table_count,
                    'is_user_schema': schema.get('is_user_schema', False),
                    'context_id': f"{db_name}.{schema_name}"
                })
        
        return contexts
    
    def get_schema_info(self, database_name: str, schema_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific schema."""
        for db in self.database_info.get('databases', []):
            if db['name'] == database_name:
                for schema in db.get('schemas', []):
                    if schema['name'] == schema_name:
                        return {
                            'database': database_name,
                            'schema': schema_name,
                            'tables': schema.get('tables', []),
                            'table_count': len(schema.get('tables', [])),
                            'is_user_schema': schema.get('is_user_schema', False)
                        }
        
        return {'error': f'Schema {schema_name} not found in database {database_name}'}


# Factory functions for creating agents
def create_enhanced_user_agent(user_email: str) -> EnhancedMultiDatabaseSQLAgent:
    """Create an enhanced agent for a specific user."""
    return EnhancedMultiDatabaseSQLAgent(user_email=user_email, discovery_mode='user_specific')


def create_enhanced_system_agent() -> EnhancedMultiDatabaseSQLAgent:
    """Create an enhanced agent for system-wide access."""
    return EnhancedMultiDatabaseSQLAgent(discovery_mode='comprehensive')


def create_enhanced_minimal_agent() -> EnhancedMultiDatabaseSQLAgent:
    """Create an enhanced agent with minimal discovery for performance."""
    return EnhancedMultiDatabaseSQLAgent(discovery_mode='minimal')


if __name__ == "__main__":
    # Test the enhanced agent
    import json
    
    print("=== ENHANCED SQL AGENT TEST ===")
    
    # Test user-specific agent
    test_email = "test@example.com"
    print(f"\n1. Creating user-specific agent for {test_email}...")
    
    try:
        agent = create_enhanced_user_agent(test_email)
        
        # Get database summary
        summary = agent.get_database_summary()
        print(f"Database summary: {json.dumps(summary, indent=2)}")
        
        # List available contexts
        contexts = agent.list_available_contexts()
        print(f"Available contexts: {len(contexts)}")
        for context in contexts[:3]:  # Show first 3
            print(f"  - {context['context_id']} ({context['table_count']} tables)")
        
        print("✅ Enhanced agent test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
