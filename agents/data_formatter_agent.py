#!/usr/bin/env python3
"""
Data Formatter Agent - Visualization and output formatting

This agent handles:
- Plotly chart generation and visualization
- Data formatting and presentation
- Mixed response generation (text + charts + tables)
- HTML chart creation and file management
"""

import logging
from typing import Dict, List, Optional, Any, Union
import uuid
import os
import re
from datetime import datetime

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.io import to_html
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None
    go = None

logger = logging.getLogger(__name__)


class DataFormatterAgent:
    """
    Data Formatter Agent focused on visualization and output formatting.
    
    Responsibilities:
    - Creating Plotly charts and visualizations
    - Formatting data into tables and presentations
    - Generating mixed responses with text, charts, and data
    - Managing chart files and serving
    """
    
    def __init__(self, static_dir: str = "static/charts"):
        """
        Initialize the Data Formatter Agent.
        
        Args:
            static_dir: Directory to save chart files
        """
        self.static_dir = static_dir
        self.chart_cache = {}
        
        # Ensure static directory exists
        os.makedirs(static_dir, exist_ok=True)
        
        logger.info(f"📊 Data Formatter Agent initialized with static dir: {static_dir}")
    
    def process_data(self, quant_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Process quantitative analysis data and create formatted output.
        
        Args:
            quant_data: Data from Mutual Fund Quant Agent
            query: Original user query for context
            
        Returns:
            Dictionary containing formatted response with optional charts
        """
        try:
            logger.info("📊 Starting data formatting and visualization")
            
            if not quant_data.get('success', False):
                logger.warning("Received unsuccessful data from Quant Agent")
                return {
                    'success': False,
                    'error': quant_data.get('error', 'Unknown error from quantitative analysis'),
                    'response': "I encountered an error during the quantitative analysis phase.",
                    'query': query
                }
            
            # Extract data components
            dataframe_data = quant_data.get('dataframe', [])
            calculations = quant_data.get('calculations', {})
            insights = quant_data.get('insights', [])
            calc_type = quant_data.get('calculation_type')
            dataframe_info = quant_data.get('dataframe_info', {})
            original_sql_data = quant_data.get('original_sql_data', {})
            
            # Convert back to DataFrame for visualization
            df = pd.DataFrame(dataframe_data) if dataframe_data else None
            
            # Determine if charts should be included
            include_chart = self._should_include_chart(query, df)
            include_table = self._should_include_table(query, df)
            
            # Generate mixed response
            response_data = self._generate_mixed_response(
                original_sql_data.get('sql_response', ''),
                df,
                calculations,
                calc_type,
                query,
                insights,
                include_chart,
                include_table
            )
            
            logger.info("✅ Data formatting completed successfully")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Data formatting failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"I encountered an error while formatting the data: {str(e)}",
                'query': query
            }
    
    def _should_include_chart(self, query: str, df: Optional[pd.DataFrame]) -> bool:
        """Determine if a chart should be included in the response."""
        if not PLOTLY_AVAILABLE or df is None or df.empty:
            return False
        
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
    
    def _should_include_table(self, query: str, df: Optional[pd.DataFrame]) -> bool:
        """Determine if a data table should be included in the response."""
        if df is None or df.empty:
            return False
        
        # Include table for small datasets or when explicitly requested
        table_keywords = ['table', 'data', 'records', 'list', 'show all']
        if any(keyword in query.lower() for keyword in table_keywords):
            return True
        
        # Include table for small datasets (< 10 rows)
        if len(df) <= 10:
            return True
        
        return False
    
    def _is_chart_request(self, query: str) -> bool:
        """Check if the query explicitly requests a chart or visualization."""
        chart_keywords = [
            'chart', 'graph', 'plot', 'visualize', 'visualization', 'bar chart', 'line chart',
            'pie chart', 'scatter plot', 'histogram', 'show me', 'display', 'draw'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in chart_keywords)
    
    def _detect_calculation_type(self, query: str) -> Optional[str]:
        """Detect the type of calculation based on query keywords."""
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
    
    def _generate_mixed_response(self, original_response: str, df: Optional[pd.DataFrame], 
                                calculations: Dict[str, Any], calc_type: Optional[str], 
                                query: str, insights: List[str], include_chart: bool = False,
                                include_table: bool = False) -> Dict[str, Any]:
        """Generate a clean, formatted response without duplication."""
        try:
            response_parts = []
            
            # Extract clean data from original SQL response (remove SQL agent's formatting)
            clean_data = self._extract_clean_data_from_sql_response(original_response, df)
            
            # Add the clean data presentation
            if clean_data:
                response_parts.append(clean_data)
            
            # Add chart confirmation if chart is being generated
            chart_info = None
            if include_chart and df is not None and not df.empty:
                chart_info = self._create_chart_with_formatter(df, calc_type, query)
                if chart_info:
                    # Simple chart confirmation without duplicating data
                    chart_confirmation = self._get_chart_confirmation_text(query, chart_info['chart_type'])
                    if chart_confirmation:
                        response_parts.append(f"\n{chart_confirmation}")
                    
                    # Add chart success notification
                    response_parts.append(f"\n📊 **Interactive Chart Generated**: {chart_info['chart_type'].title()} chart created successfully.")
            
            # Add insights from quantitative analysis (if any)
            if insights:
                response_parts.append("\n\n**Key Insights:**")
                for insight in insights:
                    response_parts.append(f"• {insight}")
            
            # Add data table if requested
            data_table = None
            if include_table and df is not None and not df.empty:
                data_table = self._format_data_table(df)
                if data_table:
                    response_parts.append(f"\n\n**Data Table:**\n{data_table}")
            
            # Combine all parts
            final_response = "\n".join(response_parts)
            
            # Prepare response dictionary
            response_dict = {
                'success': True,
                'response': final_response,
                'has_calculations': bool(calculations),
                'calculation_type': calc_type,
                'query': query
            }
            
            # Add chart info if generated
            if chart_info:
                response_dict['chart_files'] = [chart_info['chart_file']]
                response_dict['chart_file'] = chart_info['chart_file']
                response_dict['chart_type'] = chart_info['chart_type']
                logger.info(f"📊 Chart included in response: {chart_info['chart_file']}")
            
            # Add data table if generated
            if data_table:
                response_dict['data_table'] = data_table
                logger.info("📋 Data table included in response")
            
            return response_dict
            
        except Exception as e:
            logger.error(f"Error generating mixed response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': original_response or "An error occurred while formatting the response.",
                'query': query
            }
    
    def _format_data_summary(self, df: pd.DataFrame) -> str:
        """Create a formatted summary of the DataFrame."""
        try:
            summary_parts = []
            
            # Basic info
            summary_parts.append(f"• **Dataset size**: {len(df):,} rows × {len(df.columns)} columns")
            
            # Column info
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                summary_parts.append(f"• **Numeric columns**: {', '.join(numeric_cols)}")
            
            # Quick stats for numeric columns (first few)
            for col in numeric_cols[:3]:  # Only first 3 to avoid overwhelming
                data = df[col].dropna()
                if len(data) > 0:
                    summary_parts.append(f"• **{col}**: Min={data.min():.2f}, Max={data.max():.2f}, Avg={data.mean():.2f}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error formatting data summary: {e}")
            return ""
    
    def _extract_clean_data_from_sql_response(self, original_response: str, df: Optional[pd.DataFrame]) -> str:
        """Extract and clean the data presentation from SQL agent response."""
        try:
            if not original_response:
                return ""
            
            # Split response into lines
            lines = original_response.split('\n')
            clean_lines = []
            
            # Find the main data section (usually starts with "Here are the...")
            in_data_section = False
            for line in lines:
                line = line.strip()
                
                # Start of data section
                if line.startswith("Here are the") or line.startswith("Here is the"):
                    clean_lines.append(line)
                    in_data_section = True
                    continue
                
                # Stop at chart-related text or duplicate sections
                if any(phrase in line.lower() for phrase in [
                    "i will now plot", "here is the bar graph", "here is the chart",
                    "the graph visually", "chart generated"
                ]):
                    break
                
                # Include numbered/bulleted data items
                if in_data_section and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')) or line == ''):
                    clean_lines.append(line)
                elif not in_data_section and line:
                    # Include initial context before data section
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines).strip()
            
        except Exception as e:
            logger.error(f"Error extracting clean data: {e}")
            return original_response
    
    def _get_chart_confirmation_text(self, query: str, chart_type: str) -> str:
        """Generate appropriate chart confirmation text based on query."""
        try:
            query_lower = query.lower()
            
            if 'plot' in query_lower or 'graph' in query_lower or 'chart' in query_lower:
                if 'bar' in query_lower:
                    return "I will now create a bar chart for you."
                elif 'line' in query_lower:
                    return "I will now create a line chart for you."
                elif 'pie' in query_lower:
                    return "I will now create a pie chart for you."
                else:
                    return f"I will now create a {chart_type} chart for you."
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating chart confirmation: {e}")
            return ""
    
    def _format_data_table(self, df: pd.DataFrame) -> str:
        """Format DataFrame as an HTML table for proper frontend rendering."""
        try:
            # Remove duplicates and limit rows for display
            clean_df = df.drop_duplicates().head(10)
            
            # Format numeric columns to avoid scientific notation
            for col in clean_df.columns:
                if clean_df[col].dtype in ['float64', 'int64']:
                    # Format large numbers with commas and 2 decimal places
                    clean_df[col] = clean_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
            
            # Convert to HTML table with styling
            html_table = clean_df.to_html(
                index=False, 
                classes='table table-striped table-bordered',
                table_id='data-table',
                escape=False
            )
            
            # Add note if data was truncated
            if len(df) > 10:
                html_table += f"<p><em>Note: Showing first 10 rows of {len(df)} total rows</em></p>"
            
            return html_table
            
        except Exception as e:
            logger.error(f"Error formatting data table: {e}")
            return ""
    
    def _create_chart_with_formatter(self, df: pd.DataFrame, calc_type: Optional[str], query: str) -> Optional[Dict[str, Any]]:
        """Create a Plotly chart from the DataFrame."""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for chart generation")
            return None
        
        try:
            chart_data = self._create_plotly_chart(df, calc_type, query)
            if chart_data:
                return chart_data
            
            logger.warning("No suitable chart could be generated from the data")
            return None
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return None
    
    def _create_plotly_chart(self, df: pd.DataFrame, calc_type: Optional[str], query: str) -> Optional[Dict[str, Any]]:
        """Create appropriate Plotly chart based on data and query."""
        try:
            # Determine chart type based on data structure and query
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            
            chart_type = self._determine_chart_type(df, calc_type, query, numeric_cols, categorical_cols)
            
            if chart_type == 'bar':
                return self._create_bar_chart(df, numeric_cols, categorical_cols)
            elif chart_type == 'line':
                return self._create_line_chart(df, numeric_cols, categorical_cols)
            elif chart_type == 'pie':
                return self._create_pie_chart(df, numeric_cols, categorical_cols)
            elif chart_type == 'table':
                return self._create_table_chart(df)
            
            # Default to bar chart if no specific type determined
            return self._create_bar_chart(df, numeric_cols, categorical_cols)
            
        except Exception as e:
            logger.error(f"Error creating Plotly chart: {e}")
            return None
    
    def _determine_chart_type(self, df: pd.DataFrame, calc_type: Optional[str], query: str,
                            numeric_cols, categorical_cols) -> str:
        """Determine the most appropriate chart type."""
        query_lower = query.lower()
        
        # Explicit chart type requests
        if 'pie' in query_lower or 'pie chart' in query_lower:
            return 'pie'
        elif 'line' in query_lower or 'line chart' in query_lower or 'trend' in query_lower:
            return 'line'
        elif 'table' in query_lower:
            return 'table'
        
        # Based on data structure
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            if len(df) <= 10 and 'comparison' in query_lower:
                return 'pie'
            else:
                return 'bar'
        elif len(numeric_cols) >= 2:
            return 'line'
        elif len(df) <= 20:
            return 'table'
        
        return 'bar'
    
    def _create_bar_chart(self, df: pd.DataFrame, numeric_cols, categorical_cols) -> Dict[str, Any]:
        """Create a bar chart."""
        try:
            # Use first categorical column for x-axis and first numeric for y-axis
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
                
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            elif len(numeric_cols) >= 2:
                # Use first two numeric columns
                fig = px.bar(df, x=df.index, y=numeric_cols[0], title=f"{numeric_cols[0]} Distribution")
            else:
                # Fallback: use index
                fig = px.bar(df, x=df.index, y=df.columns[0], title="Data Distribution")
            
            # Customize layout
            fig.update_layout(
                template="plotly_white",
                showlegend=False,
                height=400,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            return self._save_chart(fig, 'bar')
            
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            return None
    
    def _create_line_chart(self, df: pd.DataFrame, numeric_cols, categorical_cols) -> Dict[str, Any]:
        """Create a line chart."""
        try:
            if len(numeric_cols) >= 2:
                # Use first two numeric columns
                fig = px.line(df, x=df.index, y=numeric_cols[0], title=f"{numeric_cols[0]} Trend")
            elif len(categorical_cols) > 0 and len(numeric_cols) > 0:
                # Use categorical for x and numeric for y
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
            else:
                # Fallback: use index
                fig = px.line(df, x=df.index, y=df.columns[0], title="Data Trend")
            
            # Customize layout
            fig.update_layout(
                template="plotly_white",
                showlegend=False,
                height=400,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            return self._save_chart(fig, 'line')
            
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            return None
    
    def _create_pie_chart(self, df: pd.DataFrame, numeric_cols, categorical_cols) -> Dict[str, Any]:
        """Create a pie chart."""
        try:
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                # Use categorical for labels and numeric for values
                labels_col = categorical_cols[0]
                values_col = numeric_cols[0]
                
                fig = px.pie(df, names=labels_col, values=values_col, 
                           title=f"{values_col} Distribution by {labels_col}")
            else:
                # Fallback: create pie from first few rows
                limited_df = df.head(5)
                if len(numeric_cols) > 0:
                    fig = px.pie(values=limited_df[numeric_cols[0]], 
                               names=limited_df.index,
                               title=f"{numeric_cols[0]} Distribution")
                else:
                    return None
            
            # Customize layout
            fig.update_layout(
                template="plotly_white",
                height=400,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            return self._save_chart(fig, 'pie')
            
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            return None
    
    def _create_table_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a table visualization."""
        try:
            # Limit to first 20 rows for display
            display_df = df.head(20)
            
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(display_df.columns),
                          fill_color='paleturquoise',
                          align='left'),
                cells=dict(values=[display_df[col] for col in display_df.columns],
                         fill_color='lavender',
                         align='left')
            )])
            
            fig.update_layout(
                title="Data Table",
                height=400,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            return self._save_chart(fig, 'table')
            
        except Exception as e:
            logger.error(f"Error creating table chart: {e}")
            return None
    
    def _save_chart(self, fig, chart_type: str) -> Dict[str, Any]:
        """Save Plotly figure as HTML file."""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{chart_type}_{timestamp}_{str(uuid.uuid4())[:8]}.html"
            filepath = os.path.join(self.static_dir, filename)
            
            # Convert to HTML
            html_content = to_html(fig, config={'displayModeBar': False})
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"📊 Chart saved: {filename}")
            
            return {
                'chart_file': filename,
                'chart_type': chart_type,
                'chart_path': filepath
            }
            
        except Exception as e:
            logger.error(f"Error saving chart: {e}")
            return None
