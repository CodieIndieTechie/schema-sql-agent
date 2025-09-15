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
        self.session_data_cache = {}  # Store query results for memory/plotting
        
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
    
    def store_session_data(self, session_id: str, query: str, data: Dict[str, Any]) -> None:
        """Store query results in session cache for future reference."""
        if session_id not in self.session_data_cache:
            self.session_data_cache[session_id] = []
        
        # Store with timestamp and query info
        import time
        cache_entry = {
            'timestamp': time.time(),
            'query': query,
            'data': data.get('sql_data', []),
            'raw_data': data.get('raw_data', []),
            'dataframe': data.get('dataframe', []),
            'response_text': data.get('sql_response', ''),
            'chart_type': data.get('chart_type'),
            'calculation_type': data.get('calculation_type')
        }
        
        self.session_data_cache[session_id].append(cache_entry)
        
        # Keep only last 10 queries to prevent memory bloat
        if len(self.session_data_cache[session_id]) > 10:
            self.session_data_cache[session_id] = self.session_data_cache[session_id][-10:]
        
        logger.info(f"💾 Stored session data for {session_id}: {len(self.session_data_cache[session_id])} entries")
    
    def get_previous_session_data(self, session_id: str, query_hint: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve previous query data from session cache."""
        if session_id not in self.session_data_cache or not self.session_data_cache[session_id]:
            return None
        
        # If no specific hint, return the most recent data
        if not query_hint:
            return self.session_data_cache[session_id][-1]
        
        # Try to find data matching the query hint
        query_hint_lower = query_hint.lower()
        for entry in reversed(self.session_data_cache[session_id]):
            if any(keyword in entry['query'].lower() for keyword in query_hint_lower.split()):
                return entry
        
        # Fallback to most recent
        return self.session_data_cache[session_id][-1]
    
    def _detect_plot_previous_request(self, query: str) -> bool:
        """Detect if user wants to plot data from previous queries."""
        plot_previous_keywords = [
            'plot previous', 'chart previous', 'graph previous', 'visualize previous',
            'plot that', 'chart that', 'graph that', 'visualize that',
            'plot the above', 'chart the above', 'graph the above',
            'plot last', 'chart last', 'graph last',
            'show chart', 'show graph', 'show plot'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in plot_previous_keywords)
    
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
            if schema_name and schema_name != 'public':
                if '?' in db_uri:
                    db_uri += f"&options=-csearch_path%3D{schema_name}"
                else:
                    db_uri += f"?options=-csearch_path%3D{schema_name}"
            elif database_name == 'mutual_fund':
                # Ensure public schema is used for mutual_fund database
                if '?' in db_uri:
                    db_uri += "&options=-csearch_path%3Dpublic"
                else:
                    db_uri += "?options=-csearch_path%3Dpublic"
            
            db = SQLDatabase.from_uri(db_uri)
            
            # Create SQL toolkit
            toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
            tools = toolkit.get_tools()
            
            # Generate dynamic prompt based on discovered database structure
            if database_name == 'mutual_fund':
                # Use specialized mutual fund prompt
                system_prompt = get_agent_prompt('mutual_fund')
                logger.info("🎯 Using specialized mutual fund system prompt")
            elif self.discovery_mode == 'user_specific' and self.user_email:
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
            
            # Create agent executor with enhanced settings for mutual fund database
            max_iterations = 100 if database_name == 'mutual_fund' else 75
            max_execution_time = 240 if database_name == 'mutual_fund' else 180
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=settings.debug,
                handle_parsing_errors=True,
                max_iterations=max_iterations,
                max_execution_time=max_execution_time,
                return_intermediate_steps=True,
            )
            
            logger.info(f"⚙️  Agent executor configured: max_iterations={max_iterations}, max_time={max_execution_time}s")
            
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
    
    def _determine_optimal_database(self, query: str) -> str:
        """
        Determine the optimal database for a given query based on content analysis.
        
        Args:
            query: Natural language query
            
        Returns:
            Database name that best matches the query intent
        """
        query_lower = query.lower()
        
        # Mutual fund related keywords
        mutual_fund_keywords = [
            'mutual fund', 'mf', 'nav', 'scheme', 'amc', 'fund house', 'sip', 'lumpsum',
            'equity', 'debt', 'hybrid', 'returns', 'performance', 'risk', 'volatility',
            'sharpe', 'sortino', 'alpha', 'beta', 'portfolio', 'holdings', 'expense ratio',
            'aum', 'benchmark', 'category', 'amfi', 'sebi', 'investment', 'dividend',
            'growth', 'direct', 'regular', 'exit load', 'minimum investment'
        ]
        
        # Check if query contains mutual fund keywords
        if any(keyword in query_lower for keyword in mutual_fund_keywords):
            # Check if mutual_fund database is available
            available_dbs = [db['name'] for db in self.database_info.get('databases', [])]
            if 'mutual_fund' in available_dbs:
                logger.info(f"🎯 Routing to mutual_fund database based on query content")
                return 'mutual_fund'
        
        # Default routing logic
        if self.database_info.get('current_database'):
            return self.database_info['current_database']
        elif self.database_info.get('databases'):
            return self.database_info['databases'][0]['name']
        else:
            return settings.portfoliosql_db_name
    
    def _determine_optimal_schema(self, database_name: str, query: str) -> Optional[str]:
        """
        Determine the optimal schema for a given database and query.
        
        Args:
            database_name: Target database name
            query: Natural language query
            
        Returns:
            Schema name or None for default schema
        """
        # For mutual_fund database, use public schema
        if database_name == 'mutual_fund':
            return 'public'
        
        # For other databases, use user schema if available
        if self.user_email:
            from schema_migration import email_to_schema_name
            return email_to_schema_name(self.user_email)
        
        return None
    
    def get_agent_for_context(self, database_name: Optional[str] = None, 
                            schema_name: Optional[str] = None,
                            query: Optional[str] = None) -> AgentExecutor:
        """
        Get or create an agent for the specified database/schema context.
        
        Args:
            database_name: Database name (auto-determined if not provided)
            schema_name: Schema name (auto-determined if not provided)
            query: Query text for intelligent routing
            
        Returns:
            AgentExecutor configured for the specified context
        """
        # Intelligent database routing based on query content
        if not database_name and query:
            database_name = self._determine_optimal_database(query)
        elif not database_name:
            if self.database_info.get('current_database'):
                database_name = self.database_info['current_database']
            elif self.database_info.get('databases'):
                database_name = self.database_info['databases'][0]['name']
            else:
                database_name = settings.portfoliosql_db_name
        
        # Intelligent schema routing
        if not schema_name:
            schema_name = self._determine_optimal_schema(database_name, query or "")
        
        # Create cache key
        cache_key = f"{database_name}:{schema_name or 'default'}"
        
        # Return cached agent if available
        if cache_key in self.agent_cache:
            logger.info(f"🔄 Using cached agent for: {cache_key}")
            return self.agent_cache[cache_key]
        
        # Create new agent
        agent = self._create_database_agent(database_name, schema_name)
        self.agent_cache[cache_key] = agent
        
        logger.info(f"💾 Cached new agent for: {cache_key} (DB: {database_name}, Schema: {schema_name})")
        return agent
    
    def _extract_sql_data_from_result(self, result: Dict[str, Any]) -> List[List[Any]]:
        """
        Extract structured data from SQL agent result.
        
        Args:
            result: Result dictionary from SQL agent execution
                
        Returns:
            List of rows containing the SQL query results
        """
        try:
            # Try to extract from intermediate steps first
            if 'intermediate_steps' in result:
                for step in result['intermediate_steps']:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        if hasattr(action, 'tool') and 'sql' in action.tool.lower():
                            # This is a SQL execution step
                            parsed_data = self._parse_observation_to_data(str(observation))
                            if parsed_data:
                                logger.info(f"✅ Extracted {len(parsed_data)} rows from SQL execution")
                                return parsed_data
            
            # Fallback: try to parse from output
            if 'output' in result:
                parsed_data = self._parse_observation_to_data(result['output'])
                if parsed_data:
                    logger.info(f"✅ Extracted {len(parsed_data)} rows from output")
                    return parsed_data
            
            # If no structured data found, try to extract from formatted response
            output_text = result.get('output', '')
            if any(keyword in output_text.lower() for keyword in ['chart', 'visualization', 'graph', 'plot']):
                # Look for mutual fund data patterns in the response
                import re
                
                # Try multiple patterns to extract mutual fund data
                patterns = [
                    # Pattern for numbered lists: "1. Fund Name - ₹123.45"
                    r'\d+\.\s*([^-\n]+?)\s*-\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)',
                    # Pattern for bold format: "**Fund Name**: ₹123.45"
                    r'\*\*([^*]+)\*\*:\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)',
                    # Pattern for simple format: "Fund Name: 123.45"
                    r'([A-Za-z][^:\n]{15,}?):\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)'
                ]
                
                extracted_data = []
                for pattern in patterns:
                    matches = re.findall(pattern, output_text)
                    if matches and len(matches) >= 3:  # Need at least 3 matches
                        seen_names = set()
                        for name, value in matches:
                            clean_name = name.strip()
                            if clean_name and clean_name not in seen_names and len(clean_name) > 5:
                                seen_names.add(clean_name)
                                clean_value = value.replace(',', '')
                                try:
                                    extracted_data.append([clean_name, float(clean_value)])
                                except:
                                    continue
                        if extracted_data:
                            logger.info(f"✅ Extracted {len(extracted_data)} mutual fund entries from response")
                            return extracted_data
                
                # Fallback to simple pattern if nothing else works
                pattern = r'(\w+)\s*[=:]\s*(\d+(?:\.\d+)?)'
                matches = re.findall(pattern, output_text)
                if matches:
                    synthetic_data = []
                    for name, value in matches:
                        synthetic_data.append([name, float(value)])
                    logger.info(f"✅ Created synthetic data with {len(synthetic_data)} rows")
                    return synthetic_data
            
            logger.warning("⚠️ No structured data found in SQL result")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting SQL data: {e}")
            return []
    
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
    
    def _should_call_quant_agent(self, query: str, sql_data: List[List[Any]]) -> bool:
        """
        Determine if the Mutual Fund Quant Agent should be called based on query and data.
        
        Args:
            query: User's natural language query
            sql_data: Extracted SQL data
            
        Returns:
            Boolean indicating if quant analysis is needed
        """
        query_lower = query.lower()
        
        # Financial analysis keywords
        quant_keywords = [
            'risk', 'volatility', 'sharpe', 'beta', 'correlation', 'performance', 
            'returns', 'statistics', 'analysis', 'calculate', 'compare', 'trend',
            'average', 'mean', 'median', 'standard deviation', 'variance',
            'growth', 'roi', 'profit', 'loss', 'drawdown', 'ratio'
        ]
        
        # Check if query contains financial analysis keywords
        has_quant_keywords = any(keyword in query_lower for keyword in quant_keywords)
        
        # Check if data is suitable for quantitative analysis (has numeric data)
        has_numeric_data = len(sql_data) > 0 and (len(sql_data[0]) >= 2 if sql_data else False)
        
        # Call quant agent if both conditions are met
        should_call = has_quant_keywords and has_numeric_data
        
        logger.info(f"🔍 Quant decision: keywords={has_quant_keywords}, numeric_data={has_numeric_data}, should_call={should_call}")
        logger.info(f"📊 Data structure: {len(sql_data)} rows, {len(sql_data[0]) if sql_data else 0} columns")
        
        if should_call:
            logger.info(f"🧮 Quant Agent will be called - detected financial analysis need")
        else:
            logger.info(f"❌ Quant Agent will NOT be called")
        
        return should_call
    
    def _should_call_formatter_agent(self, query: str, sql_data: List[List[Any]]) -> bool:
        """
        Determine if the Data Formatter Agent should be called based on query and data.
        
        Args:
            query: User's natural language query
            sql_data: Extracted SQL data
            
        Returns:
            Boolean indicating if visualization/formatting is needed
        """
        query_lower = query.lower()
        
        # Visualization keywords
        viz_keywords = [
            'chart', 'graph', 'plot', 'visualize', 'visualization', 'show me',
            'display', 'draw', 'bar chart', 'line chart', 'pie chart', 
            'scatter plot', 'histogram', 'dashboard', 'report'
        ]
        
        # Check if query explicitly requests visualization
        has_viz_keywords = any(keyword in query_lower for keyword in viz_keywords)
        
        # Check if data is suitable for visualization (reasonable size and structure)
        has_chartable_data = (
            len(sql_data) >= 1 and 
            len(sql_data) <= 100 and  # Not too large for charts
            len(sql_data[0]) >= 2 if sql_data else False     # At least 2 columns
        )
        
        # Also call formatter for comparison queries with good data
        has_comparison = any(word in query_lower for word in ['compare', 'vs', 'versus', 'against', 'difference'])
        
        should_call = (has_viz_keywords and has_chartable_data) or (has_comparison and has_chartable_data)
        
        logger.info(f"🔍 Formatter decision: viz_keywords={has_viz_keywords}, chartable_data={has_chartable_data}, comparison={has_comparison}, should_call={should_call}")
        
        if should_call:
            logger.info(f"📊 Formatter Agent will be called - detected visualization need")
        else:
            logger.info(f"❌ Formatter Agent will NOT be called")
        
        return should_call
    
    def _coordinate_agents(self, query: str, sql_data: Dict[str, Any], force_visualization: bool = False) -> Dict[str, Any]:
        """
        Coordinate calls to conditional agents based on query analysis and data.
        
        Args:
            query: User's natural language query
            sql_data: SQL execution results
            force_visualization: Force visualization even if not detected in query
            
        Returns:
            Enhanced response with quant analysis and/or visualization
        """
        try:
            logger.info("🎼 Starting agent coordination...")
            
            # Extract raw data for analysis
            raw_data = sql_data.get('sql_data', [])
            logger.info(f"📊 Raw data extracted: {len(raw_data)} rows")
            
            # If no structured data, try to extract from SQL response text
            if not raw_data:
                sql_response = sql_data.get('sql_response', '')
                logger.info(f"🔍 Attempting to extract data from SQL response text...")
                
                # Try to extract structured data from the response (always try, not just for visualization queries)
                if sql_response:
                    # Look for data patterns in the response
                    import re
                    
                    # Multiple patterns to handle different response formats
                    patterns = [
                        # Pattern 1: "**Name** with a NAV/AUM/Value of Value"
                        (r'\*\*([^*]+)\*\*\s+with\s+a\s+(?:NAV|AUM|value|price)\s+of\s+[₹$]?([0-9,]+(?:\.[0-9]+)?)', 'with_value_format'),
                        # Pattern 2: "**Name**: ₹Value" or "**Name**: Value"
                        (r'\*\*([^*]+)\*\*:\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)', 'bold_colon'),
                        # Pattern 3: "Name - Value" format
                        (r'([A-Za-z][^-\n]+?)\s*-\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)', 'dash_format'),
                        # Pattern 4: Numbered list "1. Name - Value"
                        (r'\d+\.\s*([^-\n]+?)\s*-\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)', 'numbered_list'),
                        # Pattern 5: "Name=Value" or "Name: Value"
                        (r'([A-Za-z]\w+)\s*[=:]\s*([0-9,]+(?:\.[0-9]+)?)', 'simple_format')
                    ]
                    
                    raw_data = []
                    extraction_method = None
                    
                    for pattern, method_name in patterns:
                        matches = re.findall(pattern, sql_response)
                        if matches and len(matches) >= 3:  # Need at least 3 matches for meaningful data
                            seen_names = set()
                            for name, value in matches:
                                clean_name = name.strip()
                                # Skip duplicates and invalid names
                                if clean_name and clean_name not in seen_names and len(clean_name) > 2:
                                    seen_names.add(clean_name)
                                    clean_value = value.replace(',', '')
                                    try:
                                        raw_data.append([clean_name, float(clean_value)])
                                    except:
                                        raw_data.append([clean_name, clean_value])
                            
                            if raw_data:
                                extraction_method = method_name
                                logger.info(f"✅ Extracted {len(raw_data)} unique data points using {method_name}")
                                break
                    
                    # If no pattern worked, try a more lenient approach
                    if not raw_data:
                        # Look for any text followed by numbers
                        fallback_pattern = r'([A-Za-z][^0-9\n]{10,}?)\s*[:\-]?\s*[₹$]?([0-9,]+(?:\.[0-9]+)?)'
                        matches = re.findall(fallback_pattern, sql_response)
                        if matches:
                            seen_names = set()
                            for name, value in matches[:10]:  # Limit to 10 to avoid noise
                                clean_name = name.strip()
                                if clean_name and clean_name not in seen_names:
                                    seen_names.add(clean_name)
                                    clean_value = value.replace(',', '')
                                    try:
                                        raw_data.append([clean_name, float(clean_value)])
                                    except:
                                        continue
                            logger.info(f"✅ Extracted {len(raw_data)} data points using fallback pattern")
            
            if raw_data:
                logger.info(f"📊 Sample row: {raw_data[0][:3] if len(raw_data[0]) > 3 else raw_data[0]}")
            else:
                logger.warning("⚠️ No raw data found in sql_data or response text")
            
            # Initialize response with SQL results
            final_response = sql_data.copy()
            
            # Conditional Edge 1: Call Quant Agent if needed
            logger.info(f"🔍 Checking if quant agent should be called for query: '{query[:50]}...'")
            logger.info(f"📊 Raw data size: {len(raw_data)} rows")
            
            if self._should_call_quant_agent(query, raw_data):
                try:
                    from agents.mutual_fund_quant_agent import MutualFundQuantAgent
                    quant_agent = MutualFundQuantAgent()
                    
                    logger.info("🧮 Calling Mutual Fund Quant Agent...")
                    quant_result = quant_agent.process_data(sql_data, query)
                    
                    if quant_result.get('success', False):
                        # Merge quant analysis into response
                        final_response['calculations'] = quant_result.get('calculations', {})
                        final_response['insights'] = quant_result.get('insights', [])
                        final_response['calculation_type'] = quant_result.get('calculation_type')
                        final_response['dataframe_info'] = quant_result.get('dataframe_info', {})
                        final_response['dataframe'] = quant_result.get('dataframe', [])
                        
                        # Update SQL response with insights
                        if quant_result.get('insights'):
                            insights_text = "\n".join(quant_result['insights'])
                            final_response['sql_response'] += f"\n\n{insights_text}"
                        
                        logger.info("✅ Quant Agent processing completed")
                    else:
                        logger.warning(f"⚠️ Quant Agent failed: {quant_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Quant Agent coordination failed: {e}")
            
            # Conditional Edge 2: Call Formatter Agent if needed
            logger.info(f"🔍 Checking if formatter agent should be called for query: '{query[:50]}...'")
            
            if self._should_call_formatter_agent(query, raw_data) or force_visualization:
                if force_visualization:
                    logger.info("🎯 Forcing visualization for previous data plotting")
                try:
                    from agents.data_formatter_agent import DataFormatterAgent
                    formatter_agent = DataFormatterAgent(static_dir="static/charts")
                    
                    logger.info("📊 Calling Data Formatter Agent...")
                    
                    # Prepare data for formatter (use quant results if available)
                    if final_response.get('calculations') and final_response.get('dataframe_info'):
                        # Use quant agent results
                        formatter_input = {
                            'success': True,
                            'dataframe': final_response.get('dataframe', []),
                            'calculations': final_response.get('calculations', {}),
                            'insights': final_response.get('insights', []),
                            'calculation_type': final_response.get('calculation_type'),
                            'dataframe_info': final_response.get('dataframe_info', {}),
                            'original_sql_data': sql_data,
                            'query': query
                        }
                    else:
                        # For regex-extracted data, always use meaningful column names
                        if raw_data and len(raw_data) > 0:
                            first_row = raw_data[0]
                            if len(first_row) == 2:
                                # Assume it's name-value pairs (common for mutual fund data)
                                columns = ['Name', 'Value']
                                data_rows = raw_data
                            else:
                                # Generate meaningful column names based on data structure
                                columns = ['Name', 'Value'] if len(first_row) == 2 else [f'Column_{i+1}' for i in range(len(first_row))]
                                data_rows = raw_data
                        else:
                            columns = ['Name', 'Value']
                            data_rows = []                       
                        dataframe_records = [dict(zip(columns, row)) for row in data_rows]
                        formatter_input = {
                            'success': True,
                            'dataframe': dataframe_records,
                            'calculations': {},
                            'insights': [],
                            'calculation_type': None,
                            'dataframe_info': {
                                'shape': (len(dataframe_records), len(dataframe_records[0]) if dataframe_records else 0),
                                'columns': list(dataframe_records[0].keys()) if dataframe_records else []
                            },
                            'original_sql_data': sql_data,
                            'query': query
                        }
                    
                    formatter_result = formatter_agent.process_data(formatter_input, query)
                    
                    if formatter_result.get('success', False):
                        # Delegate ALL output formatting to Data Formatter Agent
                        final_response['chart_files'] = formatter_result.get('chart_files', [])
                        final_response['chart_file'] = formatter_result.get('chart_file')
                        final_response['chart_type'] = formatter_result.get('chart_type')
                        final_response['data_table'] = formatter_result.get('data_table')
                        
                        # Use ONLY the formatter's response (it handles all text formatting and cleanup)
                        if formatter_result.get('response'):
                            final_response['sql_response'] = formatter_result['response']
                        
                        logger.info("✅ Formatter Agent processing completed - delegated all output formatting")
                    else:
                        logger.warning(f"⚠️ Formatter Agent failed: {formatter_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Formatter Agent coordination failed: {e}")
            
            # Ensure raw_data is included in the final response for session storage
            if raw_data and not final_response.get('raw_data'):
                final_response['raw_data'] = raw_data
            
            logger.info("🎉 Agent coordination completed")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Agent coordination failed: {e}")
            return sql_data  # Return original SQL data on coordination failure
    
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
            
            # Check if user wants to plot previous data
            if self._detect_plot_previous_request(query):
                logger.info("🔍 Detected request to plot previous data")
                previous_data = self.get_previous_session_data(session_id, query)
                
                if previous_data:
                    logger.info(f"📊 Found previous data to plot: {previous_data['query'][:50]}...")
                    
                    # Create response using previous data
                    response_data = {
                        'success': True,
                        'sql_response': f"Plotting data from previous query: {previous_data['query'][:100]}...",
                        'sql_data': previous_data['data'],
                        'raw_data': previous_data['raw_data'],
                        'dataframe': previous_data['dataframe'],
                        'database': database_name or settings.portfoliosql_db_name,
                        'schema': schema_name or user_schema,
                        'session_id': session_id,
                        'query': query,
                        'original_query': previous_data['query'],
                        'data_summary': {
                            'row_count': len(previous_data['data']),
                            'column_count': len(previous_data['data'][0]) if previous_data['data'] else 0,
                            'has_data': len(previous_data['data']) > 0
                        }
                    }
                    
                    # Force visualization by calling formatter agent directly
                    enhanced_response = self._coordinate_agents(query, response_data, force_visualization=True)
                    return enhanced_response
                else:
                    logger.warning("⚠️ No previous data found to plot")
                    return {
                        'success': False,
                        'error': "No previous query data found to plot",
                        'sql_response': "I don't have any previous query results to plot. Please run a data query first, then ask me to plot it.",
                        'sql_data': [],
                        'session_id': session_id,
                        'query': query
                    }
            
            # Normal query processing
            # Get appropriate agent for the context with intelligent routing
            agent = self.get_agent_for_context(database_name, schema_name, query)
            
            # Execute the query
            result = agent.invoke(
                {"input": query},
                config={"configurable": {"session_id": session_id}}
            )
            
            logger.info("✅ SQL query executed successfully")
            
            # Extract SQL data from result
            sql_data = self._extract_sql_data_from_result(result)
            
            # Prepare structured response
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
            
            # Graph-based agent coordination: Call conditional agents if needed
            enhanced_response = self._coordinate_agents(query, response_data)
            
            # Store query results in session cache for future plotting
            if enhanced_response.get('success') and (enhanced_response.get('sql_data') or enhanced_response.get('raw_data')):
                self.store_session_data(session_id, query, enhanced_response)
            
            return enhanced_response
            
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
