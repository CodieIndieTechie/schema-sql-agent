#!/usr/bin/env python3
"""
PostgreSQL-backed Chat History for LangChain

Custom chat history implementation that stores conversation history in PostgreSQL
instead of in-memory storage. Integrates with the schema-per-tenant architecture.
"""

import json
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from schema_migration import schema_db, ChatHistory

logger = logging.getLogger(__name__)

class PostgreSQLChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history stored in PostgreSQL database.
    
    This class implements LangChain's BaseChatMessageHistory interface
    and stores conversation history in the public.chat_history table.
    """
    
    def __init__(self, session_id: str, max_messages: int = 100):
        """
        Initialize PostgreSQL chat history.
        
        Args:
            session_id: Unique identifier for the chat session (usually user email)
            max_messages: Maximum number of messages to keep in history
        """
        self.session_id = session_id
        self.max_messages = max_messages
        self._messages: List[BaseMessage] = []
        self._loaded = False
        
    def _ensure_loaded(self):
        """Lazy load messages from database when first accessed."""
        if not self._loaded:
            self._load_messages_from_db()
            self._loaded = True
    
    def _load_messages_from_db(self):
        """Load messages from PostgreSQL database."""
        try:
            session = schema_db.get_session()
            
            # Query chat history for this session, ordered by timestamp
            chat_records = (
                session.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .order_by(ChatHistory.timestamp)
                .limit(self.max_messages)
                .all()
            )
            
            # Convert database records to LangChain messages
            self._messages = []
            for record in chat_records:
                message = self._db_record_to_message(record)
                if message:
                    self._messages.append(message)
            
            session.close()
            logger.debug(f"Loaded {len(self._messages)} messages for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error loading chat history for session {self.session_id}: {e}")
            self._messages = []
    
    def _db_record_to_message(self, record: ChatHistory) -> Optional[BaseMessage]:
        """Convert database record to LangChain message."""
        try:
            # Parse metadata if it exists
            metadata = {}
            if record.message_metadata:
                try:
                    metadata = json.loads(record.message_metadata)
                except json.JSONDecodeError:
                    pass
            
            # Create appropriate message type
            if record.message_type == 'human':
                return HumanMessage(content=record.content, additional_kwargs=metadata)
            elif record.message_type == 'ai':
                return AIMessage(content=record.content, additional_kwargs=metadata)
            elif record.message_type == 'system':
                return SystemMessage(content=record.content, additional_kwargs=metadata)
            else:
                logger.warning(f"Unknown message type: {record.message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting DB record to message: {e}")
            return None
    
    def _message_to_db_record(self, message: BaseMessage) -> ChatHistory:
        """Convert LangChain message to database record."""
        # Determine message type
        if isinstance(message, HumanMessage):
            message_type = 'human'
        elif isinstance(message, AIMessage):
            message_type = 'ai'
        elif isinstance(message, SystemMessage):
            message_type = 'system'
        else:
            message_type = 'unknown'
        
        # Serialize additional metadata
        message_metadata = json.dumps(getattr(message, 'additional_kwargs', {})) if hasattr(message, 'additional_kwargs') else None
        
        return ChatHistory(
            session_id=self.session_id,
            message_type=message_type,
            content=message.content,
            message_metadata=message_metadata,
            timestamp=datetime.now(timezone.utc)
        )
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Return the messages in the store."""
        self._ensure_loaded()
        return self._messages.copy()
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the store and persist to database."""
        try:
            # Add to in-memory cache
            self._ensure_loaded()
            self._messages.append(message)
            
            # Persist to database
            session = schema_db.get_session()
            db_record = self._message_to_db_record(message)
            session.add(db_record)
            session.commit()
            session.close()
            
            # Trim messages if we exceed max_messages
            if len(self._messages) > self.max_messages:
                self._trim_old_messages()
            
            logger.debug(f"Added message to session {self.session_id}: {message.content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error adding message to chat history: {e}")
    
    def _trim_old_messages(self):
        """Remove oldest messages if we exceed max_messages limit."""
        if len(self._messages) <= self.max_messages:
            return
        
        try:
            # Calculate how many messages to remove
            messages_to_remove = len(self._messages) - self.max_messages
            
            # Remove from in-memory cache
            self._messages = self._messages[messages_to_remove:]
            
            # Remove from database (keep only the most recent max_messages)
            session = schema_db.get_session()
            
            # Get IDs of messages to keep
            messages_to_keep = (
                session.query(ChatHistory.id)
                .filter(ChatHistory.session_id == self.session_id)
                .order_by(desc(ChatHistory.timestamp))
                .limit(self.max_messages)
                .subquery()
            )
            
            # Delete old messages
            deleted_count = (
                session.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .filter(~ChatHistory.id.in_(messages_to_keep))
                .delete(synchronize_session=False)
            )
            
            session.commit()
            session.close()
            
            logger.info(f"Trimmed {deleted_count} old messages from session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error trimming chat history: {e}")
    
    def clear(self) -> None:
        """Clear all messages from the store and database."""
        try:
            # Clear in-memory cache
            self._messages = []
            
            # Clear from database
            session = schema_db.get_session()
            deleted_count = (
                session.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .delete()
            )
            session.commit()
            session.close()
            
            logger.info(f"Cleared {deleted_count} messages from session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the history."""
        try:
            session = schema_db.get_session()
            count = (
                session.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .count()
            )
            session.close()
            return count
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        """Get the most recent N messages."""
        try:
            session = schema_db.get_session()
            
            chat_records = (
                session.query(ChatHistory)
                .filter(ChatHistory.session_id == self.session_id)
                .order_by(desc(ChatHistory.timestamp))
                .limit(limit)
                .all()
            )
            
            # Reverse to get chronological order
            chat_records.reverse()
            
            messages = []
            for record in chat_records:
                message = self._db_record_to_message(record)
                if message:
                    messages.append(message)
            
            session.close()
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []

def get_postgresql_chat_history(session_id: str, max_messages: int = 100) -> PostgreSQLChatMessageHistory:
    """
    Factory function to create PostgreSQL chat history instances.
    
    Args:
        session_id: Unique identifier for the chat session
        max_messages: Maximum number of messages to keep in history
        
    Returns:
        PostgreSQLChatMessageHistory instance
    """
    return PostgreSQLChatMessageHistory(session_id=session_id, max_messages=max_messages)

# Utility functions for chat history management
def get_all_session_ids() -> List[str]:
    """Get all unique session IDs from chat history."""
    try:
        session = schema_db.get_session()
        session_ids = (
            session.query(ChatHistory.session_id)
            .distinct()
            .all()
        )
        session.close()
        return [sid[0] for sid in session_ids]
    except Exception as e:
        logger.error(f"Error getting session IDs: {e}")
        return []

def get_session_stats() -> Dict[str, Any]:
    """Get statistics about chat history usage."""
    try:
        session = schema_db.get_session()
        
        total_messages = session.query(ChatHistory).count()
        total_sessions = session.query(ChatHistory.session_id).distinct().count()
        
        # Get message type distribution
        message_types = (
            session.query(ChatHistory.message_type, ChatHistory.id)
            .all()
        )
        
        type_counts = {}
        for msg_type, _ in message_types:
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        session.close()
        
        return {
            'total_messages': total_messages,
            'total_sessions': total_sessions,
            'message_types': type_counts,
            'avg_messages_per_session': total_messages / max(total_sessions, 1)
        }
    except Exception as e:
        logger.error(f"Error getting chat history stats: {e}")
        return {}

def cleanup_old_chat_history(days_to_keep: int = 30):
    """
    Clean up chat history older than specified days.
    
    Args:
        days_to_keep: Number of days to keep chat history
    """
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        session = schema_db.get_session()
        deleted_count = (
            session.query(ChatHistory)
            .filter(ChatHistory.timestamp < cutoff_date)
            .delete()
        )
        session.commit()
        session.close()
        
        logger.info(f"Cleaned up {deleted_count} old chat history records")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up chat history: {e}")
        return 0

if __name__ == "__main__":
    # Test the PostgreSQL chat history
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Initialize database
    from schema_migration import initialize_schema_per_tenant_db
    initialize_schema_per_tenant_db()
    
    # Test chat history
    chat_history = get_postgresql_chat_history("test@example.com")
    
    # Add some test messages
    chat_history.add_message(HumanMessage(content="Hello, how are you?"))
    chat_history.add_message(AIMessage(content="I'm doing well, thank you! How can I help you today?"))
    chat_history.add_message(HumanMessage(content="Can you help me with SQL queries?"))
    
    # Retrieve messages
    messages = chat_history.messages
    print(f"Chat history has {len(messages)} messages:")
    for i, msg in enumerate(messages):
        print(f"{i+1}. {type(msg).__name__}: {msg.content}")
    
    # Test stats
    stats = get_session_stats()
    print(f"Chat history stats: {stats}")
