#!/usr/bin/env python3
"""
Financial Analytics MCP Server

Provides secure financial analysis operations through MCP protocol:
- Portfolio analysis and risk calculations
- Mutual fund performance metrics
- Financial data processing with pandas
- Correlation and statistical analysis
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as mcp_types

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Local imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class FinancialAnalyticsMCPServer:
    """
    MCP Server for Financial Analytics operations with enhanced security.
    
    Provides isolated financial calculations through MCP protocol:
    - Portfolio analysis and optimization
    - Risk metrics and performance calculations
    - Mutual fund analysis
    - Statistical computations
    """
    
    def __init__(self):
        self.server = Server("financial-analytics")
        self.calculation_cache = {}
        self.setup_resources()
        self.setup_tools()
        
    def setup_resources(self):
        """Setup MCP resources for financial analytics."""
        
        @self.server.list_resources()
        async def list_resources() -> List[mcp_types.Resource]:
            """List available financial analytics resources."""
            return [
                mcp_types.Resource(
                    uri="analytics://portfolio/metrics",
                    name="Portfolio Metrics",
                    description="Standard portfolio performance metrics",
                    mimeType="application/json"
                ),
                mcp_types.Resource(
                    uri="analytics://risk/models",
                    name="Risk Models",
                    description="Available risk analysis models",
                    mimeType="application/json"
                ),
                mcp_types.Resource(
                    uri="analytics://mutual_funds/categories",
                    name="Mutual Fund Categories",
                    description="Mutual fund classification and analysis categories",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: mcp_types.AnyUrl) -> str:
            """Read financial analytics resource content."""
            uri_str = str(uri)
            
            if uri_str == "analytics://portfolio/metrics":
                metrics_info = {
                    "available_metrics": [
                        "total_return", "annualized_return", "volatility",
                        "sharpe_ratio", "max_drawdown", "beta", "alpha",
                        "information_ratio", "treynor_ratio", "sortino_ratio"
                    ],
                    "description": "Standard portfolio performance and risk metrics"
                }
                return json.dumps(metrics_info, indent=2)
            
            elif uri_str == "analytics://risk/models":
                risk_models = {
                    "available_models": [
                        "value_at_risk", "conditional_var", "monte_carlo_simulation",
                        "correlation_analysis", "factor_analysis", "stress_testing"
                    ],
                    "description": "Risk analysis and modeling capabilities"
                }
                return json.dumps(risk_models, indent=2)
            
            elif uri_str == "analytics://mutual_funds/categories":
                mf_categories = {
                    "categories": [
                        "equity", "debt", "hybrid", "solution_oriented",
                        "other_schemes"
                    ],
                    "analysis_types": [
                        "performance_analysis", "risk_analysis", "expense_analysis",
                        "portfolio_composition", "benchmark_comparison"
                    ]
                }
                return json.dumps(mf_categories, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    def setup_tools(self):
        """Setup MCP tools for financial analytics."""
        
        @self.server.call_tool()
        async def calculate_portfolio_metrics(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Calculate comprehensive portfolio performance metrics.
            
            Args:
                arguments: {
                    "data": dict - Portfolio data (returns, prices, holdings)
                    "benchmark_data": dict - Optional benchmark data
                    "risk_free_rate": float - Risk-free rate for calculations
                    "metrics": list - Specific metrics to calculate
                }
            """
            try:
                if not PANDAS_AVAILABLE:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Pandas not available for financial calculations",
                            "status": "error"
                        })
                    )]
                
                data = arguments.get("data", {})
                benchmark_data = arguments.get("benchmark_data", {})
                risk_free_rate = arguments.get("risk_free_rate", 0.05)
                requested_metrics = arguments.get("metrics", ["total_return", "volatility", "sharpe_ratio"])
                
                # Validate input data
                if not data:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "No portfolio data provided",
                            "status": "error"
                        })
                    )]
                
                # Calculate metrics
                metrics_result = await self._calculate_metrics(data, benchmark_data, risk_free_rate, requested_metrics)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(metrics_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error calculating portfolio metrics: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Portfolio metrics calculation failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def analyze_risk_factors(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Perform comprehensive risk analysis.
            
            Args:
                arguments: {
                    "portfolio_data": dict - Portfolio returns/prices data
                    "market_data": dict - Market/benchmark data
                    "confidence_level": float - Confidence level for VaR (default 0.95)
                    "time_horizon": int - Time horizon in days (default 252)
                }
            """
            try:
                if not PANDAS_AVAILABLE:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Pandas not available for risk analysis",
                            "status": "error"
                        })
                    )]
                
                portfolio_data = arguments.get("portfolio_data", {})
                market_data = arguments.get("market_data", {})
                confidence_level = arguments.get("confidence_level", 0.95)
                time_horizon = arguments.get("time_horizon", 252)
                
                # Perform risk analysis
                risk_analysis = await self._analyze_risk(portfolio_data, market_data, confidence_level, time_horizon)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(risk_analysis, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error in risk analysis: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Risk analysis failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def compute_correlations(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Compute correlation analysis between assets/funds.
            
            Args:
                arguments: {
                    "data": dict - Asset returns data
                    "method": str - Correlation method ("pearson", "spearman", "kendall")
                    "rolling_window": int - Optional rolling correlation window
                }
            """
            try:
                if not PANDAS_AVAILABLE:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Pandas not available for correlation analysis",
                            "status": "error"
                        })
                    )]
                
                data = arguments.get("data", {})
                method = arguments.get("method", "pearson")
                rolling_window = arguments.get("rolling_window", None)
                
                # Compute correlations
                correlation_result = await self._compute_correlations(data, method, rolling_window)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(correlation_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error computing correlations: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Correlation analysis failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def analyze_mutual_fund_performance(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Analyze mutual fund performance and characteristics.
            
            Args:
                arguments: {
                    "fund_data": dict - Mutual fund data (NAV, returns, AUM, etc.)
                    "benchmark_data": dict - Benchmark comparison data
                    "analysis_type": str - Type of analysis ("performance", "risk", "expense")
                    "time_period": str - Analysis time period ("1Y", "3Y", "5Y", "inception")
                }
            """
            try:
                if not PANDAS_AVAILABLE:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Pandas not available for mutual fund analysis",
                            "status": "error"
                        })
                    )]
                
                fund_data = arguments.get("fund_data", {})
                benchmark_data = arguments.get("benchmark_data", {})
                analysis_type = arguments.get("analysis_type", "performance")
                time_period = arguments.get("time_period", "1Y")
                
                # Analyze mutual fund
                mf_analysis = await self._analyze_mutual_fund(fund_data, benchmark_data, analysis_type, time_period)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(mf_analysis, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error in mutual fund analysis: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Mutual fund analysis failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def generate_financial_insights(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Generate financial insights and recommendations.
            
            Args:
                arguments: {
                    "analysis_data": dict - Results from previous analyses
                    "context": str - Analysis context (portfolio, fund, market)
                    "user_profile": dict - User risk profile and preferences
                }
            """
            try:
                analysis_data = arguments.get("analysis_data", {})
                context = arguments.get("context", "portfolio")
                user_profile = arguments.get("user_profile", {})
                
                # Generate insights
                insights = await self._generate_insights(analysis_data, context, user_profile)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(insights, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error generating insights: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Insight generation failed: {str(e)}",
                        "status": "error"
                    })
                )]
    
    async def _calculate_metrics(self, data: dict, benchmark_data: dict, risk_free_rate: float, requested_metrics: list) -> dict:
        """Calculate portfolio performance metrics."""
        try:
            # Convert data to DataFrame if needed
            if isinstance(data.get("returns"), list):
                returns = pd.Series(data["returns"])
            else:
                returns = pd.Series([])
            
            if returns.empty:
                return {
                    "status": "error",
                    "error": "No valid returns data provided"
                }
            
            metrics = {}
            
            # Calculate requested metrics
            for metric in requested_metrics:
                if metric == "total_return":
                    metrics["total_return"] = float((1 + returns).prod() - 1)
                elif metric == "annualized_return":
                    metrics["annualized_return"] = float(returns.mean() * 252)
                elif metric == "volatility":
                    metrics["volatility"] = float(returns.std() * np.sqrt(252))
                elif metric == "sharpe_ratio":
                    excess_return = returns.mean() - risk_free_rate/252
                    metrics["sharpe_ratio"] = float(excess_return / returns.std() * np.sqrt(252))
                elif metric == "max_drawdown":
                    cumulative = (1 + returns).cumprod()
                    rolling_max = cumulative.expanding().max()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    metrics["max_drawdown"] = float(drawdown.min())
            
            return {
                "status": "success",
                "metrics": metrics,
                "data_points": len(returns),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_risk(self, portfolio_data: dict, market_data: dict, confidence_level: float, time_horizon: int) -> dict:
        """Perform comprehensive risk analysis."""
        try:
            # Convert to pandas if needed
            if isinstance(portfolio_data.get("returns"), list):
                returns = pd.Series(portfolio_data["returns"])
            else:
                returns = pd.Series([])
            
            if returns.empty:
                return {
                    "status": "error",
                    "error": "No valid portfolio returns data"
                }
            
            risk_metrics = {}
            
            # Value at Risk (VaR)
            var_percentile = (1 - confidence_level) * 100
            risk_metrics["value_at_risk"] = float(np.percentile(returns, var_percentile))
            
            # Conditional VaR (Expected Shortfall)
            var_threshold = risk_metrics["value_at_risk"]
            conditional_var = returns[returns <= var_threshold].mean()
            risk_metrics["conditional_var"] = float(conditional_var)
            
            # Volatility
            risk_metrics["volatility"] = float(returns.std() * np.sqrt(252))
            
            # Downside deviation
            downside_returns = returns[returns < 0]
            risk_metrics["downside_deviation"] = float(downside_returns.std() * np.sqrt(252))
            
            return {
                "status": "success",
                "risk_metrics": risk_metrics,
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _compute_correlations(self, data: dict, method: str, rolling_window: Optional[int]) -> dict:
        """Compute correlation analysis."""
        try:
            # Convert data to DataFrame
            df_data = {}
            for asset, values in data.items():
                if isinstance(values, list):
                    df_data[asset] = values
            
            if not df_data:
                return {
                    "status": "error",
                    "error": "No valid correlation data provided"
                }
            
            df = pd.DataFrame(df_data)
            
            # Compute correlation matrix
            if rolling_window:
                correlation_matrix = df.rolling(window=rolling_window).corr()
                # Get the last correlation matrix
                correlation_result = correlation_matrix.iloc[-len(df.columns):].to_dict()
            else:
                correlation_matrix = df.corr(method=method)
                correlation_result = correlation_matrix.to_dict()
            
            return {
                "status": "success",
                "correlation_matrix": correlation_result,
                "method": method,
                "rolling_window": rolling_window,
                "assets": list(df.columns),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_mutual_fund(self, fund_data: dict, benchmark_data: dict, analysis_type: str, time_period: str) -> dict:
        """Analyze mutual fund performance."""
        try:
            analysis_result = {
                "fund_name": fund_data.get("name", "Unknown Fund"),
                "analysis_type": analysis_type,
                "time_period": time_period,
                "timestamp": datetime.now().isoformat()
            }
            
            if analysis_type == "performance":
                # Performance analysis
                nav_data = fund_data.get("nav", [])
                if nav_data:
                    nav_series = pd.Series(nav_data)
                    returns = nav_series.pct_change().dropna()
                    
                    analysis_result["performance_metrics"] = {
                        "total_return": float((nav_series.iloc[-1] / nav_series.iloc[0]) - 1),
                        "annualized_return": float(returns.mean() * 252),
                        "volatility": float(returns.std() * np.sqrt(252)),
                        "max_drawdown": float(((nav_series / nav_series.expanding().max()) - 1).min())
                    }
            
            elif analysis_type == "risk":
                # Risk analysis
                returns_data = fund_data.get("returns", [])
                if returns_data:
                    returns = pd.Series(returns_data)
                    analysis_result["risk_metrics"] = {
                        "volatility": float(returns.std() * np.sqrt(252)),
                        "value_at_risk_95": float(np.percentile(returns, 5)),
                        "downside_deviation": float(returns[returns < 0].std() * np.sqrt(252))
                    }
            
            elif analysis_type == "expense":
                # Expense analysis
                analysis_result["expense_metrics"] = {
                    "expense_ratio": fund_data.get("expense_ratio", 0),
                    "exit_load": fund_data.get("exit_load", 0),
                    "minimum_investment": fund_data.get("min_investment", 0)
                }
            
            return {
                "status": "success",
                "analysis": analysis_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_insights(self, analysis_data: dict, context: str, user_profile: dict) -> dict:
        """Generate financial insights and recommendations."""
        try:
            insights = {
                "context": context,
                "insights": [],
                "recommendations": [],
                "risk_assessment": "moderate",
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate context-specific insights
            if context == "portfolio":
                if "metrics" in analysis_data:
                    metrics = analysis_data["metrics"]
                    
                    # Sharpe ratio insights
                    if "sharpe_ratio" in metrics:
                        sharpe = metrics["sharpe_ratio"]
                        if sharpe > 1.0:
                            insights["insights"].append("Portfolio shows excellent risk-adjusted returns (Sharpe > 1.0)")
                        elif sharpe > 0.5:
                            insights["insights"].append("Portfolio shows good risk-adjusted returns")
                        else:
                            insights["insights"].append("Portfolio risk-adjusted returns could be improved")
                    
                    # Volatility insights
                    if "volatility" in metrics:
                        vol = metrics["volatility"]
                        if vol > 0.25:
                            insights["risk_assessment"] = "high"
                            insights["insights"].append("Portfolio exhibits high volatility - consider diversification")
                        elif vol < 0.10:
                            insights["risk_assessment"] = "low"
                            insights["insights"].append("Portfolio shows low volatility - stable but potentially lower returns")
            
            return {
                "status": "success",
                "insights": insights
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

async def main():
    """Main entry point for Financial Analytics MCP Server."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Financial Analytics MCP Server...")
    
    # Create and run server
    server_instance = FinancialAnalyticsMCPServer()
    
    # Run server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="financial-analytics",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
