"""
Data Formatter Agent - Creates beautiful, formatted presentations of financial data
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from agents.base_agent import BaseAgent, AgentState
from agents.agent_configs import DATA_FORMATTER_CONFIG

class DataFormatterAgent(BaseAgent):
    """Agent responsible for formatting and visualizing data for user presentation"""
    
    def __init__(self, openai_client):
        super().__init__(DATA_FORMATTER_CONFIG, openai_client)
        
    async def process(self, state: AgentState) -> AgentState:
        """Format data into beautiful, user-friendly presentations"""
        try:
            self.log_step(state, "formatting_response", "Creating formatted output")
            
            # Collect all data from previous agents
            data_collection = self._collect_all_data(state)
            
            # Determine the best presentation format
            format_strategy = await self._determine_format_strategy(
                state.user_query, 
                data_collection
            )
            
            # Create formatted response
            formatted_response = await self._create_formatted_response(
                data_collection, 
                format_strategy,
                state.user_query
            )
            
            # Create final message for orchestrator
            final_message = self.create_message(
                recipient="orchestrator",
                content=formatted_response,
                message_type="formatted_output",
                metadata={
                    "format_type": format_strategy.get("format_type"),
                    "includes_charts": format_strategy.get("includes_charts", False),
                    "response_length": len(str(formatted_response))
                }
            )
            
            state = self.add_message_to_state(state, final_message)
            state.current_step = "orchestrator"
            state.data["formatted_response"] = formatted_response
            
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "data_formatting")
    
    def _collect_all_data(self, state: AgentState) -> Dict[str, Any]:
        """Collect data from all previous agents"""
        
        data_collection = {
            "user_query": state.user_query,
            "sql_data": None,
            "expert_analysis": None,
            "web_research": None,
            "errors": state.errors
        }
        
        # Collect data from messages
        for message in state.messages:
            if message.sender == "sql_agent" and message.message_type == "data":
                data_collection["sql_data"] = message.content.get("sql_data")
            elif message.sender == "mutual_fund_expert" and message.message_type == "analysis":
                data_collection["expert_analysis"] = message.content.get("expert_analysis")
            elif message.sender == "web_agent" and message.message_type == "data":
                data_collection["web_research"] = message.content.get("web_research")
        
        return data_collection
    
    async def _determine_format_strategy(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best formatting strategy based on query and available data"""
        
        strategy_prompt = f"""
        Determine the best presentation format for this financial query and data:
        
        Query: "{query}"
        Available data types:
        - SQL data: {'Yes' if data.get('sql_data') else 'No'}
        - Expert analysis: {'Yes' if data.get('expert_analysis') else 'No'}
        - Web research: {'Yes' if data.get('web_research') else 'No'}
        
        Consider the query type and recommend presentation format:
        1. What visual elements would be most helpful?
        2. Should this include charts, tables, or lists?
        3. What's the appropriate level of detail?
        4. How should information be structured for clarity?
        
        Respond in JSON format:
        {{
            "format_type": "comprehensive_report|simple_answer|comparison_table|performance_chart|portfolio_summary",
            "includes_charts": true/false,
            "visual_elements": ["tables", "charts", "bullet_points", "summaries"],
            "detail_level": "high|medium|low",
            "structure": "executive_summary_first|data_first|analysis_first"
        }}
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": strategy_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.1)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback strategy
            return {
                "format_type": "comprehensive_report",
                "includes_charts": False,
                "visual_elements": ["summaries", "bullet_points"],
                "detail_level": "medium",
                "structure": "executive_summary_first"
            }
    
    async def _create_formatted_response(
        self, 
        data: Dict[str, Any], 
        strategy: Dict[str, Any], 
        query: str
    ) -> Dict[str, Any]:
        """Create the final formatted response"""
        
        # Extract data components
        sql_data = data.get("sql_data", {})
        expert_analysis = data.get("expert_analysis", {})
        web_research = data.get("web_research", {})
        
        # Create comprehensive formatting prompt
        formatting_prompt = f"""
        Create a beautiful, professional response for the financial query: "{query}"
        
        Available information:
        
        SQL Data: {json.dumps(sql_data, indent=2) if sql_data else "No database data available"}
        
        Expert Analysis: {expert_analysis.get('content', 'No expert analysis available')}
        
        Web Research: {json.dumps(web_research, indent=2) if web_research else "No web research data available"}
        
        Format Strategy: {strategy}
        
        Create a response that includes:
        1. **Executive Summary** (2-3 sentences highlighting key findings)
        2. **Detailed Analysis** (comprehensive insights from expert analysis)
        3. **Data Insights** (key findings from database queries, if available)
        4. **Current Market Context** (insights from web research, if available)
        5. **Recommendations** (actionable advice for the user)
        6. **Important Notes** (disclaimers, limitations, or caveats)
        
        Formatting requirements:
        - Use clear headings and subheadings
        - Include bullet points for easy scanning
        - Use Indian financial terminology appropriately
        - Format numbers with proper currency symbols (₹) and percentages
        - Make it visually appealing with emojis where appropriate
        - Include data tables in markdown format if relevant
        - Ensure professional tone while being accessible
        
        Structure the response to be comprehensive yet easy to understand for mutual fund investors.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": formatting_prompt}
        ]
        
        formatted_content = await self.llm_call(messages, temperature=0.2, max_tokens=3000)
        
        # Create final response structure
        formatted_response = {
            "content": formatted_content,
            "format_type": strategy.get("format_type"),
            "timestamp": datetime.now().isoformat(),
            "data_sources": self._identify_data_sources(data),
            "charts": self._create_chart_data(sql_data) if strategy.get("includes_charts") else None,
            "metadata": {
                "query": query,
                "response_length": len(formatted_content),
                "sources_used": len([d for d in [sql_data, expert_analysis, web_research] if d])
            }
        }
        
        return formatted_response
    
    def _identify_data_sources(self, data: Dict[str, Any]) -> List[str]:
        """Identify which data sources were used in the response"""
        sources = []
        
        if data.get("sql_data"):
            sources.append("Database Analysis")
        if data.get("expert_analysis"):
            sources.append("Mutual Fund Expert Analysis")
        if data.get("web_research"):
            sources.append("Current Market Research")
            
        return sources
    
    def _create_chart_data(self, sql_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create chart data structure for visualization"""
        
        if not sql_data or not sql_data.get("data"):
            return None
        
        data_rows = sql_data.get("data", [])
        columns = sql_data.get("columns", [])
        
        if not data_rows or not columns:
            return None
        
        # Determine chart type based on data structure
        chart_config = {
            "type": "table",  # Default to table
            "data": data_rows[:10],  # Limit to first 10 rows
            "columns": columns,
            "title": "Query Results",
            "description": f"Showing {min(len(data_rows), 10)} of {len(data_rows)} results"
        }
        
        # Try to create more specific chart types based on column names
        if self._has_numeric_columns(data_rows, columns):
            if self._has_time_series_data(columns):
                chart_config["type"] = "line_chart"
                chart_config["description"] = "Performance over time"
            elif len(data_rows) <= 20:
                chart_config["type"] = "bar_chart"
                chart_config["description"] = "Comparative analysis"
        
        return chart_config
    
    def _has_numeric_columns(self, data: List[Dict], columns: List[str]) -> bool:
        """Check if data has numeric columns suitable for charting"""
        if not data:
            return False
        
        first_row = data[0]
        numeric_count = 0
        
        for col in columns:
            if col in first_row:
                try:
                    float(str(first_row[col]).replace('%', '').replace(',', ''))
                    numeric_count += 1
                except (ValueError, TypeError):
                    continue
        
        return numeric_count >= 1
    
    def _has_time_series_data(self, columns: List[str]) -> bool:
        """Check if data has time-series characteristics"""
        time_indicators = ['date', 'time', 'year', 'month', 'day', 'period']
        column_names_lower = [col.lower() for col in columns]
        
        return any(indicator in ' '.join(column_names_lower) for indicator in time_indicators)
    
    def _create_summary_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """Create summary statistics for numeric data"""
        if not data:
            return {}
        
        stats = {
            "total_records": len(data),
            "data_quality": "good" if len(data) > 5 else "limited"
        }
        
        # Add more sophisticated statistics as needed
        return stats
