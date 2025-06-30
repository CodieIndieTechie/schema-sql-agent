"""
Multi-Agent System Service Layer

This service provides high-level business logic for the multi-agent system,
including session management, query processing, and result caching.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from agents.multi_agent_orchestrator import MultiAgentOrchestrator
from config.multi_agent_config import get_config, is_feature_enabled

logger = logging.getLogger(__name__)

@dataclass
class QuerySession:
    """Represents a query processing session"""
    session_id: str
    user_email: str
    started_at: datetime
    last_activity: datetime
    query_count: int = 0
    total_processing_time: float = 0.0
    successful_queries: int = 0
    failed_queries: int = 0

@dataclass
class QueryResult:
    """Structured result from query processing"""
    success: bool
    response: str
    session_id: str
    processing_time: float
    agents_used: List[str]
    workflow_path: List[str]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class MultiAgentService:
    """High-level service for multi-agent system operations"""
    
    def __init__(self):
        self.orchestrator = MultiAgentOrchestrator()
        self.sessions: Dict[str, QuerySession] = {}
        self.result_cache: Dict[str, QueryResult] = {}
        self.config = get_config()
        
        # Session cleanup configuration
        self.session_timeout = timedelta(hours=2)
        self.cache_timeout = timedelta(hours=1)
        self.max_sessions = 1000
        self.max_cache_size = 500
        
    async def process_query(
        self,
        query: str,
        user_email: str,
        session_id: Optional[str] = None,
        enable_caching: bool = True
    ) -> QueryResult:
        """
        Process a query through the multi-agent system with session management
        
        Args:
            query: User's natural language query
            user_email: User's email for schema isolation
            session_id: Optional session ID
            enable_caching: Whether to enable result caching
            
        Returns:
            QueryResult with structured response data
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"session_{user_email}_{int(asyncio.get_event_loop().time())}"
            
            # Check cache first
            cache_key = self._get_cache_key(query, user_email)
            if enable_caching and is_feature_enabled("agent_caching"):
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    logger.info(f"Returning cached result for query: {query[:50]}...")
                    return cached_result
            
            # Update session tracking
            session = self._get_or_create_session(session_id, user_email)
            session.query_count += 1
            session.last_activity = datetime.now()
            
            start_time = asyncio.get_event_loop().time()
            
            # Process query through orchestrator
            raw_result = await self.orchestrator.process_query(
                user_query=query,
                user_email=user_email,
                session_id=session_id
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Create structured result
            result = QueryResult(
                success=raw_result.get("success", False),
                response=raw_result.get("response", ""),
                session_id=session_id,
                processing_time=processing_time,
                agents_used=raw_result.get("metadata", {}).get("agents_used", []),
                workflow_path=raw_result.get("metadata", {}).get("workflow_path", []),
                metadata=raw_result.get("metadata", {}),
                error=raw_result.get("error")
            )
            
            # Update session statistics
            session.total_processing_time += processing_time
            if result.success:
                session.successful_queries += 1
            else:
                session.failed_queries += 1
            
            # Cache successful results
            if result.success and enable_caching and is_feature_enabled("agent_caching"):
                self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return QueryResult(
                success=False,
                response="I apologize, but I encountered an error while processing your query. Please try again.",
                session_id=session_id or "unknown",
                processing_time=0.0,
                agents_used=[],
                workflow_path=[],
                metadata={},
                error=str(e)
            )
    
    async def process_query_stream(
        self,
        query: str,
        user_email: str,
        session_id: Optional[str] = None
    ):
        """Process query with streaming updates"""
        try:
            if not session_id:
                session_id = f"session_{user_email}_{int(asyncio.get_event_loop().time())}"
            
            # Update session
            session = self._get_or_create_session(session_id, user_email)
            session.query_count += 1
            session.last_activity = datetime.now()
            
            async for update in self.orchestrator.process_query_streaming(
                user_query=query,
                user_email=user_email,
                session_id=session_id
            ):
                yield update
                
        except Exception as e:
            yield {
                "status": "error",
                "error": str(e),
                "response": "An error occurred during streaming query processing."
            }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information"""
        try:
            # Get orchestrator health
            orchestrator_health = await self.orchestrator.health_check()
            
            # Add service-level statistics
            active_sessions = len([
                s for s in self.sessions.values()
                if datetime.now() - s.last_activity < self.session_timeout
            ])
            
            total_queries = sum(s.query_count for s in self.sessions.values())
            successful_queries = sum(s.successful_queries for s in self.sessions.values())
            
            return {
                "orchestrator": orchestrator_health,
                "service": {
                    "active_sessions": active_sessions,
                    "total_sessions": len(self.sessions),
                    "cached_results": len(self.result_cache),
                    "total_queries_processed": total_queries,
                    "success_rate": (successful_queries / max(total_queries, 1)) * 100,
                    "config": self.config.to_dict()
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_email": session.user_email,
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "query_count": session.query_count,
            "successful_queries": session.successful_queries,
            "failed_queries": session.failed_queries,
            "total_processing_time": session.total_processing_time,
            "average_processing_time": session.total_processing_time / max(session.query_count, 1),
            "success_rate": (session.successful_queries / max(session.query_count, 1)) * 100
        }
    
    def get_user_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific user"""
        user_sessions = [
            session for session in self.sessions.values()
            if session.user_email == user_email
        ]
        
        return [
            {
                "session_id": session.session_id,
                "started_at": session.started_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "query_count": session.query_count,
                "success_rate": (session.successful_queries / max(session.query_count, 1)) * 100
            }
            for session in user_sessions
        ]
    
    def clear_user_cache(self, user_email: str) -> int:
        """Clear cached results for a specific user"""
        cleared_count = 0
        keys_to_remove = []
        
        for cache_key in self.result_cache.keys():
            if user_email in cache_key:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.result_cache[key]
            cleared_count += 1
        
        return cleared_count
    
    def refresh_user_agents(self, user_email: str) -> bool:
        """Refresh cached agents for a user"""
        try:
            sql_agent = self.orchestrator.agents.get("sql_agent")
            if sql_agent and hasattr(sql_agent, 'refresh_agent_cache'):
                sql_agent.refresh_agent_cache(user_email)
            
            # Clear user's result cache
            self.clear_user_cache(user_email)
            
            return True
        except Exception as e:
            logger.error(f"Error refreshing user agents: {str(e)}")
            return False
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired sessions and cached results"""
        now = datetime.now()
        
        # Clean up expired sessions
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        # Clean up expired cache entries
        expired_cache = []
        for cache_key, result in self.result_cache.items():
            # For simplicity, we'll just limit cache size rather than implement time-based expiry
            pass
        
        # Limit cache size
        if len(self.result_cache) > self.max_cache_size:
            # Remove oldest entries (simplified approach)
            sorted_keys = list(self.result_cache.keys())
            keys_to_remove = sorted_keys[:-self.max_cache_size]
            for key in keys_to_remove:
                del self.result_cache[key]
        
        return {
            "expired_sessions": len(expired_sessions),
            "cache_entries_removed": len(expired_cache),
            "active_sessions": len(self.sessions),
            "cached_results": len(self.result_cache)
        }
    
    def _get_or_create_session(self, session_id: str, user_email: str) -> QuerySession:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            # Cleanup if we're at max sessions
            if len(self.sessions) >= self.max_sessions:
                self.cleanup_expired_data()
            
            self.sessions[session_id] = QuerySession(
                session_id=session_id,
                user_email=user_email,
                started_at=datetime.now(),
                last_activity=datetime.now()
            )
        
        return self.sessions[session_id]
    
    def _get_cache_key(self, query: str, user_email: str) -> str:
        """Generate cache key for query"""
        # Simple cache key - in production you might want to hash this
        return f"{user_email}:{hash(query.lower().strip())}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[QueryResult]:
        """Get cached result if available and not expired"""
        return self.result_cache.get(cache_key)
    
    def _cache_result(self, cache_key: str, result: QueryResult):
        """Cache a query result"""
        if len(self.result_cache) >= self.max_cache_size:
            # Remove oldest entry (simplified LRU)
            oldest_key = next(iter(self.result_cache))
            del self.result_cache[oldest_key]
        
        self.result_cache[cache_key] = result

# Global service instance
_service: Optional[MultiAgentService] = None

def get_multi_agent_service() -> MultiAgentService:
    """Get the global multi-agent service instance"""
    global _service
    if _service is None:
        _service = MultiAgentService()
    return _service
