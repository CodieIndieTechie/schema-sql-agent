"""
Base Agent Class for Multi-Agent System
Provides common functionality for all agents
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid
from datetime import datetime
import openai
from agents.agent_configs import AgentConfig

logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Standardized message format between agents"""
    id: str
    sender: str
    recipient: str
    content: Any
    message_type: str  # "query", "data", "analysis", "formatted_output", "error"
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AgentState:
    """Agent execution state"""
    current_step: str
    messages: List[AgentMessage]
    data: Dict[str, Any]
    user_query: str
    session_id: str
    user_email: str
    errors: List[str]
    context: Dict[str, Any]

class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system"""
    
    def __init__(self, config: AgentConfig, openai_client: Optional[openai.OpenAI] = None):
        self.config = config
        self.name = config.name
        self.client = openai_client
        self.logger = logging.getLogger(f"agent.{self.name}")
        
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state"""
        pass
    
    def create_message(
        self, 
        recipient: str, 
        content: Any, 
        message_type: str = "data",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """Create a standardized message"""
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            recipient=recipient,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
    
    def add_message_to_state(self, state: AgentState, message: AgentMessage) -> AgentState:
        """Add a message to the state"""
        state.messages.append(message)
        return state
    
    def get_messages_for_agent(self, state: AgentState, agent_name: str) -> List[AgentMessage]:
        """Get all messages intended for a specific agent"""
        return [msg for msg in state.messages if msg.recipient == agent_name]
    
    def get_latest_message_from(self, state: AgentState, sender: str) -> Optional[AgentMessage]:
        """Get the latest message from a specific sender"""
        messages = [msg for msg in state.messages if msg.sender == sender]
        return messages[-1] if messages else None
    
    async def llm_call(
        self, 
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        max_tokens: int = 2000
    ) -> str:
        """Make a call to the LLM"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    def log_step(self, state: AgentState, action: str, details: str = ""):
        """Log agent actions for debugging"""
        self.logger.info(f"[{state.session_id}] {self.name}: {action} - {details}")
    
    def handle_error(self, state: AgentState, error: Exception, context: str = "") -> AgentState:
        """Handle errors and update state"""
        error_msg = f"{self.name} error in {context}: {str(error)}"
        state.errors.append(error_msg)
        self.logger.error(error_msg, exc_info=True)
        
        # Create error message
        error_message = self.create_message(
            recipient="orchestrator",
            content={"error": error_msg, "context": context},
            message_type="error"
        )
        return self.add_message_to_state(state, error_message)
