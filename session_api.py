#!/usr/bin/env python3
"""
Session Management API Endpoints

Provides REST API endpoints for chat session management, 
conversation history, and context persistence.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from session_manager import session_manager, SessionManager
from schema_migration import ChatSessionResponse, ChatMessageResponse, ConversationContextResponse

logger = logging.getLogger(__name__)

# Request/Response Models
class CreateSessionRequest(BaseModel):
    user_email: str = Field(..., description="User email address")
    session_name: Optional[str] = Field(None, description="Optional session name")

class AddMessageRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID")
    message_type: str = Field(..., description="Message type: human, ai, system")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    chart_files: Optional[List[str]] = Field(None, description="Chart file names")
    query_results: Optional[Dict[str, Any]] = Field(None, description="SQL query results")

class SetContextRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID")
    context_type: str = Field(..., description="Context type")
    context_key: str = Field(..., description="Context key")
    context_value: Any = Field(..., description="Context value")
    expires_hours: Optional[int] = Field(None, description="Expiration in hours")

class SessionSummaryResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    total_messages: int
    recent_activity: List[ChatMessageResponse]

# Create router
router = APIRouter(prefix="/api/sessions", tags=["Session Management"])

def get_session_manager() -> SessionManager:
    """Dependency to get session manager."""
    return session_manager

@router.post("/create", response_model=ChatSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    sm: SessionManager = Depends(get_session_manager)
):
    """Create a new chat session."""
    try:
        session = sm.create_session(request.user_email, request.session_name)
        return ChatSessionResponse(
            session_id=str(session.session_id),
            user_email=session.user_email,
            session_name=session.session_name,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=0
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_email}", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    user_email: str,
    limit: int = Query(50, ge=1, le=200),
    sm: SessionManager = Depends(get_session_manager)
):
    """Get all sessions for a user."""
    try:
        return sm.get_user_sessions(user_email, limit)
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active/{user_email}", response_model=ChatSessionResponse)
async def get_or_create_active_session(
    user_email: str,
    sm: SessionManager = Depends(get_session_manager)
):
    """Get or create active session for a user."""
    try:
        session = sm.get_or_create_active_session(user_email)
        
        # Get message count
        messages = sm.get_session_messages(session.session_id, limit=1000)
        
        return ChatSessionResponse(
            session_id=str(session.session_id),
            user_email=session.user_email,
            session_name=session.session_name,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=len(messages)
        )
    except Exception as e:
        logger.error(f"Error getting active session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deactivate/{session_id}")
async def deactivate_session(
    session_id: str,
    sm: SessionManager = Depends(get_session_manager)
):
    """Deactivate a chat session."""
    try:
        session_uuid = UUID(session_id)
        success = sm.deactivate_session(session_uuid)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deactivated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error deactivating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/add", response_model=ChatMessageResponse)
async def add_message(
    request: AddMessageRequest,
    sm: SessionManager = Depends(get_session_manager)
):
    """Add a message to chat history."""
    try:
        session_uuid = UUID(request.session_id)
        message = sm.add_message(
            session_uuid,
            request.message_type,
            request.content,
            request.metadata,
            request.chart_files,
            request.query_results
        )
        return ChatMessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            message_type=message.message_type,
            content=message.content,
            timestamp=message.timestamp,
            message_metadata=message.message_metadata,
            chart_files=message.chart_files,
            query_results=message.query_results
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{session_id}", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000),
    message_types: Optional[str] = Query(None, description="Comma-separated message types"),
    sm: SessionManager = Depends(get_session_manager)
):
    """Get messages for a session."""
    try:
        session_uuid = UUID(session_id)
        types_list = message_types.split(',') if message_types else None
        return sm.get_session_messages(session_uuid, limit, types_list)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/recent/{user_email}", response_model=List[ChatMessageResponse])
async def get_recent_messages(
    user_email: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=200),
    sm: SessionManager = Depends(get_session_manager)
):
    """Get recent messages across all user sessions."""
    try:
        return sm.get_recent_messages(user_email, hours, limit)
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/context/set", response_model=ConversationContextResponse)
async def set_context(
    request: SetContextRequest,
    sm: SessionManager = Depends(get_session_manager)
):
    """Set conversation context."""
    try:
        session_uuid = UUID(request.session_id)
        context = sm.set_context(
            session_uuid,
            request.context_type,
            request.context_key,
            request.context_value,
            request.expires_hours
        )
        return ConversationContextResponse(
            id=str(context.id),
            session_id=str(context.session_id),
            context_type=context.context_type,
            context_key=context.context_key,
            context_value=context.context_value,
            created_at=context.created_at,
            expires_at=context.expires_at
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error setting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/{session_id}", response_model=List[ConversationContextResponse])
async def get_context(
    session_id: str,
    context_type: Optional[str] = Query(None),
    context_key: Optional[str] = Query(None),
    sm: SessionManager = Depends(get_session_manager)
):
    """Get conversation context."""
    try:
        session_uuid = UUID(session_id)
        return sm.get_context(session_uuid, context_type, context_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{user_email}", response_model=SessionSummaryResponse)
async def get_session_summary(
    user_email: str,
    sm: SessionManager = Depends(get_session_manager)
):
    """Get session summary for a user."""
    try:
        sessions = sm.get_user_sessions(user_email, limit=1000)
        recent_messages = sm.get_recent_messages(user_email, hours=24, limit=10)
        
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.is_active])
        total_messages = sum(s.message_count or 0 for s in sessions)
        
        return SessionSummaryResponse(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            total_messages=total_messages,
            recent_activity=recent_messages
        )
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation-summary/{session_id}")
async def get_conversation_summary(
    session_id: str,
    last_n_messages: int = Query(10, ge=1, le=50),
    sm: SessionManager = Depends(get_session_manager)
):
    """Get conversation summary for agent context."""
    try:
        session_uuid = UUID(session_id)
        summary = sm.get_conversation_summary(session_uuid, last_n_messages)
        return {"summary": summary}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/{user_email}")
async def get_user_preferences(
    user_email: str,
    sm: SessionManager = Depends(get_session_manager)
):
    """Get user preferences."""
    try:
        preferences = sm.get_user_preferences(user_email)
        return {"preferences": preferences}
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preferences/{user_email}")
async def set_user_preference(
    user_email: str,
    preference_key: str,
    preference_value: Any,
    sm: SessionManager = Depends(get_session_manager)
):
    """Set user preference."""
    try:
        sm.set_user_preference(user_email, preference_key, preference_value)
        return {"message": "Preference set successfully"}
    except Exception as e:
        logger.error(f"Error setting user preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/context/expired")
async def clear_expired_contexts(
    sm: SessionManager = Depends(get_session_manager)
):
    """Clear expired conversation contexts."""
    try:
        deleted_count = sm.clear_expired_contexts()
        return {"message": f"Cleared {deleted_count} expired contexts"}
    except Exception as e:
        logger.error(f"Error clearing expired contexts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
