"""
SQL Agent Wrapper - Integrates existing SQL agent with multi-agent system
"""

import json
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent, AgentState
from agents.agent_configs import SQL_AGENT_CONFIG
from enhanced_sql_agent import create_enhanced_user_agent

class SQLAgentWrapper(BaseAgent):
    """Wrapper for existing SQL agent to integrate with multi-agent system"""
    
    def __init__(self, openai_client):
        super().__init__(SQL_AGENT_CONFIG, openai_client)
        self.sql_agents = {}  # Cache for user-specific SQL agents
    
    async def process(self, state: AgentState) -> AgentState:
        """Process SQL queries using existing enhanced SQL agent"""
        try:
            self.log_step(state, "processing_sql_query", state.user_query)
            
            # Get or create user-specific SQL agent
            sql_agent = self._get_sql_agent(state.user_email)
            
            # Extract query from orchestrator message
            orchestrator_message = self.get_latest_message_from(state, "orchestrator")
            if orchestrator_message:
                user_query = orchestrator_message.content.get("user_query", state.user_query)
                context = orchestrator_message.content.get("context", {})
            else:
                user_query = state.user_query
                context = state.context
            
            # Analyze query to determine if it needs SQL execution or schema info
            query_analysis = await self._analyze_sql_query(user_query)
            
            if query_analysis["needs_sql_execution"]:
                # Execute SQL query
                sql_result = sql_agent.process_query(
                    query=user_query,
                    session_id=state.session_id
                )
            else:
                # Provide schema information
                sql_result = self._get_schema_information(sql_agent, query_analysis)
            
            # Format result for next agent
            formatted_result = self._format_sql_result(sql_result, query_analysis)
            
            # Determine next agent based on workflow
            next_agent = self._determine_next_agent(state, query_analysis)
            
            # Create message for next agent
            result_message = self.create_message(
                recipient=next_agent,
                content={
                    "sql_data": formatted_result,
                    "original_query": user_query,
                    "query_analysis": query_analysis,
                    "database_info": self._get_database_summary(sql_agent)
                },
                message_type="data",
                metadata={"execution_time": sql_result.get("execution_time")}
            )
            
            state = self.add_message_to_state(state, result_message)
            state.current_step = next_agent
            state.data["sql_result"] = formatted_result
            
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "sql_processing")
    
    def _get_sql_agent(self, user_email: str):
        """Get or create user-specific SQL agent"""
        if user_email not in self.sql_agents:
            self.sql_agents[user_email] = create_enhanced_user_agent(user_email)
        return self.sql_agents[user_email]
    
    async def _analyze_sql_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine SQL execution requirements"""
        
        analysis_prompt = f"""
        Analyze this query to determine what SQL operations are needed:
        
        Query: "{query}"
        
        Determine:
        1. Does it need actual SQL execution (data retrieval) or just schema information?
        2. What type of data is being requested?
        3. What databases/tables might be involved?
        4. Is it a simple lookup or complex analysis?
        
        Respond in JSON format:
        {{
            "needs_sql_execution": true/false,
            "query_type": "schema_info|data_retrieval|analysis|comparison",
            "databases_involved": ["list", "of", "databases"],
            "tables_involved": ["list", "of", "tables"],
            "complexity": "low|medium|high",
            "estimated_result_size": "small|medium|large"
        }}
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.1)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Safe fallback
            return {
                "needs_sql_execution": True,
                "query_type": "data_retrieval",
                "databases_involved": ["portfoliosql"],
                "tables_involved": ["unknown"],
                "complexity": "medium",
                "estimated_result_size": "medium"
            }
    
    def _get_schema_information(self, sql_agent, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema information instead of executing queries"""
        try:
            database_info = sql_agent.database_info
            
            return {
                "success": True,
                "schema_info": {
                    "available_databases": [db["name"] for db in database_info.get("databases", [])],
                    "total_tables": sum(len(db.get("tables", [])) for db in database_info.get("databases", [])),
                    "user_schema": database_info.get("current_schema"),
                    "database_summary": database_info
                },
                "query_type": "schema_info",
                "message": "Schema information retrieved successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": "schema_info"
            }
    
    def _format_sql_result(self, sql_result: Dict[str, Any], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format SQL result for consumption by other agents"""
        
        if not sql_result.get("success", False):
            return {
                "success": False,
                "error": sql_result.get("error", "Unknown SQL error"),
                "query_analysis": query_analysis
            }
        
        formatted = {
            "success": True,
            "query_analysis": query_analysis,
            "data_type": query_analysis.get("query_type", "unknown")
        }
        
        if query_analysis.get("query_type") == "schema_info":
            formatted["schema_info"] = sql_result.get("schema_info", {})
        else:
            # Handle actual query results
            formatted.update({
                "data": sql_result.get("data", []),
                "columns": sql_result.get("columns", []),
                "row_count": len(sql_result.get("data", [])),
                "database": sql_result.get("database"),
                "schema": sql_result.get("schema"),
                "query_executed": sql_result.get("query", ""),
                "execution_time": sql_result.get("execution_time")
            })
        
        return formatted
    
    def _determine_next_agent(self, state: AgentState, query_analysis: Dict[str, Any]) -> str:
        """Determine which agent should process the data next"""
        workflow_plan = state.context.get("workflow_plan", {})
        workflow_type = workflow_plan.get("workflow_type", "default_flow")
        
        if workflow_type == "simple_query":
            return "data_formatter"
        elif query_analysis.get("query_type") == "schema_info":
            return "data_formatter"
        else:
            return "mutual_fund_expert"
    
    def _get_database_summary(self, sql_agent) -> Dict[str, Any]:
        """Get summary of available databases for context"""
        try:
            db_info = sql_agent.database_info
            return {
                "total_databases": len(db_info.get("databases", [])),
                "database_names": [db["name"] for db in db_info.get("databases", [])],
                "current_schema": db_info.get("current_schema"),
                "total_tables": sum(len(db.get("tables", [])) for db in db_info.get("databases", []))
            }
        except:
            return {"error": "Could not retrieve database summary"}
    
    def refresh_agent_cache(self, user_email: str):
        """Refresh cached SQL agent for user"""
        if user_email in self.sql_agents:
            del self.sql_agents[user_email]
