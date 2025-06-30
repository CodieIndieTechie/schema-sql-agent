"""
Mutual Fund Expert Agent - Financial analysis specialist for Indian mutual funds, index funds, and ETFs
"""

import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentState
from agents.agent_configs import MUTUAL_FUND_EXPERT_CONFIG

class MutualFundExpertAgent(BaseAgent):
    """Expert agent for mutual fund analysis and investment insights"""
    
    def __init__(self, openai_client):
        super().__init__(MUTUAL_FUND_EXPERT_CONFIG, openai_client)
        self.analysis_cache = {}
    
    async def process(self, state: AgentState) -> AgentState:
        """Analyze mutual fund data and provide expert insights"""
        try:
            self.log_step(state, "analyzing_mutual_fund_data", "Starting financial analysis")
            
            # Get data from SQL agent
            sql_message = self.get_latest_message_from(state, "sql_agent")
            if not sql_message:
                raise ValueError("No data received from SQL agent")
            
            sql_data = sql_message.content.get("sql_data", {})
            original_query = sql_data.get("original_query", state.user_query)
            
            # Perform analysis based on data type
            if sql_data.get("data_type") == "schema_info":
                analysis_result = await self._analyze_schema_query(original_query, sql_data)
            else:
                analysis_result = await self._analyze_fund_data(original_query, sql_data, state)
            
            # Determine next agent
            workflow_plan = state.context.get("workflow_plan", {})
            needs_web_research = workflow_plan.get("requires_web_data", False)
            next_agent = "web_agent" if needs_web_research else "data_formatter"
            
            # Create message for next agent
            analysis_message = self.create_message(
                recipient=next_agent,
                content={
                    "expert_analysis": analysis_result,
                    "original_query": original_query,
                    "sql_data": sql_data,
                    "analysis_metadata": {
                        "analysis_type": analysis_result.get("analysis_type"),
                        "confidence_level": analysis_result.get("confidence_level"),
                        "requires_web_data": needs_web_research
                    }
                },
                message_type="analysis"
            )
            
            state = self.add_message_to_state(state, analysis_message)
            state.current_step = next_agent
            state.data["expert_analysis"] = analysis_result
            
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "mutual_fund_analysis")
    
    async def _analyze_schema_query(self, query: str, sql_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze schema-related queries"""
        
        schema_info = sql_data.get("schema_info", {})
        
        analysis_prompt = f"""
        The user asked: "{query}"
        
        Available database information:
        - Databases: {schema_info.get('available_databases', [])}
        - Total tables: {schema_info.get('total_tables', 0)}
        - User schema: {schema_info.get('user_schema', 'unknown')}
        
        As a mutual fund expert, explain what data is available and how it can be used for investment analysis.
        Focus on:
        1. What types of mutual fund data are available
        2. How this data can help with investment decisions
        3. What analysis can be performed
        4. Suggest specific questions the user might want to ask
        
        Provide a helpful, educational response about the available financial data.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.3)
        
        return {
            "analysis_type": "schema_explanation",
            "content": response,
            "confidence_level": "high",
            "data_availability": schema_info,
            "suggested_queries": self._generate_suggested_queries(schema_info)
        }
    
    async def _analyze_fund_data(self, query: str, sql_data: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Analyze actual mutual fund data"""
        
        data = sql_data.get("data", [])
        columns = sql_data.get("columns", [])
        
        if not data:
            return {
                "analysis_type": "no_data",
                "content": "No data was retrieved for analysis. Please refine your query or check data availability.",
                "confidence_level": "low"
            }
        
        # Determine analysis type based on data structure
        analysis_type = self._determine_analysis_type(query, columns, data)
        
        # Perform specific analysis
        if analysis_type == "performance_analysis":
            return await self._analyze_performance(query, data, columns)
        elif analysis_type == "comparison_analysis":
            return await self._analyze_comparison(query, data, columns)
        elif analysis_type == "portfolio_analysis":
            return await self._analyze_portfolio(query, data, columns)
        elif analysis_type == "fund_search":
            return await self._analyze_fund_search(query, data, columns)
        else:
            return await self._general_analysis(query, data, columns)
    
    def _determine_analysis_type(self, query: str, columns: List[str], data: List[Dict]) -> str:
        """Determine the type of analysis needed based on query and data"""
        
        query_lower = query.lower()
        column_names = [col.lower() for col in columns]
        
        # Check for performance-related keywords
        if any(word in query_lower for word in ["performance", "return", "nav", "growth", "yield"]):
            return "performance_analysis"
        
        # Check for comparison keywords
        elif any(word in query_lower for word in ["compare", "vs", "better", "best", "worst"]):
            return "comparison_analysis"
        
        # Check for portfolio keywords
        elif any(word in query_lower for word in ["portfolio", "allocation", "holding", "investment"]):
            return "portfolio_analysis"
        
        # Check for search/filter keywords
        elif any(word in query_lower for word in ["find", "search", "list", "show", "funds"]):
            return "fund_search"
        
        else:
            return "general_analysis"
    
    async def _analyze_performance(self, query: str, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Analyze fund performance data"""
        
        analysis_prompt = f"""
        Analyze the following mutual fund performance data for the query: "{query}"
        
        Data columns: {columns}
        Sample data (first 5 rows): {data[:5]}
        Total rows: {len(data)}
        
        Provide performance analysis including:
        1. Key performance metrics and trends
        2. Risk assessment
        3. Comparison to benchmarks (if available)
        4. Investment recommendations
        5. Important caveats and considerations
        
        Focus on actionable insights for Indian mutual fund investors.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.3)
        
        return {
            "analysis_type": "performance_analysis",
            "content": response,
            "confidence_level": "high",
            "data_summary": {
                "total_funds": len(data),
                "columns_analyzed": columns,
                "key_metrics": self._extract_key_metrics(data, columns)
            }
        }
    
    async def _analyze_comparison(self, query: str, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Analyze comparative fund data"""
        
        analysis_prompt = f"""
        Perform comparative analysis for the query: "{query}"
        
        Data columns: {columns}
        Data: {data}
        
        Provide comparative analysis including:
        1. Head-to-head comparison of funds
        2. Strengths and weaknesses of each
        3. Risk-adjusted returns
        4. Suitability for different investor profiles
        5. Clear recommendation with reasoning
        
        Present in a structured, easy-to-compare format.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.3)
        
        return {
            "analysis_type": "comparison_analysis",
            "content": response,
            "confidence_level": "high",
            "comparison_summary": {
                "funds_compared": len(data),
                "comparison_criteria": columns
            }
        }
    
    async def _analyze_portfolio(self, query: str, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Analyze portfolio-related data"""
        
        analysis_prompt = f"""
        Analyze portfolio data for the query: "{query}"
        
        Data columns: {columns}
        Portfolio data: {data}
        
        Provide portfolio analysis including:
        1. Asset allocation breakdown
        2. Diversification assessment
        3. Risk concentration areas
        4. Rebalancing recommendations
        5. Performance attribution
        
        Focus on portfolio optimization and risk management.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.3)
        
        return {
            "analysis_type": "portfolio_analysis",
            "content": response,
            "confidence_level": "high",
            "portfolio_metrics": self._calculate_portfolio_metrics(data, columns)
        }
    
    async def _analyze_fund_search(self, query: str, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Analyze fund search/listing results"""
        
        analysis_prompt = f"""
        Analyze fund search results for the query: "{query}"
        
        Available funds data:
        Columns: {columns}
        Number of funds: {len(data)}
        Sample funds: {data[:10]}
        
        Provide analysis including:
        1. Overview of available funds
        2. Categories and types represented
        3. Key differentiators between funds
        4. Selection criteria recommendations
        5. Top picks with reasoning
        
        Help the user make informed investment decisions.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.3)
        
        return {
            "analysis_type": "fund_search",
            "content": response,
            "confidence_level": "high",
            "search_summary": {
                "total_funds": len(data),
                "fund_categories": self._categorize_funds(data, columns)
            }
        }
    
    async def _general_analysis(self, query: str, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """General financial data analysis"""
        
        analysis_prompt = f"""
        Provide general financial analysis for the query: "{query}"
        
        Data available:
        Columns: {columns}
        Data: {data}
        
        As a mutual fund expert, provide:
        1. Key insights from the data
        2. Financial implications
        3. Investment considerations
        4. Actionable recommendations
        5. Risk factors to consider
        
        Tailor the analysis to Indian mutual fund context.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.3)
        
        return {
            "analysis_type": "general_analysis",
            "content": response,
            "confidence_level": "medium",
            "data_insights": self._extract_general_insights(data, columns)
        }
    
    def _generate_suggested_queries(self, schema_info: Dict[str, Any]) -> List[str]:
        """Generate suggested queries based on available data"""
        suggestions = [
            "Show me the top performing mutual funds this year",
            "Compare large cap vs mid cap fund performance",
            "Find low-cost index funds in my database",
            "Show me funds with highest returns in the last 5 years",
            "List all SIP-eligible funds"
        ]
        return suggestions
    
    def _extract_key_metrics(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Extract key metrics from fund data"""
        # Simplified metrics extraction
        return {
            "total_records": len(data),
            "columns_available": len(columns),
            "analysis_scope": "mutual_fund_data"
        }
    
    def _calculate_portfolio_metrics(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Calculate basic portfolio metrics"""
        return {
            "holdings_count": len(data),
            "diversification_score": "medium",  # Simplified
            "risk_level": "moderate"  # Simplified
        }
    
    def _categorize_funds(self, data: List[Dict], columns: List[str]) -> Dict[str, int]:
        """Categorize funds by type"""
        # Simplified categorization
        return {
            "equity_funds": len([d for d in data if "equity" in str(d).lower()]),
            "debt_funds": len([d for d in data if "debt" in str(d).lower()]),
            "hybrid_funds": len([d for d in data if "hybrid" in str(d).lower()]),
            "other_funds": len(data)
        }
    
    def _extract_general_insights(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Extract general insights from data"""
        return {
            "data_completeness": "good" if data else "poor",
            "analysis_confidence": "high" if len(data) > 10 else "medium",
            "recommendation_basis": "data_driven" if data else "general_guidance"
        }
