#!/usr/bin/env python3
"""
A2A Service Layer - High-level service for A2A protocol orchestration

This service provides a clean interface for the API layer to interact with
the A2A orchestrator, handling session management, error recovery, and
response formatting.

Features:
- Clean API for A2A orchestration
- Session and context management
- Error handling and recovery
- Performance monitoring
- PDF report serving
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import os

from agents.a2a_orchestrator import A2AOrchestrator
from agents.a2a_protocol import QueryAnalyzer, get_a2a_protocol

logger = logging.getLogger(__name__)


class A2AService:
    """
    High-level service for A2A protocol orchestration.
    
    Provides a clean interface for API endpoints to interact with
    the A2A orchestrator while handling session management and
    error recovery.
    """
    
    def __init__(self, static_dir: str = "static/charts"):
        """
        Initialize the A2A service.
        
        Args:
            static_dir: Directory for static files (charts, reports)
        """
        self.static_dir = static_dir
        self.orchestrators: Dict[str, A2AOrchestrator] = {}
        self.protocol = get_a2a_protocol()
        
        # Service metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'active_sessions': 0
        }
        
        logger.info("A2A Service initialized")
    
    def get_orchestrator(self, user_email: str) -> A2AOrchestrator:
        """
        Get or create an orchestrator for a specific user.
        
        Args:
            user_email: User's email for schema-per-tenant architecture
            
        Returns:
            A2AOrchestrator instance for the user
        """
        if user_email not in self.orchestrators:
            self.orchestrators[user_email] = A2AOrchestrator(
                user_email=user_email,
                static_dir=self.static_dir
            )
            self.metrics['active_sessions'] += 1
            logger.info(f"Created new A2A orchestrator for user: {user_email}")
        
        return self.orchestrators[user_email]
    
    async def process_query(self, query: str, user_email: str = "anonymous@example.com",
                          session_id: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query through the A2A protocol.
        
        Args:
            query: User's natural language query
            user_email: User's email for schema isolation
            session_id: Optional session ID for context
            context: Optional additional context
            
        Returns:
            Comprehensive response with data, analysis, and visualizations
        """
        start_time = datetime.now()
        self.metrics['total_requests'] += 1
        
        try:
            # Get orchestrator for user
            orchestrator = self.get_orchestrator(user_email)
            
            # Process query through A2A orchestrator
            result = await orchestrator.process_query(
                query=query,
                session_id=session_id,
                context=context
            )
            
            # Update metrics
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            self._update_metrics(response_time, result.get('success', True))
            
            # Add service metadata
            result['service_metadata'] = {
                'response_time': response_time,
                'user_email': user_email,
                'session_id': session_id,
                'service_version': '1.0.0',
                'timestamp': end_time.isoformat()
            }
            
            logger.info(f"Query processed successfully in {response_time:.2f}s for user: {user_email}")
            return result
            
        except Exception as e:
            logger.error(f"A2A service query processing failed: {str(e)}")
            
            # Update error metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(response_time, False)
            
            return {
                'success': False,
                'error': str(e),
                'response': f"I apologize, but I encountered an error while processing your query: {str(e)}",
                'service_metadata': {
                    'response_time': response_time,
                    'user_email': user_email,
                    'session_id': session_id,
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def analyze_query_capabilities(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query to determine what capabilities will be needed.
        
        Args:
            query: User's natural language query
            
        Returns:
            Query analysis results
        """
        try:
            analysis = QueryAnalyzer.analyze_query(query)
            
            return {
                'success': True,
                'analysis': {
                    'requires_database': analysis.requires_database,
                    'requires_analysis': analysis.requires_analysis,
                    'requires_visualization': analysis.requires_visualization,
                    'requires_pdf_export': analysis.requires_pdf_export,
                    'query_type': analysis.query_type,
                    'complexity_score': analysis.complexity_score,
                    'keywords': analysis.keywords,
                    'entities': analysis.entities
                },
                'estimated_agents': self._estimate_agents_needed(analysis),
                'estimated_time': self._estimate_processing_time(analysis)
            }
            
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _estimate_agents_needed(self, analysis) -> List[str]:
        """Estimate which agents will be needed based on analysis."""
        agents = ['enhanced_sql']  # Always need SQL agent
        
        if analysis.requires_analysis:
            agents.append('mutual_fund_quant')
        
        if analysis.requires_visualization or analysis.requires_pdf_export:
            agents.append('data_formatter')
        
        return agents
    
    def _estimate_processing_time(self, analysis) -> float:
        """Estimate processing time based on query complexity."""
        base_time = 2.0  # Base SQL processing time
        
        if analysis.requires_analysis:
            base_time += 3.0  # Quant analysis time
        
        if analysis.requires_visualization:
            base_time += 2.0  # Chart generation time
        
        if analysis.requires_pdf_export:
            base_time += 5.0  # PDF generation time
        
        # Adjust for complexity
        complexity_multiplier = 1.0 + (analysis.complexity_score * 0.5)
        
        return base_time * complexity_multiplier
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the A2A service.
        
        Returns:
            Health status information
        """
        try:
            # Get protocol metrics
            protocol_metrics = self.protocol.get_performance_metrics()
            
            # Get orchestrator health for active sessions
            orchestrator_health = {}
            for user_email, orchestrator in self.orchestrators.items():
                orchestrator_health[user_email] = orchestrator.get_health_status()
            
            return {
                'service_status': 'healthy',
                'service_metrics': self.metrics,
                'protocol_metrics': protocol_metrics,
                'active_orchestrators': len(self.orchestrators),
                'orchestrator_health': orchestrator_health,
                'static_dir': self.static_dir,
                'static_dir_exists': os.path.exists(self.static_dir),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'service_status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_service_capabilities(self) -> Dict[str, Any]:
        """
        Get available service capabilities.
        
        Returns:
            Service capabilities information
        """
        return {
            'supported_operations': {
                'database_queries': True,
                'financial_analysis': True,
                'quantitative_reasoning': True,
                'data_visualization': True,
                'pdf_reports': True,
                'conditional_agent_invocation': True,
                'a2a_protocol_communication': True
            },
            'supported_query_types': [
                'mutual_fund', 'portfolio', 'equity', 'debt', 'general'
            ],
            'supported_chart_types': [
                'bar', 'line', 'pie', 'scatter', 'table'
            ],
            'supported_export_formats': [
                'json', 'html', 'pdf', 'text'
            ],
            'agent_capabilities': {
                'enhanced_sql': ['database_query', 'schema_discovery'],
                'mutual_fund_quant': ['financial_analysis', 'quantitative_reasoning', 'react_framework'],
                'data_formatter': ['data_visualization', 'report_generation', 'pdf_export']
            },
            'a2a_protocol_features': {
                'message_passing': True,
                'conditional_invocation': True,
                'context_preservation': True,
                'error_recovery': True,
                'performance_monitoring': True
            }
        }
    
    def cleanup_inactive_sessions(self, hours: int = 24) -> Dict[str, Any]:
        """
        Clean up inactive orchestrator sessions.
        
        Args:
            hours: Hours of inactivity before cleanup
            
        Returns:
            Cleanup results
        """
        try:
            initial_count = len(self.orchestrators)
            
            # For now, we'll implement a simple cleanup
            # In a production system, you'd track last activity timestamps
            
            # Clean up protocol message history
            cleaned_messages = self.protocol.cleanup_old_messages(hours)
            
            logger.info(f"Cleaned up {cleaned_messages} old protocol messages")
            
            return {
                'success': True,
                'orchestrators_before': initial_count,
                'orchestrators_after': len(self.orchestrators),
                'messages_cleaned': cleaned_messages,
                'cleanup_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_metrics(self, response_time: float, success: bool):
        """Update service metrics."""
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
        
        # Update average response time
        total_successful = self.metrics['successful_requests']
        if total_successful > 0:
            current_avg = self.metrics['avg_response_time']
            self.metrics['avg_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
    
    def get_pdf_file_path(self, filename: str) -> Optional[str]:
        """
        Get the full path to a PDF file.
        
        Args:
            filename: PDF filename
            
        Returns:
            Full file path if exists, None otherwise
        """
        reports_dir = os.path.join(self.static_dir, "reports")
        if not os.path.exists(reports_dir):
            reports_dir = self.static_dir
        
        file_path = os.path.join(reports_dir, filename)
        
        if os.path.exists(file_path):
            return file_path
        
        return None
    
    def list_available_reports(self, user_email: str) -> List[Dict[str, Any]]:
        """
        List available PDF reports for a user.
        
        Args:
            user_email: User's email
            
        Returns:
            List of available reports
        """
        try:
            reports_dir = os.path.join(self.static_dir, "reports")
            if not os.path.exists(reports_dir):
                reports_dir = self.static_dir
            
            reports = []
            
            if os.path.exists(reports_dir):
                for filename in os.listdir(reports_dir):
                    if filename.endswith('.pdf') or filename.endswith('.txt'):
                        file_path = os.path.join(reports_dir, filename)
                        file_stat = os.stat(file_path)
                        
                        reports.append({
                            'filename': filename,
                            'size': file_stat.st_size,
                            'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'type': 'pdf' if filename.endswith('.pdf') else 'text'
                        })
            
            # Sort by creation time (newest first)
            reports.sort(key=lambda x: x['created'], reverse=True)
            
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports: {str(e)}")
            return []


# Global service instance
a2a_service = A2AService()


def get_a2a_service() -> A2AService:
    """Get the global A2A service instance."""
    return a2a_service
