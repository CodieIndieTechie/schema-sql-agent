"""
Services module for multi-agent system

Provides high-level business logic and service layer abstractions.
"""

from .multi_agent_service import (
    MultiAgentService,
    QuerySession,
    QueryResult,
    get_multi_agent_service
)

__all__ = [
    "MultiAgentService",
    "QuerySession", 
    "QueryResult",
    "get_multi_agent_service"
]
