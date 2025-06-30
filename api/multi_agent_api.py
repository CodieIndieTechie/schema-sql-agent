"""
Multi-Agent System FastAPI Endpoints

This module provides REST API endpoints for the multi-agent financial analysis system.
All endpoints interface with the MultiAgentOrchestrator to coordinate agent workflows.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from services.multi_agent_service import get_multi_agent_service, MultiAgentService
from config.multi_agent_config import get_config

# Initialize router
router = APIRouter(prefix="/multi-agent", tags=["Multi-Agent System"])

# Dependency injection for service
def get_service() -> MultiAgentService:
    """Get singleton service instance"""
    return get_multi_agent_service()

# Request/Response Models
class MultiAgentQueryRequest(BaseModel):
    """Request model for multi-agent queries"""
    query: str = Field(..., description="Natural language query about financial data")
    user_email: str = Field(..., description="User email for schema isolation")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    workflow_preference: Optional[str] = Field(None, description="Preferred workflow type")
    enable_web_research: bool = Field(True, description="Enable web research in analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Show me the best performing mutual funds in the last year",
                "user_email": "investor@example.com",
                "session_id": "session_123",
                "workflow_preference": "full_analysis_with_web",
                "enable_web_research": True
            }
        }

class MultiAgentQueryResponse(BaseModel):
    """Response model for multi-agent queries"""
    success: bool
    response: str
    session_id: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "response": "# Top Performing Mutual Funds Analysis\n\n## Executive Summary\n...",
                "session_id": "session_123",
                "metadata": {
                    "total_steps": 5,
                    "workflow_path": ["orchestrator", "sql_agent", "mutual_fund_expert", "data_formatter"],
                    "processing_time": 12.5,
                    "agents_used": ["orchestrator", "sql_agent", "mutual_fund_expert", "web_agent", "data_formatter"]
                }
            }
        }

class AgentHealthResponse(BaseModel):
    """Response model for agent health check"""
    orchestrator_status: str
    total_agents: int
    agents: Dict[str, Dict[str, Any]]
    timestamp: str

class WorkflowInfoResponse(BaseModel):
    """Response model for workflow information"""
    available_workflows: List[str]
    workflow_descriptions: Dict[str, str]
    agent_capabilities: Dict[str, str]

# Main Endpoints

@router.post("/query", response_model=MultiAgentQueryResponse)
async def process_multi_agent_query(
    request: MultiAgentQueryRequest,
    service: MultiAgentService = Depends(get_service)
):
    """
    Process a natural language query through the multi-agent system
    
    This endpoint coordinates multiple specialized agents to provide comprehensive
    financial analysis and insights based on the user's query.
    """
    try:
        # Validate input
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if not request.user_email.strip():
            raise HTTPException(status_code=400, detail="User email is required")
        
        # Process query through multi-agent system
        result = await service.process_query(
            query=request.query,
            user_email=request.user_email,
            session_id=request.session_id,
            enable_caching=request.enable_caching
        )
        
        return MultiAgentQueryResponse(
            success=result.success,
            response=result.response,
            session_id=result.session_id,
            processing_time=result.processing_time,
            agents_used=result.agents_used,
            workflow_path=result.workflow_path,
            metadata=result.metadata,
            error=result.error
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing multi-agent query: {str(e)}"
        )

@router.post("/query/stream")
async def process_multi_agent_query_stream(
    request: MultiAgentQueryRequest,
    service: MultiAgentService = Depends(get_service)
):
    """
    Process a query with streaming updates for real-time progress
    
    Returns a stream of JSON objects showing the progress through each agent.
    """
    try:
        async def generate_stream():
            async for update in service.process_query_stream(
                query=request.query,
                user_email=request.user_email,
                session_id=request.session_id
            ):
                yield f"data: {json.dumps(update)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in streaming query: {str(e)}"
        )

@router.get("/health", response_model=AgentHealthResponse)
async def get_agent_health(
    service: MultiAgentService = Depends(get_service)
):
    """
    Get health status of all agents in the multi-agent system
    """
    try:
        health_data = await service.get_system_health()
        orchestrator_data = health_data.get("orchestrator", {})
        
        return AgentHealthResponse(
            orchestrator_status=orchestrator_data.get("status", "unknown"),
            total_agents=orchestrator_data.get("total_agents", 0),
            agents=orchestrator_data.get("agents", {}),
            timestamp=health_data.get("timestamp", datetime.now().isoformat())
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking agent health: {str(e)}"
        )

@router.get("/workflows", response_model=WorkflowInfoResponse)
async def get_workflow_info(
    service: MultiAgentService = Depends(get_service)
):
    """
    Get information about available workflows and agent capabilities
    """
    try:
        workflow_info = service.orchestrator.get_available_workflows()
        return WorkflowInfoResponse(**workflow_info)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving workflow info: {str(e)}"
        )

# Agent Management Endpoints

@router.post("/agents/refresh/{user_email}")
async def refresh_user_agent_cache(
    user_email: str,
    service: MultiAgentService = Depends(get_service)
):
    """
    Refresh the cached SQL agent for a specific user
    
    Useful when database schema changes or user permissions are updated.
    """
    try:
        success = service.refresh_user_agents(user_email)
        
        return {
            "success": success,
            "message": f"Agent cache refreshed for user: {user_email}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing agent cache: {str(e)}"
        )

@router.get("/agents/status")
async def get_agents_status(
    service: MultiAgentService = Depends(get_service)
):
    """
    Get detailed status of each individual agent
    """
    try:
        status = {}
        orchestrator = service.orchestrator
        
        for agent_name, agent in orchestrator.agents.items():
            agent_status = {
                "name": agent_name,
                "type": type(agent).__name__,
                "config_loaded": hasattr(agent, 'config'),
                "llm_client_available": hasattr(agent, 'openai_client'),
                "last_activity": "N/A"  # Could be enhanced with actual tracking
            }
            
            # Add agent-specific status
            if agent_name == "sql_agent" and hasattr(agent, 'sql_agents'):
                agent_status["cached_users"] = len(agent.sql_agents)
            
            status[agent_name] = agent_status
        
        return {
            "agents": status,
            "total_agents": len(status),
            "service_stats": {
                "active_sessions": len(service.sessions),
                "cached_results": len(service.result_cache)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting agents status: {str(e)}"
        )

# Configuration Endpoints

@router.get("/config")
async def get_multi_agent_config():
    """
    Get current multi-agent system configuration
    """
    try:
        config = get_config()
        return {
            "success": True,
            "config": config.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving configuration: {str(e)}"
        )

# Utility Endpoints

@router.post("/test")
async def test_multi_agent_system():
    """
    Test endpoint to verify multi-agent system functionality
    """
    try:
        test_service = get_multi_agent_service()
        
        # Simple health check
        health_result = await test_service.get_system_health()
        
        orchestrator_health = health_result.get("orchestrator", {})
        
        return {
            "success": True,
            "message": "Multi-agent system is operational",
            "health_summary": {
                "total_agents": orchestrator_health.get("total_agents", 0),
                "healthy_agents": len([
                    agent for agent, status in orchestrator_health.get("agents", {}).items()
                    if status.get("status") == "healthy"
                ]),
                "service_stats": health_result.get("service", {})
            },
            "timestamp": health_result.get("timestamp", datetime.now().isoformat())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Multi-agent system test failed",
            "timestamp": datetime.now().isoformat()
        }
