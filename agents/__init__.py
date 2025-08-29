"""
Three-Agent Pipeline System for Financial Data Analysis

This package contains a streamlined three-agent pipeline system that coordinates
specialized agents for comprehensive financial analysis and insights.

Core Three-Agent Pipeline:
- EnhancedMultiDatabaseSQLAgent: Database discovery, connection management, SQL execution
- MutualFundQuantAgent: Pandas operations, complex calculations, financial metrics  
- DataFormatterAgent: Plotly visualization, data formatting, output generation

Orchestration:
- AgentOrchestrator: Manages sequential flow through the three-agent pipeline

Usage:
    from services.agent_orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator(static_dir="static/charts")
    result = await orchestrator.process_query(
        user_email="user@example.com",
        session_id="session123",
        query="Show me top performing mutual funds",
        discovery_mode="multitenant"
    )
"""

# Core three-agent pipeline
from .enhanced_sql_agent import EnhancedSQLAgent, create_enhanced_sql_agent
from .mutual_fund_quant_agent import MutualFundQuantAgent
from .data_formatter_agent import DataFormatterAgent

__all__ = [
    'EnhancedSQLAgent',
    'create_enhanced_sql_agent', 
    'MutualFundQuantAgent',
    'DataFormatterAgent'
]

__version__ = "1.0.0"
