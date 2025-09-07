#!/usr/bin/env python3
"""
MCP Orchestrator - Drop-in replacement for AgentOrchestrator

Maintains exact same API as current AgentOrchestrator while using MCP servers internally.
Provides seamless migration to MCP-based architecture with zero functionality loss.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

from .mcp_client_manager import get_mcp_client_manager

logger = logging.getLogger(__name__)

class MCPOrchestrator:
    """
    Drop-in replacement for current AgentOrchestrator.
    
    Maintains exact same API while using MCP servers internally:
    - Same method signatures
    - Same response formats
    - Same error handling
    - Enhanced security through MCP isolation
    """
    
    def __init__(self, static_dir: str = "static/charts"):
        """
        Initialize MCP Orchestrator.
        
        Args:
            static_dir: Directory for chart files (maintains compatibility)
        """
        self.static_dir = static_dir
        self.mcp_manager = get_mcp_client_manager()
        
        # Agent performance tracking (maintains compatibility)
        self.execution_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }
        
        # Initialize MCP clients
        self._initialize_mcp_clients()
    
    def _initialize_mcp_clients(self):
        """Initialize MCP client connections."""
        try:
            # This will be called asynchronously when needed
            pass
        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {str(e)}")
    
    async def process_query(self, query: str, user_email: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process query through MCP-based agent pipeline.
        
        Maintains exact same API as current AgentOrchestrator.process_query()
        
        Args:
            query: Natural language query
            user_email: User email for schema isolation
            session_id: Optional session ID
            
        Returns:
            Dict with same format as current orchestrator:
            {
                "response": str,
                "chart_files": List[str],
                "metadata": Dict[str, Any]
            }
        """
        start_time = datetime.now()
        self.execution_stats['total_requests'] += 1
        
        try:
            # Ensure MCP clients are initialized
            await self._ensure_mcp_clients_ready()
            
            # Step 1: Process query with SQL Database MCP Server
            sql_result = await self._process_sql_query(query, user_email, session_id)
            
            if sql_result.get("status") != "success":
                self.execution_stats['failed_requests'] += 1
                return self._format_error_response(sql_result.get("error", "SQL processing failed"))
            
            # Step 2: Determine if financial analysis is needed
            needs_analytics = self._needs_financial_analysis(query, sql_result)
            analytics_result = None
            
            if needs_analytics:
                analytics_result = await self._process_financial_analysis(sql_result)
            
            # Step 3: Determine if visualization is needed
            needs_visualization = self._needs_visualization(query)
            chart_result = None
            
            if needs_visualization:
                chart_result = await self._process_visualization(query, sql_result, analytics_result)
            
            # Step 4: Combine results and format response
            final_response = self._combine_results(sql_result, analytics_result, chart_result)
            
            # Update stats
            self.execution_stats['successful_requests'] += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_avg_response_time(execution_time)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in MCP orchestrator: {str(e)}")
            self.execution_stats['failed_requests'] += 1
            return self._format_error_response(f"Query processing failed: {str(e)}")
    
    async def _ensure_mcp_clients_ready(self):
        """Ensure MCP clients are initialized and ready."""
        try:
            # Check if clients are already initialized
            status = self.mcp_manager.get_connection_status()
            
            if not status or all(s != "connected" for s in status.values()):
                # Initialize clients if not ready
                success = await self.mcp_manager.initialize_clients()
                if not success:
                    raise Exception("Failed to initialize MCP clients")
                    
        except Exception as e:
            logger.error(f"MCP client initialization failed: {str(e)}")
            raise
    
    async def _process_sql_query(self, query: str, user_email: str, session_id: Optional[str]) -> Dict[str, Any]:
        """Process query with SQL Database MCP Server."""
        try:
            arguments = {
                "query": query,
                "user_email": user_email,
                "session_id": session_id or str(uuid.uuid4())
            }
            
            result = await self.mcp_manager.call_sql_tool("execute_sql_query", arguments)
            return result
            
        except Exception as e:
            logger.error(f"SQL query processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_financial_analysis(self, sql_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process financial analysis with Financial Analytics MCP Server."""
        try:
            # Extract data from SQL result
            data = sql_result.get("data", {})
            
            if not data:
                return None
            
            arguments = {
                "data": data,
                "risk_free_rate": 0.05,
                "metrics": ["total_return", "volatility", "sharpe_ratio", "max_drawdown"]
            }
            
            result = await self.mcp_manager.call_analytics_tool("calculate_portfolio_metrics", arguments)
            return result
            
        except Exception as e:
            logger.error(f"Financial analysis failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_visualization(self, query: str, sql_result: Dict[str, Any], analytics_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process visualization with Visualization MCP Server."""
        try:
            # Determine chart type from query
            chart_type = self._determine_chart_type(query)
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(sql_result, analytics_result)
            
            if not chart_data:
                return None
            
            arguments = {
                "data": chart_data,
                "chart_type": chart_type,
                "title": self._generate_chart_title(query),
                "x_label": "X Axis",
                "y_label": "Y Axis",
                "theme": "plotly_white"
            }
            
            result = await self.mcp_manager.call_visualization_tool("create_plotly_chart", arguments)
            return result
            
        except Exception as e:
            logger.error(f"Visualization processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _needs_financial_analysis(self, query: str, sql_result: Dict[str, Any]) -> bool:
        """Determine if financial analysis is needed."""
        financial_keywords = [
            'portfolio', 'return', 'risk', 'sharpe', 'volatility', 
            'performance', 'analysis', 'metrics', 'fund', 'investment'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in financial_keywords)
    
    def _needs_visualization(self, query: str) -> bool:
        """Determine if visualization is needed."""
        viz_keywords = [
            'chart', 'graph', 'plot', 'visualiz', 'show me', 'display',
            'draw', 'create', 'generate', 'bar', 'line', 'pie'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in viz_keywords)
    
    def _determine_chart_type(self, query: str) -> str:
        """Determine appropriate chart type from query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['bar', 'column']):
            return 'bar'
        elif any(word in query_lower for word in ['line', 'trend', 'time']):
            return 'line'
        elif any(word in query_lower for word in ['pie', 'donut', 'proportion']):
            return 'pie'
        elif any(word in query_lower for word in ['scatter', 'correlation']):
            return 'scatter'
        elif any(word in query_lower for word in ['table', 'list']):
            return 'table'
        else:
            return 'bar'  # Default
    
    def _prepare_chart_data(self, sql_result: Dict[str, Any], analytics_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for chart generation."""
        try:
            # Try to extract data from SQL result
            data = sql_result.get("data", {})
            
            if isinstance(data, dict):
                # Convert dict to x/y format if possible
                if len(data) >= 2:
                    keys = list(data.keys())
                    return {
                        "x": data[keys[0]] if isinstance(data[keys[0]], list) else [data[keys[0]]],
                        "y": data[keys[1]] if isinstance(data[keys[1]], list) else [data[keys[1]]]
                    }
            
            # If analytics result available, use metrics
            if analytics_result and analytics_result.get("status") == "success":
                metrics = analytics_result.get("metrics", {})
                if metrics:
                    return {
                        "x": list(metrics.keys()),
                        "y": list(metrics.values())
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Chart data preparation failed: {str(e)}")
            return {}
    
    def _generate_chart_title(self, query: str) -> str:
        """Generate appropriate chart title from query."""
        # Simple title generation
        if 'portfolio' in query.lower():
            return 'Portfolio Analysis'
        elif 'performance' in query.lower():
            return 'Performance Metrics'
        elif 'risk' in query.lower():
            return 'Risk Analysis'
        else:
            return 'Data Visualization'
    
    def _combine_results(self, sql_result: Dict[str, Any], analytics_result: Optional[Dict[str, Any]], chart_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine results from all MCP servers into final response."""
        # Build response text
        response_parts = []
        
        # Add SQL response
        if sql_result.get("response"):
            response_parts.append(sql_result["response"])
        
        # Add analytics insights
        if analytics_result and analytics_result.get("status") == "success":
            metrics = analytics_result.get("metrics", {})
            if metrics:
                response_parts.append(f"\nFinancial Analysis:")
                for metric, value in metrics.items():
                    response_parts.append(f"- {metric.replace('_', ' ').title()}: {value:.4f}")
        
        # Combine response text
        final_response = "\n".join(response_parts) if response_parts else "Query processed successfully."
        
        # Extract chart files
        chart_files = []
        if chart_result and chart_result.get("status") == "success":
            chart_files = chart_result.get("chart_files", [])
        
        # Build metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "sql_metadata": sql_result.get("metadata", {}),
            "analytics_metadata": analytics_result.get("metadata", {}) if analytics_result else {},
            "chart_metadata": chart_result.get("metadata", {}) if chart_result else {},
            "mcp_servers_used": []
        }
        
        # Track which servers were used
        if sql_result.get("status") == "success":
            metadata["mcp_servers_used"].append("sql_database")
        if analytics_result and analytics_result.get("status") == "success":
            metadata["mcp_servers_used"].append("financial_analytics")
        if chart_result and chart_result.get("status") == "success":
            metadata["mcp_servers_used"].append("visualization")
        
        return {
            "response": final_response,
            "chart_files": chart_files,
            "metadata": metadata
        }
    
    def _format_error_response(self, error_message: str) -> Dict[str, Any]:
        """Format error response in expected format."""
        return {
            "response": f"I apologize, but I encountered an error while processing your query: {error_message}",
            "chart_files": [],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "error": error_message,
                "status": "error"
            }
        }
    
    def _update_avg_response_time(self, execution_time: float):
        """Update average response time statistics."""
        total_successful = self.execution_stats['successful_requests']
        if total_successful > 1:
            current_avg = self.execution_stats['avg_response_time']
            new_avg = ((current_avg * (total_successful - 1)) + execution_time) / total_successful
            self.execution_stats['avg_response_time'] = new_avg
        else:
            self.execution_stats['avg_response_time'] = execution_time
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of MCP orchestrator and servers.
        
        Maintains compatibility with current orchestrator health checks.
        """
        try:
            # Get MCP client manager health
            mcp_health = await self.mcp_manager.health_check()
            
            # Combine with orchestrator stats
            return {
                "status": "healthy" if mcp_health.get("status") == "healthy" else "degraded",
                "orchestrator_stats": self.execution_stats,
                "mcp_servers": mcp_health.get("servers", {}),
                "mcp_summary": mcp_health.get("summary", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "orchestrator_stats": self.execution_stats,
                "timestamp": datetime.now().isoformat()
            }
    
    async def refresh_connections(self) -> Dict[str, Any]:
        """Refresh MCP server connections."""
        try:
            # Shutdown existing connections
            await self.mcp_manager.shutdown()
            
            # Reinitialize
            success = await self.mcp_manager.initialize_clients()
            
            return {
                "status": "success" if success else "failed",
                "message": "MCP connections refreshed" if success else "Failed to refresh connections",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Connection refresh failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics (maintains compatibility)."""
        return {
            "execution_stats": self.execution_stats,
            "static_dir": self.static_dir,
            "mcp_connection_status": self.mcp_manager.get_connection_status(),
            "timestamp": datetime.now().isoformat()
        }

# Global orchestrator instance for backward compatibility
_mcp_orchestrator = None

def get_mcp_orchestrator(static_dir: str = "static/charts") -> MCPOrchestrator:
    """Get global MCP orchestrator instance."""
    global _mcp_orchestrator
    if _mcp_orchestrator is None:
        _mcp_orchestrator = MCPOrchestrator(static_dir=static_dir)
    return _mcp_orchestrator

# Backward compatibility alias
def get_orchestrator(static_dir: str = "static/charts") -> MCPOrchestrator:
    """Backward compatibility alias for get_mcp_orchestrator."""
    return get_mcp_orchestrator(static_dir)
