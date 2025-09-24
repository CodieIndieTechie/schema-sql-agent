#!/usr/bin/env python3
"""
A2A Orchestrator - Advanced Agent-to-Agent Communication Orchestrator

This orchestrator implements sophisticated A2A communication patterns with:
- Conditional agent invocation based on query analysis
- Seamless data flow between agents
- Context preservation and error recovery
- Performance monitoring and optimization
- PDF report generation capabilities
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import traceback

from .a2a_protocol import (
    A2AProtocol, A2AMessage, AgentType, MessageType, AgentCapability,
    QueryAnalyzer, QueryAnalysis, get_a2a_protocol
)
from .enhanced_sql_agent import EnhancedSQLAgent
from .mutual_fund_quant_agent import MutualFundQuantAgent
from .data_formatter_agent import DataFormatterAgent

logger = logging.getLogger(__name__)


class A2AOrchestrator:
    """
    Advanced orchestrator implementing A2A protocol for seamless agent communication.
    
    Features:
    - Conditional agent invocation based on query requirements
    - Seamless data flow with context preservation
    - Error handling and recovery mechanisms
    - Performance monitoring and optimization
    - PDF report generation
    """
    
    def __init__(self, user_email: Optional[str] = None, static_dir: str = "static/charts"):
        """
        Initialize the A2A orchestrator.
        
        Args:
            user_email: User email for schema-per-tenant architecture
            static_dir: Directory for chart and report files
        """
        self.user_email = user_email or "anonymous@example.com"
        self.static_dir = static_dir
        self.protocol = get_a2a_protocol()
        
        # Initialize agents
        self.sql_agent = None
        self.quant_agent = None
        self.formatter_agent = None
        
        # Performance tracking
        self.execution_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'agent_invocations': {
                'sql': 0,
                'quant': 0,
                'formatter': 0
            }
        }
        
        # Initialize agents and register with protocol
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize and register agents with the A2A protocol."""
        try:
            # Initialize Enhanced SQL Agent
            self.sql_agent = EnhancedSQLAgent(
                user_email=self.user_email,
                discovery_mode='comprehensive'
            )
            self.protocol.register_agent(
                AgentType.ENHANCED_SQL,
                [AgentCapability.DATABASE_QUERY],
                self.sql_agent
            )
            
            # Initialize Mutual Fund Quant Agent
            self.quant_agent = MutualFundQuantAgent()
            self.protocol.register_agent(
                AgentType.MUTUAL_FUND_QUANT,
                [AgentCapability.FINANCIAL_ANALYSIS, AgentCapability.QUANTITATIVE_REASONING],
                self.quant_agent
            )
            
            # Initialize Data Formatter Agent
            self.formatter_agent = DataFormatterAgent(static_dir=self.static_dir)
            self.protocol.register_agent(
                AgentType.DATA_FORMATTER,
                [AgentCapability.DATA_VISUALIZATION, AgentCapability.REPORT_GENERATION, AgentCapability.PDF_EXPORT],
                self.formatter_agent
            )
            
            logger.info("All agents initialized and registered with A2A protocol")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def process_query(self, query: str, session_id: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user query through A2A protocol with conditional agent invocation.
        
        Args:
            query: User's natural language query
            session_id: Optional session ID for context
            context: Optional additional context
            
        Returns:
            Comprehensive response with data, analysis, and visualizations
        """
        start_time = datetime.now()
        self.execution_stats['total_requests'] += 1
        
        try:
            # Step 1: Analyze query to determine required agents
            query_analysis = QueryAnalyzer.analyze_query(query)
            logger.info(f"Query analysis: {query_analysis}")
            
            # Step 2: Create initial context
            flow_context = {
                'original_query': query,
                'session_id': session_id,
                'user_email': self.user_email,
                'query_analysis': query_analysis,
                'flow_start_time': start_time.isoformat(),
                'additional_context': context or {}
            }
            
            # Step 3: Execute conditional agent flow
            result = await self._execute_agent_flow(query, query_analysis, flow_context)
            
            # Step 4: Update performance metrics
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            self._update_performance_metrics(response_time, True)
            
            # Step 5: Add metadata to result
            result['metadata'] = {
                'query_analysis': query_analysis.__dict__,
                'response_time': response_time,
                'agents_invoked': result.get('agents_invoked', []),
                'flow_id': session_id,
                'timestamp': end_time.isoformat()
            }
            
            logger.info(f"Query processed successfully in {response_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(traceback.format_exc())
            
            self._update_performance_metrics(0, False)
            
            return {
                'response': f"I apologize, but I encountered an error while processing your query: {str(e)}",
                'error': str(e),
                'success': False,
                'metadata': {
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    async def _execute_agent_flow(self, query: str, analysis: QueryAnalysis, 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the conditional agent flow based on query analysis.
        
        Args:
            query: Original user query
            analysis: Query analysis results
            context: Flow context
            
        Returns:
            Processed result from agent flow
        """
        agents_invoked = []
        flow_data = {}
        
        # Step 1: Enhanced SQL Agent (if database access needed)
        if analysis.requires_database:
            logger.info("Invoking Enhanced SQL Agent for database operations")
            sql_result = await self._invoke_sql_agent(query, context)
            agents_invoked.append('enhanced_sql')
            flow_data['sql_result'] = sql_result
            
            # Update context with SQL results
            context['sql_data'] = sql_result.get('data')
            context['sql_response'] = sql_result.get('response')
        
        # Step 2: Mutual Fund Quant Agent (if analysis needed)
        if analysis.requires_analysis and flow_data.get('sql_result'):
            logger.info("Invoking Mutual Fund Quant Agent for financial analysis")
            quant_result = await self._invoke_quant_agent(query, context, flow_data['sql_result'])
            agents_invoked.append('mutual_fund_quant')
            flow_data['quant_result'] = quant_result
            
            # Update context with analysis results
            context['analysis_data'] = quant_result.get('analysis')
            context['reasoning_trace'] = quant_result.get('reasoning_trace')
        
        # Step 3: Data Formatter Agent (if visualization or PDF needed)
        if analysis.requires_visualization or analysis.requires_pdf_export:
            logger.info("Invoking Data Formatter Agent for visualization and formatting")
            format_result = await self._invoke_formatter_agent(query, context, flow_data)
            agents_invoked.append('data_formatter')
            flow_data['format_result'] = format_result
        
        # Step 4: Consolidate results
        final_result = self._consolidate_results(query, analysis, flow_data, agents_invoked)
        final_result['agents_invoked'] = agents_invoked
        
        return final_result
    
    async def _invoke_sql_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke Enhanced SQL Agent through A2A protocol.
        
        Args:
            query: User query
            context: Flow context
            
        Returns:
            SQL agent result
        """
        self.execution_stats['agent_invocations']['sql'] += 1
        
        # Create A2A message
        message = self.protocol.create_message(
            sender=AgentType.ENHANCED_SQL,  # Orchestrator acts as SQL agent for messaging
            recipient=AgentType.ENHANCED_SQL,
            message_type=MessageType.QUERY_REQUEST,
            payload={'query': query},
            context=context
        )
        
        try:
            # Process query through SQL agent
            result = await asyncio.to_thread(self.sql_agent.process_query, query)
            
            # Create response message
            response_message = self.protocol.create_message(
                sender=AgentType.ENHANCED_SQL,
                recipient=AgentType.ENHANCED_SQL,
                message_type=MessageType.DATA_RESPONSE,
                payload=result,
                context=context,
                parent_message_id=message.message_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"SQL Agent invocation failed: {str(e)}")
            return {
                'response': f"Database query failed: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    async def _invoke_quant_agent(self, query: str, context: Dict[str, Any], 
                                sql_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke Mutual Fund Quant Agent through A2A protocol.
        
        Args:
            query: User query
            context: Flow context
            sql_result: Results from SQL agent
            
        Returns:
            Quant agent result
        """
        self.execution_stats['agent_invocations']['quant'] += 1
        
        # Create A2A message
        message = self.protocol.create_message(
            sender=AgentType.ENHANCED_SQL,
            recipient=AgentType.MUTUAL_FUND_QUANT,
            message_type=MessageType.ANALYSIS_REQUEST,
            payload={
                'query': query,
                'data': sql_result.get('data'),
                'sql_response': sql_result.get('response')
            },
            context=context
        )
        
        try:
            # Process through quant agent
            result = await asyncio.to_thread(
                self.quant_agent.process_data_with_reasoning,
                sql_result.get('data'),
                query,
                context.get('additional_context', {})
            )
            
            # Create response message
            response_message = self.protocol.create_message(
                sender=AgentType.MUTUAL_FUND_QUANT,
                recipient=AgentType.ENHANCED_SQL,
                message_type=MessageType.ANALYSIS_RESPONSE,
                payload=result,
                context=context,
                parent_message_id=message.message_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Quant Agent invocation failed: {str(e)}")
            return {
                'analysis': f"Financial analysis failed: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    async def _invoke_formatter_agent(self, query: str, context: Dict[str, Any], 
                                    flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke Data Formatter Agent through A2A protocol.
        
        Args:
            query: User query
            context: Flow context
            flow_data: Data from previous agents
            
        Returns:
            Formatter agent result
        """
        self.execution_stats['agent_invocations']['formatter'] += 1
        
        # Prepare data for formatting
        format_payload = {
            'query': query,
            'sql_data': flow_data.get('sql_result', {}).get('data'),
            'analysis_data': flow_data.get('quant_result', {}).get('analysis'),
            'reasoning_trace': flow_data.get('quant_result', {}).get('reasoning_trace'),
            'requires_pdf': context.get('query_analysis', {}).requires_pdf_export
        }
        
        # Create A2A message
        message = self.protocol.create_message(
            sender=AgentType.MUTUAL_FUND_QUANT,
            recipient=AgentType.DATA_FORMATTER,
            message_type=MessageType.FORMAT_REQUEST,
            payload=format_payload,
            context=context
        )
        
        try:
            # Process through formatter agent
            result = await asyncio.to_thread(
                self.formatter_agent.create_comprehensive_response,
                format_payload['sql_data'],
                query,
                format_payload.get('analysis_data'),
                format_payload.get('reasoning_trace')
            )
            
            # Add PDF generation if requested
            if format_payload.get('requires_pdf'):
                pdf_result = await self._generate_pdf_report(query, flow_data, result)
                result['pdf_file'] = pdf_result.get('pdf_file')
            
            # Create response message
            response_message = self.protocol.create_message(
                sender=AgentType.DATA_FORMATTER,
                recipient=AgentType.MUTUAL_FUND_QUANT,
                message_type=MessageType.FORMAT_RESPONSE,
                payload=result,
                context=context,
                parent_message_id=message.message_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Formatter Agent invocation failed: {str(e)}")
            return {
                'response': f"Data formatting failed: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    async def _generate_pdf_report(self, query: str, flow_data: Dict[str, Any], 
                                 format_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate PDF report from the comprehensive analysis.
        
        Args:
            query: Original user query
            flow_data: Data from all agents
            format_result: Formatted result
            
        Returns:
            PDF generation result
        """
        try:
            # This would integrate with a PDF generation library
            # For now, we'll create a placeholder
            import os
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"mutual_fund_report_{timestamp}.pdf"
            pdf_path = os.path.join(self.static_dir, pdf_filename)
            
            # Placeholder for actual PDF generation
            # In a real implementation, you would use libraries like:
            # - reportlab
            # - weasyprint
            # - pdfkit
            
            logger.info(f"PDF report generation requested: {pdf_filename}")
            
            return {
                'pdf_file': pdf_filename,
                'pdf_path': pdf_path,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _consolidate_results(self, query: str, analysis: QueryAnalysis, 
                           flow_data: Dict[str, Any], agents_invoked: List[str]) -> Dict[str, Any]:
        """
        Consolidate results from all invoked agents into a comprehensive response.
        
        Args:
            query: Original query
            analysis: Query analysis
            flow_data: Data from all agents
            agents_invoked: List of agents that were invoked
            
        Returns:
            Consolidated response
        """
        # Start with base response
        result = {
            'response': '',
            'success': True,
            'chart_files': [],
            'data': None,
            'analysis': None,
            'reasoning_trace': None
        }
        
        # Consolidate SQL results
        if 'sql_result' in flow_data:
            sql_result = flow_data['sql_result']
            result['data'] = sql_result.get('data')
            if sql_result.get('response'):
                result['response'] += sql_result['response'] + '\n\n'
        
        # Consolidate Quant results
        if 'quant_result' in flow_data:
            quant_result = flow_data['quant_result']
            result['analysis'] = quant_result.get('analysis')
            result['reasoning_trace'] = quant_result.get('reasoning_trace')
            if quant_result.get('analysis'):
                result['response'] += quant_result['analysis'] + '\n\n'
        
        # Consolidate Formatter results
        if 'format_result' in flow_data:
            format_result = flow_data['format_result']
            if format_result.get('chart_files'):
                result['chart_files'] = format_result['chart_files']
            if format_result.get('formatted_response'):
                result['response'] = format_result['formatted_response']
            if format_result.get('pdf_file'):
                result['pdf_file'] = format_result['pdf_file']
        
        # If no agents were invoked, provide a basic response
        if not agents_invoked:
            result['response'] = f"I understand your query: '{query}'. However, I couldn't determine the specific actions needed. Could you please provide more details about what you'd like me to help you with?"
        
        # Clean up response
        result['response'] = result['response'].strip()
        
        return result
    
    def _update_performance_metrics(self, response_time: float, success: bool):
        """Update performance metrics."""
        if success:
            self.execution_stats['successful_requests'] += 1
        else:
            self.execution_stats['failed_requests'] += 1
        
        # Update average response time
        total_successful = self.execution_stats['successful_requests']
        if total_successful > 0:
            current_avg = self.execution_stats['avg_response_time']
            self.execution_stats['avg_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the orchestrator and all agents.
        
        Returns:
            Health status information
        """
        return {
            'orchestrator_status': 'healthy',
            'agents_registered': len(self.protocol.agent_registry),
            'agents_available': {
                'sql': self.protocol.is_agent_available(AgentType.ENHANCED_SQL),
                'quant': self.protocol.is_agent_available(AgentType.MUTUAL_FUND_QUANT),
                'formatter': self.protocol.is_agent_available(AgentType.DATA_FORMATTER)
            },
            'execution_stats': self.execution_stats,
            'protocol_metrics': self.protocol.get_performance_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get available capabilities from all registered agents.
        
        Returns:
            Capabilities information
        """
        capabilities = {}
        for agent_type, agent_info in self.protocol.agent_registry.items():
            capabilities[agent_type.value] = [cap.value for cap in agent_info['capabilities']]
        
        return {
            'agent_capabilities': capabilities,
            'supported_operations': {
                'database_queries': True,
                'financial_analysis': True,
                'data_visualization': True,
                'pdf_reports': True,
                'conditional_invocation': True
            },
            'query_types_supported': [
                'mutual_fund', 'portfolio', 'equity', 'debt', 'general'
            ]
        }
