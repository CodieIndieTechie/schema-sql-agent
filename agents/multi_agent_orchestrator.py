"""
Multi-Agent Orchestrator - Coordinates all agents using workflow management
"""

import asyncio
from typing import Dict, Any, Optional, List
from agents.base_agent import AgentState
from agents.orchestrator_agent import OrchestratorAgent
from agents.sql_agent_wrapper import SQLAgentWrapper
from agents.mutual_fund_expert import MutualFundExpertAgent
from agents.web_agent import WebAgent
from agents.data_formatter import DataFormatterAgent
import openai
import os
from config.multi_agent_config import get_config, get_openai_config, get_orchestrator_config

class MultiAgentOrchestrator:
    """Main orchestrator that coordinates all agents in the multi-agent system"""
    
    def __init__(self):
        # Load configuration
        self.config = get_config()
        openai_config = get_openai_config()
        orchestrator_config = get_orchestrator_config()
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=openai_config.api_key)
        
        # Initialize all agents
        self.agents = {
            "orchestrator": OrchestratorAgent(self.openai_client),
            "sql_agent": SQLAgentWrapper(self.openai_client),
            "mutual_fund_expert": MutualFundExpertAgent(self.openai_client),
            "web_agent": WebAgent(self.openai_client),
            "data_formatter": DataFormatterAgent(self.openai_client)
        }
        
        # Workflow configuration from environment
        self.max_iterations = orchestrator_config.max_iterations
        self.timeout_seconds = orchestrator_config.timeout_seconds
        
    async def process_query(
        self, 
        user_query: str, 
        user_email: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system
        
        Args:
            user_query: The user's natural language query
            user_email: User's email for schema isolation
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Dict containing the final response and metadata
        """
        try:
            # Initialize state
            state = AgentState(
                user_query=user_query,
                user_email=user_email,
                session_id=session_id or f"session_{user_email}_{int(asyncio.get_event_loop().time())}",
                current_step="orchestrator",
                messages=[],
                data={},
                context={},
                errors=[]
            )
            
            # Start orchestration
            final_state = await self._orchestrate_workflow(state)
            
            # Extract final response
            final_response = self._extract_final_response(final_state)
            
            return {
                "success": True,
                "response": final_response,
                "session_id": final_state.session_id,
                "metadata": {
                    "total_steps": len(final_state.messages),
                    "workflow_path": self._get_workflow_path(final_state),
                    "processing_time": final_state.data.get("total_processing_time"),
                    "agents_used": list(set([msg.sender for msg in final_state.messages]))
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your query. Please try again or rephrase your question.",
                "session_id": session_id
            }
    
    async def _orchestrate_workflow(self, state: AgentState) -> AgentState:
        """Orchestrate the workflow through all agents"""
        
        iteration_count = 0
        start_time = asyncio.get_event_loop().time()
        
        while (state.current_step != "completed" and 
               iteration_count < self.max_iterations and
               (asyncio.get_event_loop().time() - start_time) < self.timeout_seconds):
            
            try:
                # Get current agent
                current_agent = self.agents.get(state.current_step)
                if not current_agent:
                    raise ValueError(f"Unknown agent: {state.current_step}")
                
                # Process current step
                state = await current_agent.process(state)
                
                iteration_count += 1
                
                # Log progress
                print(f"Step {iteration_count}: {state.current_step} -> {getattr(state, 'next_step', 'continuing')}")
                
            except Exception as e:
                # Handle agent errors
                state.errors.append({
                    "agent": state.current_step,
                    "error": str(e),
                    "iteration": iteration_count
                })
                
                # Try to recover or end workflow
                if state.current_step == "orchestrator":
                    # If orchestrator fails, end workflow
                    break
                else:
                    # Send back to orchestrator for error handling
                    state.current_step = "orchestrator"
        
        # Record total processing time
        state.data["total_processing_time"] = asyncio.get_event_loop().time() - start_time
        
        return state
    
    def _extract_final_response(self, state: AgentState) -> str:
        """Extract the final formatted response from the workflow"""
        
        # Look for formatted response from data formatter
        for message in reversed(state.messages):
            if (message.sender == "data_formatter" and 
                message.message_type == "formatted_output"):
                return message.content.get("content", "No response available")
        
        # Fallback to orchestrator final response
        for message in reversed(state.messages):
            if (message.sender == "orchestrator" and 
                message.message_type == "final_response"):
                return message.content.get("content", "No response available")
        
        # Ultimate fallback
        if state.errors:
            return f"I encountered some errors while processing your query: {'; '.join([err['error'] for err in state.errors[-3:]])}"
        else:
            return "I was unable to generate a complete response. Please try rephrasing your query."
    
    def _get_workflow_path(self, state: AgentState) -> List[str]:
        """Get the path of agents that were used in the workflow"""
        path = []
        for message in state.messages:
            if message.sender not in path:
                path.append(message.sender)
        return path
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of all agents"""
        
        health_status = {
            "orchestrator_status": "healthy",
            "total_agents": len(self.agents),
            "agents": {}
        }
        
        for agent_name, agent in self.agents.items():
            try:
                # Basic agent check
                health_status["agents"][agent_name] = {
                    "status": "healthy",
                    "config_loaded": hasattr(agent, 'config'),
                    "llm_client": hasattr(agent, 'openai_client')
                }
            except Exception as e:
                health_status["agents"][agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    def get_available_workflows(self) -> Dict[str, Any]:
        """Get information about available workflows"""
        
        return {
            "available_workflows": [
                "simple_query",
                "full_analysis_with_web",
                "comparison_analysis",
                "portfolio_analysis",
                "performance_analysis"
            ],
            "workflow_descriptions": {
                "simple_query": "Direct SQL query with basic formatting",
                "full_analysis_with_web": "Complete analysis with expert insights and web research",
                "comparison_analysis": "Comparative analysis of multiple funds",
                "portfolio_analysis": "Portfolio-level analysis and recommendations",
                "performance_analysis": "Detailed performance analysis with benchmarking"
            },
            "agent_capabilities": {
                "orchestrator": "Query routing and workflow management",
                "sql_agent": "Database queries and schema information",
                "mutual_fund_expert": "Financial analysis and investment insights",
                "web_agent": "Current market research and news",
                "data_formatter": "Beautiful data presentation and visualization"
            }
        }
    
    async def process_query_streaming(
        self, 
        user_query: str, 
        user_email: str, 
        session_id: Optional[str] = None
    ):
        """
        Process query with streaming updates (for real-time UI updates)
        
        This is a generator that yields progress updates
        """
        try:
            # Initialize state
            state = AgentState(
                user_query=user_query,
                user_email=user_email,
                session_id=session_id or f"session_{user_email}_{int(asyncio.get_event_loop().time())}",
                current_step="orchestrator",
                messages=[],
                data={},
                context={},
                errors=[]
            )
            
            iteration_count = 0
            start_time = asyncio.get_event_loop().time()
            
            yield {"status": "started", "message": "Analyzing your query..."}
            
            while (state.current_step != "completed" and 
                   iteration_count < self.max_iterations):
                
                current_agent = self.agents.get(state.current_step)
                if not current_agent:
                    break
                
                # Yield progress update
                yield {
                    "status": "processing",
                    "current_agent": state.current_step,
                    "step": iteration_count + 1,
                    "message": f"Processing with {state.current_step}..."
                }
                
                # Process current step
                state = await current_agent.process(state)
                iteration_count += 1
            
            # Extract final response
            final_response = self._extract_final_response(state)
            
            yield {
                "status": "completed",
                "response": final_response,
                "metadata": {
                    "total_steps": iteration_count,
                    "processing_time": asyncio.get_event_loop().time() - start_time,
                    "agents_used": list(set([msg.sender for msg in state.messages]))
                }
            }
            
        except Exception as e:
            yield {
                "status": "error",
                "error": str(e),
                "response": "An error occurred while processing your query."
            }
