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
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html
import uuid
import os
import re

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
    
    def _is_chart_request(self, query: str) -> bool:
        """Detect if the user is requesting a chart/visualization."""
        chart_keywords = [
            'chart', 'graph', 'plot', 'visualize', 'draw', 'show chart',
            'bar chart', 'pie chart', 'line chart', 'scatter plot',
            'histogram', 'box plot', 'heatmap', 'visualization'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in chart_keywords)
    
    def _extract_sql_data_from_result(self, result: Dict[str, Any]) -> Optional[List[tuple]]:
        """Extract SQL data from agent result intermediate steps."""
        try:
            intermediate_steps = result.get('intermediate_steps', [])
            
            # Look for SQL query results in intermediate steps
            for step in intermediate_steps:
                if isinstance(step, (list, tuple)) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # Check if this is a SQL query tool result
                    if hasattr(action, 'tool') and 'sql' in str(action.tool).lower():
                        # Try to parse the observation as SQL results
                        if isinstance(observation, str):
                            # Look for list/tuple patterns in the observation
                            import ast
                            try:
                                # Try to extract data that looks like SQL results
                                if '[(' in observation and ')]' in observation:
                                    # Extract the list of tuples
                                    start = observation.find('[(')
                                    end = observation.find(')]') + 2
                                    data_str = observation[start:end]
                                    data = ast.literal_eval(data_str)
                                    return data
                            except:
                                continue
            
            return None
        except Exception as e:
            logger.warning(f"Failed to extract SQL data: {e}")
            return None
    
    def _generate_chart_from_data(self, data: List[tuple], query: str) -> Optional[Dict[str, str]]:
        """Generate a chart from SQL data using pandas and plotly."""
        try:
            if not data or len(data) == 0:
                return None
            
            # Convert to pandas DataFrame
            # Assume first row represents the structure
            if len(data[0]) == 2:
                # Two columns - good for bar charts, pie charts
                df = pd.DataFrame(data, columns=['category', 'value'])
                
                # Determine chart type from query
                query_lower = query.lower()
                if 'pie' in query_lower:
                    chart_type = 'pie'
                elif 'line' in query_lower:
                    chart_type = 'line'
                else:
                    chart_type = 'bar'  # Default
                
                # Generate appropriate chart
                if chart_type == 'pie':
                    fig = px.pie(df, names='category', values='value', 
                               title=self._generate_chart_title(query))
                elif chart_type == 'line':
                    fig = px.line(df, x='category', y='value', 
                                title=self._generate_chart_title(query))
                else:  # bar chart
                    fig = px.bar(df, x='category', y='value', 
                               title=self._generate_chart_title(query))
                
            else:
                # Multiple columns - use first column as x, second as y
                columns = [f'col_{i}' for i in range(len(data[0]))]
                df = pd.DataFrame(data, columns=columns)
                fig = px.bar(df, x=columns[0], y=columns[1], 
                           title=self._generate_chart_title(query))
                chart_type = 'bar'
            
            # Save chart as HTML file optimized for iframe embedding
            chart_id = str(uuid.uuid4())
            chart_filename = f"chart_{chart_id}.html"
            charts_dir = "static/charts"
            os.makedirs(charts_dir, exist_ok=True)
            
            chart_path = os.path.join(charts_dir, chart_filename)
            
            # Generate iframe-friendly HTML
            fig.write_html(
                chart_path,
                config={
                    'displayModeBar': False,  # Hide plotly toolbar for cleaner embed
                    'responsive': True        # Make chart responsive
                },
                div_id=f"chart-{chart_id}",
                include_plotlyjs='cdn'    # Use CDN for smaller file size
            )
            
            logger.info(f"📊 Chart generated: {chart_filename}")
            
            return {
                'chart_file': chart_filename,
                'chart_type': chart_type,
                'chart_path': chart_path
            }
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return None
    
    def _generate_chart_title(self, query: str) -> str:
        """Generate a meaningful chart title from the user query."""
        # Simple title generation based on query content
        if 'mutual fund' in query.lower():
            return "Mutual Fund Portfolio Analysis"
        elif 'portfolio' in query.lower():
            return "Portfolio Analysis"
        elif 'weight' in query.lower():
            return "Weight Distribution"
        else:
            return "Data Visualization"
    
    def _detect_calculation_type(self, query: str) -> Optional[str]:
        """Detect what type of calculation is being requested."""
        query_lower = query.lower()
        
        # Financial risk calculations
        risk_keywords = ['risk', 'volatility', 'sharpe', 'beta', 'var', 'standard deviation', 'drawdown']
        if any(keyword in query_lower for keyword in risk_keywords):
            return 'risk_analysis'
        
        # Performance calculations
        performance_keywords = ['return', 'performance', 'growth', 'roi', 'gains', 'profit']
        if any(keyword in query_lower for keyword in performance_keywords):
            return 'performance_analysis'
        
        # Correlation analysis
        correlation_keywords = ['correlation', 'relationship', 'connected', 'correlated']
        if any(keyword in query_lower for keyword in correlation_keywords):
            return 'correlation_analysis'
        
        # Statistical analysis
        stats_keywords = ['average', 'mean', 'median', 'summary', 'statistics', 'stats']
        if any(keyword in query_lower for keyword in stats_keywords):
            return 'statistical_analysis'
        
        # Comparison analysis
        comparison_keywords = ['compare', 'vs', 'versus', 'against', 'difference', 'better', 'worse']
        if any(keyword in query_lower for keyword in comparison_keywords):
            return 'comparison_analysis'
        
        return None
    
    def _perform_calculations(self, df: pd.DataFrame, calc_type: str, query: str) -> Dict[str, Any]:
        """Perform calculations on the DataFrame based on the calculation type."""
        try:
            results = {}
            
            if calc_type == 'risk_analysis':
                results = self._calculate_risk_metrics(df)
            elif calc_type == 'performance_analysis':
                results = self._calculate_performance_metrics(df)
            elif calc_type == 'correlation_analysis':
                results = self._calculate_correlation_metrics(df)
            elif calc_type == 'statistical_analysis':
                results = self._calculate_statistical_metrics(df)
            elif calc_type == 'comparison_analysis':
                results = self._calculate_comparison_metrics(df)
            
            return results
            
        except Exception as e:
            logger.error(f"Calculation failed for {calc_type}: {e}")
            return {}
    
    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate financial risk metrics."""
        results = {}
        
        # Look for numeric columns that could represent returns or values
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                if 'return' in col.lower() or 'price' in col.lower() or 'value' in col.lower():
                    data = df[col].dropna()
                    
                    if len(data) > 1:
                        results[f'{col}_volatility'] = data.std()
                        results[f'{col}_mean_return'] = data.mean()
                        
                        # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
                        if data.std() != 0:
                            results[f'{col}_sharpe_ratio'] = data.mean() / data.std()
                        
                        # Max drawdown
                        if 'price' in col.lower() or 'value' in col.lower():
                            running_max = data.expanding().max()
                            drawdown = (data - running_max) / running_max
                            results[f'{col}_max_drawdown'] = drawdown.min()
        
        return results
    
    def _calculate_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics."""
        results = {}
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            
            if len(data) > 0:
                results[f'{col}_total'] = data.sum()
                results[f'{col}_average'] = data.mean()
                results[f'{col}_max'] = data.max()
                results[f'{col}_min'] = data.min()
                
                # Growth rate (if we have time series data)
                if len(data) > 1:
                    first_value = data.iloc[0]
                    last_value = data.iloc[-1]
                    if first_value != 0:
                        results[f'{col}_total_growth'] = ((last_value - first_value) / first_value) * 100
        
        return results
    
    def _calculate_correlation_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation metrics between numeric columns."""
        results = {}
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) >= 2:
            correlation_matrix = df[numeric_cols].corr()
            
            # Find strongest correlations
            correlations = []
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    corr_value = correlation_matrix.loc[col1, col2]
                    if not pd.isna(corr_value):
                        correlations.append({
                            'pair': f'{col1} vs {col2}',
                            'correlation': corr_value
                        })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            results['top_correlations'] = correlations[:5]  # Top 5
        
        return results
    
    def _calculate_statistical_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistical metrics."""
        results = {}
        
        # Overall data summary
        results['total_records'] = len(df)
        results['total_columns'] = len(df.columns)
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 0:
                results[f'{col}_count'] = len(data)
                results[f'{col}_mean'] = data.mean()
                results[f'{col}_median'] = data.median()
                results[f'{col}_std'] = data.std()
        
        return results
    
    def _calculate_comparison_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comparison metrics between different categories."""
        results = {}
        
        # Look for categorical columns to group by
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat_col = categorical_cols[0]  # Use first categorical column
            num_col = numeric_cols[0]     # Use first numeric column
            
            # Group by categorical column and calculate statistics
            grouped = df.groupby(cat_col)[num_col].agg(['mean', 'sum', 'count'])
            
            # Convert to dictionary format
            for category in grouped.index:
                results[f'{category}_average'] = grouped.loc[category, 'mean']
                results[f'{category}_total'] = grouped.loc[category, 'sum']
                results[f'{category}_count'] = grouped.loc[category, 'count']
            
            # Find best and worst performers
            best_performer = grouped['mean'].idxmax()
            worst_performer = grouped['mean'].idxmin()
            
            results['best_performer'] = best_performer
            results['worst_performer'] = worst_performer
            results['best_performer_value'] = grouped.loc[best_performer, 'mean']
            results['worst_performer_value'] = grouped.loc[worst_performer, 'mean']
        
        return results
    
    def _format_calculation_insights(self, calculations: Dict[str, Any], calc_type: str) -> str:
        """Format calculation results into human-readable insights."""
        if not calculations:
            return ""
        
        insights = []
        
        if calc_type == 'risk_analysis':
            for key, value in calculations.items():
                if 'sharpe_ratio' in key:
                    if value > 1.0:
                        insights.append(f"📈 Excellent risk-adjusted returns (Sharpe ratio: {value:.2f})")
                    elif value > 0.5:
                        insights.append(f"📊 Good risk-adjusted returns (Sharpe ratio: {value:.2f})")
                    else:
                        insights.append(f"⚠️ Low risk-adjusted returns (Sharpe ratio: {value:.2f})")
                elif 'volatility' in key:
                    col_name = key.replace('_volatility', '')
                    insights.append(f"📊 {col_name} volatility: {value:.2f}")
                elif 'max_drawdown' in key:
                    insights.append(f"📉 Maximum drawdown: {value:.2%}")
        
        elif calc_type == 'performance_analysis':
            for key, value in calculations.items():
                if 'total_growth' in key:
                    col_name = key.replace('_total_growth', '')
                    if value > 0:
                        insights.append(f"📈 {col_name} gained {value:.1f}% over the period")
                    else:
                        insights.append(f"📉 {col_name} declined {abs(value):.1f}% over the period")
                elif 'average' in key:
                    col_name = key.replace('_average', '')
                    insights.append(f"📊 Average {col_name}: {value:.2f}")
        
        elif calc_type == 'comparison_analysis':
            if 'best_performer' in calculations:
                best = calculations['best_performer']
                best_value = calculations.get('best_performer_value', 0)
                worst = calculations.get('worst_performer', '')
                worst_value = calculations.get('worst_performer_value', 0)
                
                insights.append(f"🏆 Best performer: {best} ({best_value:.2f})")
                if worst:
                    insights.append(f"📉 Worst performer: {worst} ({worst_value:.2f})")
        
        elif calc_type == 'statistical_analysis':
            if 'total_records' in calculations:
                insights.append(f"📊 Dataset contains {calculations['total_records']} records")
            
            for key, value in calculations.items():
                if 'mean' in key and not key.startswith('total'):
                    col_name = key.replace('_mean', '')
                    insights.append(f"📈 Average {col_name}: {value:.2f}")
        
        elif calc_type == 'correlation_analysis':
            if 'top_correlations' in calculations:
                correlations = calculations['top_correlations']
                if correlations:
                    insights.append("🔗 Strongest correlations:")
                    for corr in correlations[:3]:  # Top 3
                        strength = "Strong" if abs(corr['correlation']) > 0.7 else "Moderate" if abs(corr['correlation']) > 0.3 else "Weak"
                        insights.append(f"   • {corr['pair']}: {strength} ({corr['correlation']:.2f})")
        
        return "\n".join(insights)
    
    def _should_include_chart(self, query: str, df: pd.DataFrame) -> bool:
        """Determine if a chart should be included in the response."""
        # Always include chart if explicitly requested
        if self._is_chart_request(query):
            return True
        
        # Include chart for comparison queries with reasonable data size
        if self._detect_calculation_type(query) == 'comparison_analysis' and len(df) <= 50:
            return True
        
        # Include chart for performance analysis with time series data
        if self._detect_calculation_type(query) == 'performance_analysis' and len(df) > 2:
            return True
        
        return False
    
    def _should_include_table(self, query: str, df: pd.DataFrame) -> bool:
        """Determine if a data table should be included in the response."""
        # Include table for small datasets or when explicitly requested
        table_keywords = ['table', 'data', 'records', 'list', 'show all']
        if any(keyword in query.lower() for keyword in table_keywords):
            return True
        
        # Include table for small datasets (< 10 rows)
        if len(df) <= 10:
            return True
        
        return False
    
    def _generate_mixed_response(self, original_response: str, df: pd.DataFrame, 
                                calculations: Dict[str, Any], calc_type: str, 
                                query: str) -> Dict[str, Any]:
        """Generate a mixed response with text, calculations, and potentially charts."""
        response_parts = []
        
        # Start with original agent response
        if original_response:
            response_parts.append(original_response)
        
        # Add calculation insights
        if calculations:
            insights = self._format_calculation_insights(calculations, calc_type)
            if insights:
                response_parts.append(f"\n🔍 **Analysis Results:**\n{insights}")
        
        # Generate chart if appropriate
        chart_info = None
        if self._should_include_chart(query, df):
            chart_info = self._generate_chart_from_data(
                df.values.tolist() if len(df) > 0 else [], 
                query
            )
        
        # Generate data table if appropriate
        table_html = None
        if self._should_include_table(query, df):
            # Create a clean HTML table
            table_html = df.head(10).to_html(classes='data-table', table_id='analysis-table')
        
        # Combine all response parts
        combined_response = "\n\n".join(response_parts)
        
        result = {
            'response': combined_response,
            'has_calculations': bool(calculations),
            'calculation_type': calc_type if calculations else None
        }
        
        # Add chart info if generated
        if chart_info:
            result['chart_file'] = chart_info['chart_file']
            result['chart_type'] = chart_info['chart_type']
        
        # Add table if generated
        if table_html:
            result['data_table'] = table_html
        
        return result
    
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
            
            # Enhanced processing: Extract SQL data and perform calculations
            sql_data = self._extract_sql_data_from_result(result)
            df = None
            calculations = {}
            calc_type = None
            
            if sql_data:
                logger.info(f"📊 SQL data extracted: {len(sql_data)} rows")
                
                # Convert to pandas DataFrame for analysis
                try:
                    # Smart column detection for DataFrame creation
                    if len(sql_data) > 0 and len(sql_data[0]) == 2:
                        df = pd.DataFrame(sql_data, columns=['category', 'value'])
                    else:
                        # Generate generic column names
                        num_cols = len(sql_data[0]) if sql_data else 0
                        columns = [f'col_{i}' for i in range(num_cols)]
                        df = pd.DataFrame(sql_data, columns=columns)
                    
                    logger.info(f"🐼 DataFrame created: {df.shape}")
                    
                    # Detect and perform calculations if requested
                    calc_type = self._detect_calculation_type(query)
                    if calc_type:
                        logger.info(f"🔍 Calculation type detected: {calc_type}")
                        calculations = self._perform_calculations(df, calc_type, query)
                        logger.info(f"📊 Calculations completed: {len(calculations)} metrics")
                    
                except Exception as e:
                    logger.error(f"DataFrame processing failed: {e}")
                    df = None
            
            # Generate mixed response (text + calculations + charts)
            original_response = result.get("output", "")
            
            if df is not None and (calculations or self._is_chart_request(query)):
                # Generate enhanced mixed response
                mixed_response = self._generate_mixed_response(
                    original_response, df, calculations, calc_type, query
                )
                
                response_dict = {
                    'success': True,
                    'response': mixed_response['response'],
                    'database': database_name,
                    'schema': schema_name or user_schema,
                    'session_id': session_id,
                    'intermediate_steps': result.get("intermediate_steps", []),
                    'has_calculations': mixed_response.get('has_calculations', False),
                    'calculation_type': mixed_response.get('calculation_type')
                }
                
                # Add chart info if generated
                if 'chart_file' in mixed_response:
                    response_dict['chart_file'] = mixed_response['chart_file']
                    response_dict['chart_type'] = mixed_response['chart_type']
                    logger.info(f"📊 Chart added to response: {mixed_response['chart_file']}")
                
                # Add data table if generated
                if 'data_table' in mixed_response:
                    response_dict['data_table'] = mixed_response['data_table']
                    logger.info("📋 Data table added to response")
                
            else:
                # Fallback to simple chart generation for chart requests
                chart_info = None
                if self._is_chart_request(query) and sql_data:
                    chart_info = self._generate_chart_from_data(sql_data, query)
                
                response_dict = {
                    'success': True,
                    'response': original_response,
                    'database': database_name,
                    'schema': schema_name or user_schema,
                    'session_id': session_id,
                    'intermediate_steps': result.get("intermediate_steps", [])
                }
                
                # Add chart info if chart was generated
                if chart_info:
                    response_dict['chart_file'] = chart_info['chart_file']
                    response_dict['chart_type'] = chart_info['chart_type']
                    logger.info(f"📊 Chart added to response: {chart_info['chart_file']}")
            
            return response_dict
            
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
