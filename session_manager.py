#!/usr/bin/env python3
"""
Comprehensive Session Management Service

Handles chat sessions, conversation history, and context persistence
for the SQL Agent system with memory capabilities.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from schema_migration import (
    schema_db, ChatSession, ChatHistory, ConversationContext,
    ChatSessionResponse, ChatMessageResponse, ConversationContextResponse
)

logger = logging.getLogger(__name__)

class SessionManager:
    """Comprehensive session management for chat history and context."""
    
    def __init__(self):
        self.db = schema_db
    
    # Session Management
    def create_session(self, user_email: str, session_name: Optional[str] = None) -> ChatSession:
        """Create a new chat session for a user."""
        session = self.db.get_session()
        try:
            chat_session = ChatSession(
                user_email=user_email,
                session_name=session_name or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            logger.info(f"✅ Created new session {chat_session.session_id} for {user_email}")
            return chat_session
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error creating session for {user_email}: {e}")
            raise
        finally:
            session.close()
    
    def get_or_create_active_session(self, user_email: str) -> ChatSession:
        """Get the active session for a user or create a new one."""
        session = self.db.get_session()
        try:
            # Look for active session
            active_session = session.query(ChatSession).filter(
                and_(
                    ChatSession.user_email == user_email,
                    ChatSession.is_active == True
                )
            ).order_by(desc(ChatSession.updated_at)).first()
            
            if active_session:
                return active_session
            
            # Create new session if none exists
            return self.create_session(user_email)
        finally:
            session.close()
    
    def get_user_sessions(self, user_email: str, limit: int = 50) -> List[ChatSessionResponse]:
        """Get all sessions for a user with message counts."""
        session = self.db.get_session()
        try:
            sessions = session.query(ChatSession).filter(
                ChatSession.user_email == user_email
            ).order_by(desc(ChatSession.updated_at)).limit(limit).all()
            
            result = []
            for chat_session in sessions:
                message_count = session.query(ChatHistory).filter(
                    ChatHistory.session_id == chat_session.session_id
                ).count()
                
                result.append(ChatSessionResponse(
                    session_id=str(chat_session.session_id),
                    user_email=chat_session.user_email,
                    session_name=chat_session.session_name,
                    created_at=chat_session.created_at,
                    updated_at=chat_session.updated_at,
                    is_active=chat_session.is_active,
                    message_count=message_count
                ))
            
            return result
        finally:
            session.close()
    
    def update_session_activity(self, session_id: UUID) -> None:
        """Update session's last activity timestamp."""
        session = self.db.get_session()
        try:
            chat_session = session.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            if chat_session:
                chat_session.updated_at = datetime.now(timezone.utc)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error updating session activity: {e}")
        finally:
            session.close()
    
    def deactivate_session(self, session_id: UUID) -> bool:
        """Deactivate a chat session."""
        session = self.db.get_session()
        try:
            chat_session = session.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            if chat_session:
                chat_session.is_active = False
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error deactivating session: {e}")
            return False
        finally:
            session.close()
    
    def delete_session(self, session_id: UUID) -> bool:
        """Delete a chat session completely."""
        session = self.db.get_session()
        try:
            # First delete all related data
            self.delete_session_messages(session_id)
            self.delete_session_contexts(session_id)
            
            # Then delete the session itself
            deleted_count = session.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).delete()
            
            session.commit()
            
            if deleted_count > 0:
                logger.info(f"✅ Deleted session {session_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error deleting session {session_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """Get a session by ID."""
        session = self.db.get_session()
        try:
            chat_session = session.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            return chat_session
        except Exception as e:
            logger.error(f"❌ Error getting session {session_id}: {e}")
            return None
        finally:
            session.close()
    
    # Message Management
    def add_message(
        self,
        session_id: UUID,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chart_files: Optional[List[str]] = None,
        query_results: Optional[Dict[str, Any]] = None
    ) -> ChatHistory:
        """Add a message to the chat history."""
        session = self.db.get_session()
        try:
            message = ChatHistory(
                session_id=session_id,
                message_type=message_type,
                content=content,
                message_metadata=json.dumps(metadata) if metadata else None,
                chart_files=json.dumps(chart_files) if chart_files else None,
                query_results=json.dumps(query_results) if query_results else None
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            
            # Update session activity
            self.update_session_activity(session_id)
            
            logger.info(f"✅ Added {message_type} message to session {session_id}")
            return message
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error adding message: {e}")
            raise
        finally:
            session.close()
    
    def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 100,
        message_types: Optional[List[str]] = None
    ) -> List[ChatMessageResponse]:
        """Get messages for a session."""
        session = self.db.get_session()
        try:
            query = session.query(ChatHistory).filter(
                ChatHistory.session_id == session_id
            )
            
            if message_types:
                query = query.filter(ChatHistory.message_type.in_(message_types))
            
            messages = query.order_by(ChatHistory.timestamp).limit(limit).all()
            
            return [
                ChatMessageResponse(
                    id=str(msg.id),
                    session_id=str(msg.session_id),
                    message_type=msg.message_type,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    message_metadata=msg.message_metadata,
                    chart_files=msg.chart_files,
                    query_results=msg.query_results
                )
                for msg in messages
            ]
        finally:
            session.close()
    
    def get_recent_messages(
        self,
        user_email: str,
        hours: int = 24,
        limit: int = 50
    ) -> List[ChatMessageResponse]:
        """Get recent messages across all user sessions."""
        session = self.db.get_session()
        try:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            messages = session.query(ChatHistory).join(ChatSession).filter(
                and_(
                    ChatSession.user_email == user_email,
                    ChatHistory.timestamp >= since
                )
            ).order_by(desc(ChatHistory.timestamp)).limit(limit).all()
            
            return [
                ChatMessageResponse(
                    id=str(msg.id),
                    session_id=str(msg.session_id),
                    message_type=msg.message_type,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    message_metadata=msg.message_metadata,
                    chart_files=msg.chart_files,
                    query_results=msg.query_results
                )
                for msg in messages
            ]
        finally:
            session.close()
    
    def delete_session_messages(self, session_id: UUID) -> int:
        """Delete all messages for a session."""
        session = self.db.get_session()
        try:
            deleted_count = session.query(ChatHistory).filter(
                ChatHistory.session_id == session_id
            ).delete()
            session.commit()
            logger.info(f"✅ Deleted {deleted_count} messages for session {session_id}")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error deleting messages for session {session_id}: {e}")
            return 0
        finally:
            session.close()
    
    # Context Management
    def set_context(
        self,
        session_id: UUID,
        context_type: str,
        context_key: str,
        context_value: Any,
        expires_hours: Optional[int] = None
    ) -> ConversationContext:
        """Set or update conversation context."""
        session = self.db.get_session()
        try:
            expires_at = None
            if expires_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            
            # Check if context already exists
            existing_context = session.query(ConversationContext).filter(
                and_(
                    ConversationContext.session_id == session_id,
                    ConversationContext.context_type == context_type,
                    ConversationContext.context_key == context_key
                )
            ).first()
            
            if existing_context:
                # Update existing context
                existing_context.context_value = json.dumps(context_value) if not isinstance(context_value, str) else context_value
                existing_context.expires_at = expires_at
                context = existing_context
            else:
                # Create new context
                context = ConversationContext(
                    session_id=session_id,
                    context_type=context_type,
                    context_key=context_key,
                    context_value=json.dumps(context_value) if not isinstance(context_value, str) else context_value,
                    expires_at=expires_at
                )
                session.add(context)
            
            session.commit()
            session.refresh(context)
            logger.info(f"✅ Set context {context_type}.{context_key} for session {session_id}")
            return context
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error setting context: {e}")
            raise
        finally:
            session.close()
    
    def get_context(
        self,
        session_id: UUID,
        context_type: Optional[str] = None,
        context_key: Optional[str] = None
    ) -> List[ConversationContextResponse]:
        """Get conversation context."""
        session = self.db.get_session()
        try:
            query = session.query(ConversationContext).filter(
                ConversationContext.session_id == session_id
            )
            
            # Filter expired contexts
            now = datetime.now(timezone.utc)
            query = query.filter(
                or_(
                    ConversationContext.expires_at.is_(None),
                    ConversationContext.expires_at > now
                )
            )
            
            if context_type:
                query = query.filter(ConversationContext.context_type == context_type)
            
            if context_key:
                query = query.filter(ConversationContext.context_key == context_key)
            
            contexts = query.order_by(desc(ConversationContext.created_at)).all()
            
            return [
                ConversationContextResponse(
                    id=str(ctx.id),
                    session_id=str(ctx.session_id),
                    context_type=ctx.context_type,
                    context_key=ctx.context_key,
                    context_value=ctx.context_value,
                    created_at=ctx.created_at,
                    expires_at=ctx.expires_at
                )
                for ctx in contexts
            ]
        finally:
            session.close()
    
    def get_context_value(
        self,
        session_id: UUID,
        context_type: str,
        context_key: str,
        default: Any = None
    ) -> Any:
        """Get a specific context value with JSON parsing."""
        contexts = self.get_context(session_id, context_type, context_key)
        if contexts:
            try:
                return json.loads(contexts[0].context_value)
            except json.JSONDecodeError:
                return contexts[0].context_value
        return default
    
    def clear_expired_contexts(self) -> int:
        """Clear expired conversation contexts."""
        session = self.db.get_session()
        try:
            now = datetime.now(timezone.utc)
            deleted = session.query(ConversationContext).filter(
                and_(
                    ConversationContext.expires_at.isnot(None),
                    ConversationContext.expires_at <= now
                )
            ).delete()
            session.commit()
            logger.info(f"✅ Cleared {deleted} expired contexts")
            return deleted
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error clearing expired contexts: {e}")
            return 0
        finally:
            session.close()
    
    def delete_session_contexts(self, session_id: UUID) -> int:
        """Delete all contexts for a session."""
        session = self.db.get_session()
        try:
            deleted_count = session.query(ConversationContext).filter(
                ConversationContext.session_id == session_id
            ).delete()
            session.commit()
            logger.info(f"✅ Deleted {deleted_count} contexts for session {session_id}")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error deleting contexts for session {session_id}: {e}")
            return 0
        finally:
            session.close()
    
    # Memory and Context Helpers
    def get_conversation_summary(self, session_id: UUID, last_n_messages: int = 10) -> str:
        """Generate a conversation summary for agent context."""
        messages = self.get_session_messages(session_id, limit=last_n_messages)
        
        if not messages:
            return "No previous conversation history."
        
        summary_parts = []
        for msg in messages[-last_n_messages:]:
            role = "User" if msg.message_type == "human" else "Assistant"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)
    
    def get_user_preferences(self, user_email: str) -> Dict[str, Any]:
        """Get user preferences across all sessions."""
        session = self.db.get_session()
        try:
            # Get the most recent active session
            active_session = self.get_or_create_active_session(user_email)
            
            # Get user preference contexts
            preferences = self.get_context(
                active_session.session_id,
                context_type="user_preference"
            )
            
            result = {}
            for pref in preferences:
                try:
                    result[pref.context_key] = json.loads(pref.context_value)
                except json.JSONDecodeError:
                    result[pref.context_key] = pref.context_value
            
            return result
        finally:
            session.close()
    
    def set_user_preference(
        self,
        user_email: str,
        preference_key: str,
        preference_value: Any
    ) -> None:
        """Set a user preference."""
        active_session = self.get_or_create_active_session(user_email)
        self.set_context(
            active_session.session_id,
            "user_preference",
            preference_key,
            preference_value
        )

# Global session manager instance
session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return session_manager
