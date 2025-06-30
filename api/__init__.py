"""
API Module for Multi-Agent Financial Analysis System

This module contains all FastAPI endpoints and routing logic for the application.
It provides both traditional SQL agent endpoints and new multi-agent system endpoints.

Modules:
- multi_agent_api: Multi-agent system endpoints
- multitenant_api: Original SQL agent endpoints (existing)
"""

from .multi_agent_api import router as multi_agent_router

__all__ = ["multi_agent_router"]
