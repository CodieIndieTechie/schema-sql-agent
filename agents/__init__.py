"""
Multi-Agent System for Financial Data Analysis

This package contains a sophisticated multi-agent system built on top of the existing
SQL agent infrastructure. The system coordinates multiple specialized agents to provide
comprehensive financial analysis and insights.

Agents:
- OrchestratorAgent: Main coordinator and query router
- SQLAgentWrapper: Database query execution and schema management
- MutualFundExpertAgent: Financial analysis and investment insights
- WebAgent: Market research and current information gathering
- DataFormatterAgent: Response formatting and visualization

Usage:
    from agents.multi_agent_orchestrator import MultiAgentOrchestrator
    
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.process_query(
        user_query="Show me top performing mutual funds",
        user_email="user@example.com"
    )
"""

from .multi_agent_orchestrator import MultiAgentOrchestrator
from .orchestrator_agent import OrchestratorAgent
from .sql_agent_wrapper import SQLAgentWrapper
from .mutual_fund_expert import MutualFundExpertAgent
from .web_agent import WebAgent  
from .data_formatter import DataFormatterAgent
from .base_agent import BaseAgent, AgentState, AgentMessage

__all__ = [
    'MultiAgentOrchestrator',
    'OrchestratorAgent',
    'SQLAgentWrapper', 
    'MutualFundExpertAgent',
    'WebAgent',
    'DataFormatterAgent',
    'BaseAgent',
    'AgentState',
    'AgentMessage'
]

__version__ = "1.0.0"
