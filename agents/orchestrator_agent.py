"""
Orchestrator Agent - Central coordinator for the multi-agent system
"""

import json
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentState, AgentMessage
from agents.agent_configs import ORCHESTRATOR_CONFIG

class OrchestratorAgent(BaseAgent):
    """Central orchestrator that manages the workflow between all agents"""
    
    def __init__(self, openai_client):
        super().__init__(ORCHESTRATOR_CONFIG, openai_client)
        self.conversation_history = {}
    
    async def process(self, state: AgentState) -> AgentState:
        """Process user query and coordinate agent workflow"""
        try:
            self.log_step(state, "processing_user_query", state.user_query)
            
            # Analyze user query to determine workflow
            workflow_decision = await self._analyze_query(state)
            state.context["workflow_plan"] = workflow_decision
            
            # Create initial routing message
            routing_message = self.create_message(
                recipient=workflow_decision["next_agent"],
                content={
                    "user_query": state.user_query,
                    "workflow_plan": workflow_decision,
                    "context": state.context
                },
                message_type="query"
            )
            
            state = self.add_message_to_state(state, routing_message)
            state.current_step = workflow_decision["next_agent"]
            
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "query_processing")
    
    async def _analyze_query(self, state: AgentState) -> Dict[str, Any]:
        """Analyze user query to determine appropriate workflow"""
        
        analysis_prompt = f"""
        Analyze the following user query and determine the appropriate workflow:
        
        Query: "{state.user_query}"
        
        Available workflows:
        1. simple_query: For basic database queries, table listings, or simple data retrieval
        2. default_flow: For mutual fund analysis requiring SQL data + expert analysis
        3. with_web_research: For queries needing current market information or recent news
        
        Consider:
        - Does the query ask for current/recent market information? → use with_web_research
        - Does the query ask for fund analysis, comparison, or investment advice? → use default_flow  
        - Does the query ask for simple data or table information? → use simple_query
        
        Respond with JSON format:
        {{
            "workflow_type": "simple_query|default_flow|with_web_research",
            "next_agent": "sql_agent",
            "reasoning": "explanation of why this workflow was chosen",
            "requires_web_data": true/false,
            "complexity_level": "low|medium|high"
        }}
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.1)
        
        try:
            decision = json.loads(response)
            self.log_step(state, "workflow_decision", f"Chose {decision['workflow_type']}")
            return decision
        except json.JSONDecodeError:
            # Fallback to default workflow
            return {
                "workflow_type": "default_flow",
                "next_agent": "sql_agent", 
                "reasoning": "JSON parsing failed, using default workflow",
                "requires_web_data": False,
                "complexity_level": "medium"
            }
    
    async def finalize_response(self, state: AgentState) -> Dict[str, Any]:
        """Create final response to user after all agents have processed"""
        try:
            # Get the formatted output from data formatter
            formatter_message = self.get_latest_message_from(state, "data_formatter")
            
            if formatter_message and formatter_message.message_type == "formatted_output":
                response_content = formatter_message.content
            else:
                # Fallback - create response from available data
                response_content = await self._create_fallback_response(state)
            
            # Store conversation history
            self._store_conversation(state, response_content)
            
            return {
                "success": True,
                "response": response_content,
                "workflow_executed": state.context.get("workflow_plan", {}),
                "agents_involved": list(set([msg.sender for msg in state.messages])),
                "session_id": state.session_id
            }
            
        except Exception as e:
            self.logger.error(f"Error finalizing response: {e}")
            return {
                "success": False,
                "error": str(e),
                "partial_data": state.data,
                "session_id": state.session_id
            }
    
    async def _create_fallback_response(self, state: AgentState) -> str:
        """Create fallback response when formatted output is not available"""
        
        # Collect all available data
        sql_data = None
        expert_analysis = None
        web_info = None
        
        for message in state.messages:
            if message.sender == "sql_agent" and message.message_type == "data":
                sql_data = message.content
            elif message.sender == "mutual_fund_expert" and message.message_type == "analysis":
                expert_analysis = message.content
            elif message.sender == "web_agent" and message.message_type == "data":
                web_info = message.content
        
        # Create response using available data
        fallback_prompt = f"""
        Create a comprehensive response to the user query: "{state.user_query}"
        
        Available data:
        SQL Data: {sql_data if sql_data else "None"}
        Expert Analysis: {expert_analysis if expert_analysis else "None"}
        Web Information: {web_info if web_info else "None"}
        
        Create a clear, informative response that addresses the user's question.
        Use professional financial language appropriate for Indian mutual fund investors.
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": fallback_prompt}
        ]
        
        return await self.llm_call(messages, temperature=0.2)
    
    def _store_conversation(self, state: AgentState, response: str):
        """Store conversation history for future reference"""
        session_id = state.session_id
        
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "timestamp": state.messages[0].timestamp if state.messages else None,
            "user_query": state.user_query,
            "response": response,
            "workflow": state.context.get("workflow_plan", {}),
            "errors": state.errors
        })
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return self.conversation_history.get(session_id, [])
