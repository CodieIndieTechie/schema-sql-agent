#!/usr/bin/env python3
"""
A2A (Agent-to-Agent) Protocol for Inter-Agentic Communication

This module implements a sophisticated communication protocol for seamless
agent-to-agent interaction with conditional invocation, data flow management,
and context preservation.

Key Features:
- Message passing with structured data formats
- Conditional agent invocation based on query analysis
- Context preservation across agent boundaries
- Error handling and recovery mechanisms
- Performance monitoring and optimization
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Enumeration of available agent types in the system."""
    ENHANCED_SQL = "enhanced_sql"
    MUTUAL_FUND_QUANT = "mutual_fund_quant"
    DATA_FORMATTER = "data_formatter"


class MessageType(Enum):
    """Types of messages that can be passed between agents."""
    QUERY_REQUEST = "query_request"
    DATA_RESPONSE = "data_response"
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    FORMAT_REQUEST = "format_request"
    FORMAT_RESPONSE = "format_response"
    ERROR = "error"
    STATUS = "status"


class AgentCapability(Enum):
    """Capabilities that agents can provide."""
    DATABASE_QUERY = "database_query"
    FINANCIAL_ANALYSIS = "financial_analysis"
    QUANTITATIVE_REASONING = "quantitative_reasoning"
    DATA_VISUALIZATION = "data_visualization"
    REPORT_GENERATION = "report_generation"
    PDF_EXPORT = "pdf_export"


@dataclass
class A2AMessage:
    """
    Standardized message format for agent-to-agent communication.
    """
    message_id: str
    sender: AgentType
    recipient: AgentType
    message_type: MessageType
    timestamp: datetime
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    parent_message_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['sender'] = self.sender.value
        result['recipient'] = self.recipient.value
        result['message_type'] = self.message_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary format."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['sender'] = AgentType(data['sender'])
        data['recipient'] = AgentType(data['recipient'])
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


@dataclass
class QueryAnalysis:
    """
    Analysis of user query to determine required agent capabilities.
    """
    requires_database: bool = False
    requires_analysis: bool = False
    requires_visualization: bool = False
    requires_pdf_export: bool = False
    query_type: str = "general"
    complexity_score: float = 0.0
    keywords: List[str] = None
    entities: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []


class QueryAnalyzer:
    """
    Analyzes user queries to determine which agents need to be invoked.
    """
    
    # Keywords that indicate different types of operations
    DATABASE_KEYWORDS = [
        'show', 'list', 'find', 'search', 'query', 'select', 'get', 'fetch',
        'tables', 'data', 'database', 'records', 'entries', 'information'
    ]
    
    ANALYSIS_KEYWORDS = [
        'analyze', 'analysis', 'compare', 'comparison', 'evaluate', 'assessment',
        'performance', 'risk', 'return', 'ratio', 'correlation', 'trend',
        'recommendation', 'advice', 'suggest', 'best', 'top', 'worst',
        'sharpe', 'sortino', 'volatility', 'drawdown', 'alpha', 'beta'
    ]
    
    VISUALIZATION_KEYWORDS = [
        'chart', 'graph', 'plot', 'visualize', 'visualization', 'draw',
        'bar chart', 'line chart', 'pie chart', 'scatter plot', 'histogram',
        'dashboard'
    ]
    
    PDF_KEYWORDS = [
        'pdf', 'download', 'export', 'save', 'document', 
        'detailed report', 'comprehensive report', 'full report', 'generate report'
    ]
    
    @staticmethod
    def analyze_query(query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine required capabilities.
        
        Args:
            query: User's natural language query
            
        Returns:
            QueryAnalysis object with capability requirements
        """
        query_lower = query.lower()
        
        # Check for database operations
        requires_database = any(keyword in query_lower for keyword in QueryAnalyzer.DATABASE_KEYWORDS)
        
        # Check for analysis requirements
        requires_analysis = any(keyword in query_lower for keyword in QueryAnalyzer.ANALYSIS_KEYWORDS)
        
        # Check for visualization requirements (be more specific to avoid false positives)
        requires_visualization = any(keyword in query_lower for keyword in QueryAnalyzer.VISUALIZATION_KEYWORDS)
        
        # Don't trigger visualization for analysis-only queries unless explicitly requested
        analysis_only_patterns = ['analyze', 'analysis', 'assess', 'evaluate', 'review']
        if (not requires_visualization and 
            any(pattern in query_lower for pattern in analysis_only_patterns) and
            not any(viz_word in query_lower for viz_word in ['chart', 'graph', 'plot', 'visualize', 'show me'])):
            requires_visualization = False
        
        # Check for PDF export requirements
        requires_pdf_export = any(keyword in query_lower for keyword in QueryAnalyzer.PDF_KEYWORDS)
        
        # Determine query type
        query_type = "general"
        if "mutual fund" in query_lower or "fund" in query_lower:
            query_type = "mutual_fund"
        elif "portfolio" in query_lower:
            query_type = "portfolio"
        elif "stock" in query_lower or "equity" in query_lower:
            query_type = "equity"
        elif "bond" in query_lower or "debt" in query_lower:
            query_type = "debt"
        
        # Calculate complexity score
        complexity_score = 0.0
        if requires_database:
            complexity_score += 0.2
        if requires_analysis:
            complexity_score += 0.4
        if requires_visualization:
            complexity_score += 0.3
        if requires_pdf_export:
            complexity_score += 0.1
        
        # Extract keywords and entities (simplified)
        keywords = [word for word in query_lower.split() if len(word) > 3]
        entities = []  # Could be enhanced with NER
        
        return QueryAnalysis(
            requires_database=requires_database,
            requires_analysis=requires_analysis,
            requires_visualization=requires_visualization,
            requires_pdf_export=requires_pdf_export,
            query_type=query_type,
            complexity_score=complexity_score,
            keywords=keywords[:10],  # Limit to top 10
            entities=entities
        )


class A2AProtocol:
    """
    Core A2A protocol implementation for managing agent communication.
    """
    
    def __init__(self):
        """Initialize the A2A protocol."""
        self.message_history: List[A2AMessage] = []
        self.agent_registry: Dict[AgentType, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, Any] = {
            'total_messages': 0,
            'successful_flows': 0,
            'failed_flows': 0,
            'avg_response_time': 0.0
        }
    
    def register_agent(self, agent_type: AgentType, capabilities: List[AgentCapability], 
                      instance: Any = None) -> None:
        """
        Register an agent with the protocol.
        
        Args:
            agent_type: Type of agent being registered
            capabilities: List of capabilities the agent provides
            instance: Optional agent instance reference
        """
        self.agent_registry[agent_type] = {
            'capabilities': capabilities,
            'instance': instance,
            'registered_at': datetime.now(),
            'message_count': 0,
            'last_active': None
        }
        logger.info(f"Registered agent {agent_type.value} with capabilities: {[c.value for c in capabilities]}")
    
    def create_message(self, sender: AgentType, recipient: AgentType, 
                      message_type: MessageType, payload: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None,
                      parent_message_id: Optional[str] = None) -> A2AMessage:
        """
        Create a new A2A message.
        
        Args:
            sender: Sending agent type
            recipient: Receiving agent type
            message_type: Type of message
            payload: Message payload data
            context: Optional context information
            parent_message_id: Optional parent message ID for threading
            
        Returns:
            A2AMessage instance
        """
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            timestamp=datetime.now(),
            payload=payload,
            context=context,
            parent_message_id=parent_message_id
        )
        
        self.message_history.append(message)
        self.performance_metrics['total_messages'] += 1
        
        # Update agent activity
        if recipient in self.agent_registry:
            self.agent_registry[recipient]['message_count'] += 1
            self.agent_registry[recipient]['last_active'] = datetime.now()
        
        logger.debug(f"Created message {message.message_id}: {sender.value} -> {recipient.value}")
        return message
    
    def get_agent_capabilities(self, agent_type: AgentType) -> List[AgentCapability]:
        """
        Get capabilities of a registered agent.
        
        Args:
            agent_type: Agent type to query
            
        Returns:
            List of agent capabilities
        """
        if agent_type in self.agent_registry:
            return self.agent_registry[agent_type]['capabilities']
        return []
    
    def is_agent_available(self, agent_type: AgentType) -> bool:
        """
        Check if an agent is available for processing.
        
        Args:
            agent_type: Agent type to check
            
        Returns:
            True if agent is available, False otherwise
        """
        return agent_type in self.agent_registry and self.agent_registry[agent_type]['instance'] is not None
    
    def get_message_thread(self, message_id: str) -> List[A2AMessage]:
        """
        Get all messages in a thread starting from a root message.
        
        Args:
            message_id: Root message ID
            
        Returns:
            List of messages in the thread
        """
        thread_messages = []
        
        # Find root message
        root_message = None
        for msg in self.message_history:
            if msg.message_id == message_id:
                root_message = msg
                break
        
        if not root_message:
            return thread_messages
        
        thread_messages.append(root_message)
        
        # Find child messages recursively
        def find_children(parent_id: str):
            children = [msg for msg in self.message_history if msg.parent_message_id == parent_id]
            for child in children:
                thread_messages.append(child)
                find_children(child.message_id)
        
        find_children(message_id)
        return thread_messages
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get protocol performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        return self.performance_metrics.copy()
    
    def cleanup_old_messages(self, hours: int = 24) -> int:
        """
        Clean up old messages from history.
        
        Args:
            hours: Number of hours to keep messages
            
        Returns:
            Number of messages cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        initial_count = len(self.message_history)
        
        self.message_history = [
            msg for msg in self.message_history 
            if msg.timestamp > cutoff_time
        ]
        
        cleaned_count = initial_count - len(self.message_history)
        logger.info(f"Cleaned up {cleaned_count} old messages")
        return cleaned_count


# Global A2A protocol instance
a2a_protocol = A2AProtocol()


def get_a2a_protocol() -> A2AProtocol:
    """Get the global A2A protocol instance."""
    return a2a_protocol
