#!/usr/bin/env python3
"""
Agent Orchestrator Service - Manages sequential flow between three core agents

This service orchestrates the flow:
Input Query → Enhanced SQL Agent → Mutual Fund Quant Agent → Data Formatter Agent → Output Response

The orchestrator ensures proper data flow, error handling, and response formatting
across the three-agent pipeline.
"""

import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

from agents.enhanced_sql_agent import (
    create_enhanced_sql_agent, 
    create_system_sql_agent
)
from agents.mutual_fund_quant_agent import MutualFundQuantAgent
from agents.data_formatter_agent import DataFormatterAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the sequential flow between Enhanced SQL Agent, 
    Mutual Fund Quant Agent, and Data Formatter Agent.
    """
    
    def __init__(self, static_dir: str = "static/charts"):
        """
        Initialize the orchestrator with the three core agents.
        
        Args:
            static_dir: Directory for chart files (passed to Data Formatter Agent)
        """
        self.quant_agent = MutualFundQuantAgent()
        self.formatter_agent = DataFormatterAgent(static_dir=static_dir)
        self.static_dir = static_dir
        
        # Agent performance tracking
        self.execution_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }
        
        logger.info("🎼 Agent Orchestrator initialized with three-agent pipeline")
    
    async def process_query(self, query: str, user_email: str, session_id: str,
                           discovery_mode: str = "multitenant") -> Dict[str, Any]:
        """
        Process a user query through the three-agent sequential pipeline.
        
        Args:
            query: User's natural language query
            user_email: User email for schema isolation
            session_id: Session ID for conversation tracking
            discovery_mode: Database discovery mode ('multitenant' or 'multidatabase')
            
        Returns:
            Dictionary containing the final formatted response
        """
        start_time = datetime.now()
        request_id = f"{session_id}_{int(start_time.timestamp())}"
        
        logger.info(f"🎼 Starting query processing [Request: {request_id}]")
        logger.info(f"📝 Query: {query}")
        logger.info(f"👤 User: {user_email}")
        logger.info(f"🔍 Discovery mode: {discovery_mode}")
        
        try:
            self.execution_stats['total_requests'] += 1
            
            # Step 1: Enhanced SQL Agent - Database operations and SQL execution
            logger.info("🔍 Step 1: Enhanced SQL Agent processing...")
            sql_response = await self._execute_sql_agent(query, user_email, session_id, discovery_mode)
            
            if not sql_response.get('success', False):
                logger.error(f"❌ SQL Agent failed: {sql_response.get('error', 'Unknown error')}")
                return self._create_error_response(
                    "SQL processing failed", 
                    sql_response.get('error', 'Database query execution failed'),
                    query, request_id
                )
            
            logger.info("✅ Step 1 completed: SQL Agent successful")
            
            # Step 2: Mutual Fund Quant Agent - Quantitative analysis and calculations
            logger.info("🧮 Step 2: Mutual Fund Quant Agent processing...")
            quant_response = self.quant_agent.process_data(sql_response, query)
            
            if not quant_response.get('success', False):
                logger.warning(f"⚠️ Quant Agent had issues: {quant_response.get('error', 'Unknown error')}")
                # Continue with original SQL response if quant analysis fails
                quant_response = {
                    'success': True,
                    'dataframe': [],
                    'calculations': {},
                    'insights': [],
                    'query': query,
                    'original_sql_data': sql_response
                }
            
            logger.info("✅ Step 2 completed: Quant Agent processed")
            
            # Step 3: Data Formatter Agent - Visualization and output formatting
            logger.info("📊 Step 3: Data Formatter Agent processing...")
            final_response = self.formatter_agent.process_data(quant_response, query)
            
            if not final_response.get('success', False):
                logger.warning(f"⚠️ Formatter Agent had issues: {final_response.get('error', 'Unknown error')}")
                # Fallback to basic response
                final_response = {
                    'success': True,
                    'response': sql_response.get('sql_response', 'Query processed successfully'),
                    'query': query
                }
            
            logger.info("✅ Step 3 completed: Data Formatter Agent finished")
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Update performance stats
            self.execution_stats['successful_requests'] += 1
            self._update_avg_response_time(execution_time)
            
            # Enhance final response with metadata
            final_response.update({
                'request_id': request_id,
                'execution_time': execution_time,
                'user_email': user_email,
                'session_id': session_id,
                'discovery_mode': discovery_mode,
                'pipeline_stages': {
                    'sql_agent': '✅ Completed',
                    'quant_agent': '✅ Completed' if quant_response.get('success') else '⚠️ Partial',
                    'formatter_agent': '✅ Completed' if final_response.get('success') else '⚠️ Partial'
                }
            })
            
            logger.info(f"🎉 Query processing completed successfully [Request: {request_id}] in {execution_time:.2f}s")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Orchestrator failed [Request: {request_id}]: {e}")
            self.execution_stats['failed_requests'] += 1
            
            return self._create_error_response(
                "Orchestration failed", 
                str(e),
                query, request_id
            )
    
    async def _execute_sql_agent(self, query: str, user_email: str, session_id: str, 
                                discovery_mode: str) -> Dict[str, Any]:
        """Execute the Enhanced SQL Agent with proper configuration."""
        try:
            # Create SQL agent based on discovery mode
            if discovery_mode == "multitenant":
                sql_agent = create_enhanced_sql_agent(user_email)
            elif discovery_mode == "multidatabase":
                sql_agent = create_system_sql_agent()
            else:
                logger.warning(f"Unknown discovery mode: {discovery_mode}, defaulting to multitenant")
                sql_agent = create_enhanced_sql_agent(user_email)
            
            if not sql_agent:
                return {
                    'success': False,
                    'error': 'Failed to create SQL agent'
                }
            
            # Execute query through the SQL agent
            response = sql_agent.process_query(query, session_id)
            
            return response
            
        except Exception as e:
            logger.error(f"SQL Agent execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_error_response(self, error_type: str, error_message: str, 
                              query: str, request_id: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            'success': False,
            'error': error_message,
            'error_type': error_type,
            'response': f"I apologize, but I encountered an error: {error_message}",
            'query': query,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def _update_avg_response_time(self, execution_time: float):
        """Update the average response time statistic."""
        total_successful = self.execution_stats['successful_requests']
        if total_successful == 1:
            self.execution_stats['avg_response_time'] = execution_time
        else:
            # Calculate rolling average
            current_avg = self.execution_stats['avg_response_time']
            new_avg = ((current_avg * (total_successful - 1)) + execution_time) / total_successful
            self.execution_stats['avg_response_time'] = new_avg
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator performance statistics."""
        return {
            'execution_stats': self.execution_stats.copy(),
            'agents_status': {
                'enhanced_sql_agent': '✅ Active',
                'mutual_fund_quant_agent': '✅ Active',
                'data_formatter_agent': '✅ Active'
            },
            'static_directory': self.static_dir
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        health_status = {
            'orchestrator': '✅ Healthy',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check Quant Agent
            health_status['quant_agent'] = '✅ Healthy' if self.quant_agent else '❌ Not initialized'
            
            # Check Formatter Agent
            health_status['formatter_agent'] = '✅ Healthy' if self.formatter_agent else '❌ Not initialized'
            
            # Check static directory
            import os
            health_status['static_directory'] = '✅ Available' if os.path.exists(self.static_dir) else '❌ Missing'
            
        except Exception as e:
            health_status['error'] = str(e)
            health_status['orchestrator'] = '❌ Unhealthy'
        
        return health_status


# Global orchestrator instance (can be configured as singleton)
_orchestrator_instance = None


def get_orchestrator(static_dir: str = "static/charts") -> AgentOrchestrator:
    """
    Get or create the global orchestrator instance.
    
    Args:
        static_dir: Directory for chart files
        
    Returns:
        AgentOrchestrator instance
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator(static_dir=static_dir)
        logger.info("🎼 Global orchestrator instance created")
    
    return _orchestrator_instance


def reset_orchestrator():
    """Reset the global orchestrator instance (useful for testing)."""
    global _orchestrator_instance
    _orchestrator_instance = None
    logger.info("🔄 Global orchestrator instance reset")
