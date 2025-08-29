"""
Services module for three-agent pipeline system

Provides the agent orchestrator service for coordinating the three-agent pipeline.
"""

from .agent_orchestrator import AgentOrchestrator, get_orchestrator

__all__ = [
    "AgentOrchestrator",
    "get_orchestrator"
]
