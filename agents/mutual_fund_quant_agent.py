#!/usr/bin/env python3
"""
Mutual Fund Quant Agent - Advanced Financial Reasoning and Quantitative Analysis

This agent implements a sophisticated ReAct (Reasoning + Acting) pattern for deep financial analysis:
- Multi-step reasoning with thought-action-observation cycles
- Chain-of-thought reasoning for complex financial decisions
- Advanced quantitative analysis with contextual insights
- Memory-based learning from previous analysis patterns
- Sophisticated financial reasoning tools and frameworks
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningStep(Enum):
    """Enumeration of reasoning steps in the ReAct framework."""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    CONCLUSION = "conclusion"


@dataclass
class ReasoningTrace:
    """Represents a single reasoning step in the ReAct framework."""
    step_type: ReasoningStep
    content: str
    data: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FinancialReasoningTools:
    """Advanced financial reasoning tools for sophisticated analysis."""
    
    @staticmethod
    def assess_risk_profile(data: pd.DataFrame, scheme_name: str = None) -> Dict[str, Any]:
        """Assess comprehensive risk profile with multi-dimensional analysis."""
        risk_assessment = {
            'volatility_analysis': {},
            'drawdown_analysis': {},
            'risk_adjusted_metrics': {},
            'risk_category': 'Unknown',
            'risk_score': 0.0
        }
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                if 'return' in col.lower() or 'nav' in col.lower() or 'price' in col.lower():
                    values = data[col].dropna()
                    if len(values) > 1:
                        # Volatility analysis
                        volatility = values.std()
                        annualized_vol = volatility * np.sqrt(252) if len(values) > 252 else volatility * np.sqrt(len(values))
                        
                        # Drawdown analysis
                        running_max = values.expanding().max()
                        drawdown = (values - running_max) / running_max
                        max_drawdown = drawdown.min()
                        
                        # Risk-adjusted metrics
                        mean_return = values.mean()
                        sharpe_ratio = mean_return / volatility if volatility != 0 else 0
                        
                        risk_assessment['volatility_analysis'][col] = {
                            'daily_volatility': volatility,
                            'annualized_volatility': annualized_vol,
                            'volatility_percentile': np.percentile(values, 75) - np.percentile(values, 25)
                        }
                        
                        risk_assessment['drawdown_analysis'][col] = {
                            'max_drawdown': max_drawdown,
                            'avg_drawdown': drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0,
                            'recovery_periods': len(drawdown[drawdown < 0])
                        }
                        
                        risk_assessment['risk_adjusted_metrics'][col] = {
                            'sharpe_ratio': sharpe_ratio,
                            'sortino_ratio': mean_return / values[values < 0].std() if len(values[values < 0]) > 0 else 0,
                            'calmar_ratio': mean_return / abs(max_drawdown) if max_drawdown != 0 else 0
                        }
                        
                        # Risk categorization
                        if annualized_vol < 0.1:
                            risk_assessment['risk_category'] = 'Low Risk'
                            risk_assessment['risk_score'] = 2.0
                        elif annualized_vol < 0.2:
                            risk_assessment['risk_category'] = 'Moderate Risk'
                            risk_assessment['risk_score'] = 5.0
                        elif annualized_vol < 0.3:
                            risk_assessment['risk_category'] = 'High Risk'
                            risk_assessment['risk_score'] = 7.5
                        else:
                            risk_assessment['risk_category'] = 'Very High Risk'
                            risk_assessment['risk_score'] = 9.0
        
        return risk_assessment
    
    @staticmethod
    def analyze_performance_context(data: pd.DataFrame, time_period: str = "overall") -> Dict[str, Any]:
        """Analyze performance in market context with sophisticated metrics."""
        context_analysis = {
            'performance_metrics': {},
            'market_context': {},
            'trend_analysis': {},
            'performance_consistency': {}
        }
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if 'return' in col.lower() or 'performance' in col.lower():
                values = data[col].dropna()
                if len(values) > 0:
                    # Performance metrics
                    total_return = values.sum() if 'return' in col.lower() else (values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100
                    avg_return = values.mean()
                    median_return = values.median()
                    
                    # Trend analysis
                    if len(values) > 1:
                        trend_slope = np.polyfit(range(len(values)), values, 1)[0]
                        trend_direction = "Upward" if trend_slope > 0 else "Downward" if trend_slope < 0 else "Flat"
                    else:
                        trend_slope = 0
                        trend_direction = "Insufficient Data"
                    
                    # Performance consistency
                    consistency_score = 1 - (values.std() / abs(values.mean())) if values.mean() != 0 else 0
                    
                    context_analysis['performance_metrics'][col] = {
                        'total_return': total_return,
                        'average_return': avg_return,
                        'median_return': median_return,
                        'best_period': values.max(),
                        'worst_period': values.min()
                    }
                    
                    context_analysis['trend_analysis'][col] = {
                        'trend_slope': trend_slope,
                        'trend_direction': trend_direction,
                        'momentum': values.iloc[-5:].mean() - values.iloc[:5].mean() if len(values) >= 10 else 0
                    }
                    
                    context_analysis['performance_consistency'][col] = {
                        'consistency_score': consistency_score,
                        'volatility_of_returns': values.std(),
                        'positive_periods': len(values[values > 0]) / len(values) * 100
                    }
        
        return context_analysis
    
    @staticmethod
    def generate_investment_thesis(risk_profile: Dict, performance_context: Dict, 
                                 market_conditions: str = "neutral") -> Dict[str, Any]:
        """Generate sophisticated investment thesis based on comprehensive analysis."""
        thesis = {
            'investment_recommendation': 'Hold',
            'confidence_level': 0.5,
            'key_strengths': [],
            'key_concerns': [],
            'market_suitability': {},
            'strategic_considerations': []
        }
        
        # Analyze risk-return profile
        avg_risk_score = risk_profile.get('risk_score', 5.0)
        
        # Extract performance insights
        performance_metrics = performance_context.get('performance_metrics', {})
        trend_analysis = performance_context.get('trend_analysis', {})
        consistency = performance_context.get('performance_consistency', {})
        
        # Generate recommendation logic
        positive_factors = 0
        negative_factors = 0
        
        for col, metrics in performance_metrics.items():
            if metrics.get('average_return', 0) > 0:
                positive_factors += 1
                thesis['key_strengths'].append(f"Positive average returns in {col}")
            else:
                negative_factors += 1
                thesis['key_concerns'].append(f"Negative average returns in {col}")
        
        for col, trend in trend_analysis.items():
            if trend.get('trend_direction') == 'Upward':
                positive_factors += 1
                thesis['key_strengths'].append(f"Upward trend in {col}")
            elif trend.get('trend_direction') == 'Downward':
                negative_factors += 1
                thesis['key_concerns'].append(f"Downward trend in {col}")
        
        # Risk assessment impact
        if avg_risk_score <= 3:
            thesis['key_strengths'].append("Low risk profile suitable for conservative investors")
        elif avg_risk_score >= 8:
            thesis['key_concerns'].append("High risk profile requires careful consideration")
        
        # Generate final recommendation
        if positive_factors > negative_factors * 1.5:
            thesis['investment_recommendation'] = 'Buy'
            thesis['confidence_level'] = min(0.9, 0.6 + (positive_factors - negative_factors) * 0.1)
        elif negative_factors > positive_factors * 1.5:
            thesis['investment_recommendation'] = 'Sell'
            thesis['confidence_level'] = min(0.9, 0.6 + (negative_factors - positive_factors) * 0.1)
        else:
            thesis['investment_recommendation'] = 'Hold'
            thesis['confidence_level'] = 0.5
        
        # Market suitability analysis
        thesis['market_suitability'] = {
            'bull_market': 'Suitable' if avg_risk_score >= 5 else 'Moderate',
            'bear_market': 'Suitable' if avg_risk_score <= 5 else 'Risky',
            'volatile_market': 'Suitable' if avg_risk_score <= 7 else 'High Risk'
        }
        
        return thesis


class MutualFundQuantAgent:
    """
    Advanced Mutual Fund Quant Agent with ReAct Reasoning Framework.
    
    This agent implements sophisticated reasoning patterns:
    - ReAct (Reasoning + Acting) framework for deep analysis
    - Chain-of-thought reasoning for complex financial decisions
    - Multi-step reasoning with thought-action-observation cycles
    - Memory-based learning from previous analysis patterns
    - Advanced financial reasoning tools and contextual insights
    """
    
    def __init__(self):
        """Initialize the Advanced Mutual Fund Quant Agent with ReAct framework."""
        self.calculation_cache = {}
        self.reasoning_memory = {}  # Store reasoning patterns for learning
        self.financial_tools = FinancialReasoningTools()
        self.reasoning_traces = []  # Store complete reasoning chains
        
        logger.info("🧮 Advanced Mutual Fund Quant Agent with ReAct reasoning initialized")
    
    def process_data(self, sql_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Process SQL data using advanced ReAct reasoning framework.
        
        This method implements sophisticated reasoning patterns:
        1. THOUGHT: Analyze the query and data context
        2. ACTION: Execute appropriate financial analysis tools
        3. OBSERVATION: Evaluate results and intermediate findings
        4. REFLECTION: Consider implications and generate insights
        5. CONCLUSION: Synthesize final recommendations
        
        Args:
            sql_data: Data from Enhanced SQL Agent
            query: Original user query for context
            
        Returns:
            Dictionary containing sophisticated analysis with reasoning traces
        """
        reasoning_session_id = f"reasoning_{int(datetime.now().timestamp())}"
        reasoning_traces = []
        
        try:
            logger.info(f"🧠 Starting ReAct reasoning analysis [Session: {reasoning_session_id}]")
            
            # STEP 1: THOUGHT - Initial analysis of the problem
            thought_trace = self._add_reasoning_step(
                ReasoningStep.THOUGHT,
                f"Analyzing user query: '{query}'. I need to understand what type of financial analysis is required and examine the available data structure.",
                reasoning_traces
            )
            
            # Extract and validate raw data
            raw_data = sql_data.get('sql_data', [])
            if not raw_data:
                error_trace = self._add_reasoning_step(
                    ReasoningStep.OBSERVATION,
                    "No data available for analysis. Cannot proceed with quantitative analysis.",
                    reasoning_traces,
                    confidence=0.0
                )
                return self._create_error_response("No data available for analysis", query, reasoning_traces)
            
            # STEP 2: ACTION - Convert data and perform initial analysis
            action_trace = self._add_reasoning_step(
                ReasoningStep.ACTION,
                f"Converting {len(raw_data)} rows of SQL data to pandas DataFrame for analysis. Examining data structure and quality.",
                reasoning_traces
            )
            
            df = self._create_dataframe(raw_data)
            if df is None or df.empty:
                error_trace = self._add_reasoning_step(
                    ReasoningStep.OBSERVATION,
                    "Failed to create valid DataFrame from SQL data. Data may be malformed or empty.",
                    reasoning_traces,
                    confidence=0.0
                )
                return self._create_error_response("Unable to process data into DataFrame", query, reasoning_traces)
            
            # STEP 3: OBSERVATION - Analyze data characteristics
            observation_trace = self._add_reasoning_step(
                ReasoningStep.OBSERVATION,
                f"Successfully created DataFrame with {df.shape[0]} rows and {df.shape[1]} columns. "
                f"Columns: {list(df.columns)}. Numeric columns: {list(df.select_dtypes(include=[np.number]).columns)}",
                reasoning_traces,
                data={'dataframe_shape': df.shape, 'columns': list(df.columns)},
                confidence=0.8
            )
            
            # STEP 4: THOUGHT - Determine analysis strategy
            analysis_strategy = self._determine_analysis_strategy(query, df)
            strategy_trace = self._add_reasoning_step(
                ReasoningStep.THOUGHT,
                f"Based on the query pattern and data structure, I will execute: {analysis_strategy['strategy']}. "
                f"This involves: {', '.join(analysis_strategy['components'])}",
                reasoning_traces,
                data=analysis_strategy,
                confidence=analysis_strategy['confidence']
            )
            
            # STEP 5: ACTION - Execute comprehensive financial analysis
            analysis_results = self._execute_comprehensive_analysis(df, query, analysis_strategy, reasoning_traces)
            
            # STEP 6: REFLECTION - Synthesize insights and implications
            reflection_trace = self._add_reasoning_step(
                ReasoningStep.REFLECTION,
                f"Analysis completed with {len(analysis_results.get('calculations', {}))} quantitative metrics. "
                f"Key findings: {analysis_results.get('key_findings', 'Standard analysis completed')}. "
                f"Investment implications: {analysis_results.get('investment_implications', 'Requires further context')}",
                reasoning_traces,
                data=analysis_results.get('reflection_data', {}),
                confidence=analysis_results.get('analysis_confidence', 0.7)
            )
            
            # STEP 7: CONCLUSION - Generate final recommendations
            final_recommendations = self._generate_final_recommendations(analysis_results, query, reasoning_traces)
            conclusion_trace = self._add_reasoning_step(
                ReasoningStep.CONCLUSION,
                f"Final recommendation: {final_recommendations.get('primary_recommendation', 'Hold')} "
                f"(Confidence: {final_recommendations.get('confidence_level', 0.5):.1%}). "
                f"Key reasons: {', '.join(final_recommendations.get('key_reasons', ['Standard analysis']))}",
                reasoning_traces,
                data=final_recommendations,
                confidence=final_recommendations.get('confidence_level', 0.5)
            )
            
            # Store reasoning pattern for future learning
            self._store_reasoning_pattern(query, reasoning_traces, analysis_results)
            
            # Prepare comprehensive response
            response_data = {
                'success': True,
                'dataframe': df.to_dict('records'),
                'dataframe_info': {
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'memory_usage': df.memory_usage(deep=True).sum(),
                    'null_counts': df.isnull().sum().to_dict()
                },
                'calculations': analysis_results.get('calculations', {}),
                'calculation_type': analysis_strategy['strategy'],
                'insights': analysis_results.get('insights', []),
                'reasoning_traces': [self._serialize_reasoning_trace(trace) for trace in reasoning_traces],
                'investment_thesis': final_recommendations,
                'analysis_confidence': final_recommendations.get('confidence_level', 0.5),
                'query': query,
                'original_sql_data': sql_data,
                'reasoning_session_id': reasoning_session_id
            }
            
            logger.info(f"✅ ReAct reasoning analysis completed successfully [Session: {reasoning_session_id}]")
            logger.info(f"🎯 Final recommendation: {final_recommendations.get('primary_recommendation', 'Hold')} "
                       f"(Confidence: {final_recommendations.get('confidence_level', 0.5):.1%})")
            
            return response_data
            
        except Exception as e:
            error_trace = self._add_reasoning_step(
                ReasoningStep.OBSERVATION,
                f"Critical error during ReAct analysis: {str(e)}. Falling back to basic analysis.",
                reasoning_traces,
                confidence=0.0
            )
            logger.error(f"❌ ReAct reasoning analysis failed: {e}")
            return self._create_error_response(str(e), query, reasoning_traces)
    
    def _add_reasoning_step(self, step_type: ReasoningStep, content: str, traces: List[ReasoningTrace], 
                           data: Optional[Dict[str, Any]] = None, confidence: float = 0.7) -> ReasoningTrace:
        """Add a reasoning step to the trace and log it."""
        trace = ReasoningTrace(
            step_type=step_type,
            content=content,
            data=data,
            confidence=confidence
        )
        traces.append(trace)
        logger.info(f"🧠 {step_type.value.upper()}: {content}")
        return trace
    
    def _determine_analysis_strategy(self, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Determine the optimal analysis strategy based on query and data characteristics."""
        query_lower = query.lower()
        strategy = {
            'strategy': 'comprehensive_analysis',
            'components': [],
            'confidence': 0.7,
            'reasoning': ''
        }
        
        # Analyze query intent
        if any(keyword in query_lower for keyword in ['risk', 'volatility', 'sharpe', 'drawdown', 'beta']):
            strategy['components'].append('risk_assessment')
            strategy['reasoning'] += 'Risk-related keywords detected. '
        
        if any(keyword in query_lower for keyword in ['performance', 'return', 'growth', 'profit']):
            strategy['components'].append('performance_analysis')
            strategy['reasoning'] += 'Performance analysis keywords detected. '
        
        if any(keyword in query_lower for keyword in ['compare', 'vs', 'versus', 'best', 'worst']):
            strategy['components'].append('comparative_analysis')
            strategy['reasoning'] += 'Comparative analysis keywords detected. '
        
        if any(keyword in query_lower for keyword in ['recommend', 'invest', 'buy', 'sell', 'advice']):
            strategy['components'].append('investment_thesis')
            strategy['reasoning'] += 'Investment recommendation requested. '
        
        # Analyze data characteristics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 2:
            strategy['components'].append('correlation_analysis')
            strategy['reasoning'] += 'Multiple numeric columns available for correlation analysis. '
        
        if df.shape[0] > 10:
            strategy['components'].append('statistical_analysis')
            strategy['reasoning'] += 'Sufficient data points for statistical analysis. '
        
        # Default components if none detected
        if not strategy['components']:
            strategy['components'] = ['basic_analysis', 'statistical_summary']
            strategy['strategy'] = 'basic_analysis'
            strategy['confidence'] = 0.5
            strategy['reasoning'] = 'No specific analysis type detected, using basic analysis. '
        else:
            strategy['strategy'] = 'comprehensive_analysis'
            strategy['confidence'] = min(0.9, 0.6 + len(strategy['components']) * 0.1)
        
        return strategy
    
    def _execute_comprehensive_analysis(self, df: pd.DataFrame, query: str, 
                                      strategy: Dict[str, Any], traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """Execute comprehensive financial analysis based on the determined strategy."""
        results = {
            'calculations': {},
            'insights': [],
            'key_findings': '',
            'investment_implications': '',
            'analysis_confidence': 0.7,
            'reflection_data': {}
        }
        
        components = strategy.get('components', [])
        
        # Execute risk assessment
        if 'risk_assessment' in components:
            self._add_reasoning_step(
                ReasoningStep.ACTION,
                "Executing comprehensive risk assessment using advanced financial metrics.",
                traces
            )
            risk_profile = self.financial_tools.assess_risk_profile(df)
            results['calculations']['risk_profile'] = risk_profile
            results['insights'].extend(self._generate_risk_insights(risk_profile))
        
        # Execute performance analysis
        if 'performance_analysis' in components:
            self._add_reasoning_step(
                ReasoningStep.ACTION,
                "Analyzing performance metrics with market context and trend analysis.",
                traces
            )
            performance_context = self.financial_tools.analyze_performance_context(df)
            results['calculations']['performance_context'] = performance_context
            results['insights'].extend(self._generate_performance_insights(performance_context))
        
        # Execute comparative analysis
        if 'comparative_analysis' in components:
            self._add_reasoning_step(
                ReasoningStep.ACTION,
                "Performing comparative analysis to identify best and worst performers.",
                traces
            )
            comparison_results = self._perform_comparative_analysis(df)
            results['calculations']['comparison_analysis'] = comparison_results
            results['insights'].extend(self._generate_comparison_insights(comparison_results))
        
        # Execute correlation analysis
        if 'correlation_analysis' in components:
            self._add_reasoning_step(
                ReasoningStep.ACTION,
                "Analyzing correlations between different financial metrics.",
                traces
            )
            correlation_results = self._perform_correlation_analysis(df)
            results['calculations']['correlation_analysis'] = correlation_results
            results['insights'].extend(self._generate_correlation_insights(correlation_results))
        
        # Execute statistical analysis
        if 'statistical_analysis' in components:
            self._add_reasoning_step(
                ReasoningStep.ACTION,
                "Computing comprehensive statistical metrics and distributions.",
                traces
            )
            statistical_results = self._perform_statistical_analysis(df)
            results['calculations']['statistical_analysis'] = statistical_results
            results['insights'].extend(self._generate_statistical_insights(statistical_results))
        
        # Generate key findings
        results['key_findings'] = self._synthesize_key_findings(results['calculations'])
        results['investment_implications'] = self._derive_investment_implications(results['calculations'])
        results['analysis_confidence'] = self._calculate_analysis_confidence(results['calculations'])
        
        return results
    
    def _generate_final_recommendations(self, analysis_results: Dict[str, Any], query: str, 
                                      traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """Generate final investment recommendations based on comprehensive analysis."""
        calculations = analysis_results.get('calculations', {})
        
        # Extract key components for recommendation
        risk_profile = calculations.get('risk_profile', {})
        performance_context = calculations.get('performance_context', {})
        
        # Generate investment thesis using financial tools
        if risk_profile and performance_context:
            investment_thesis = self.financial_tools.generate_investment_thesis(
                risk_profile, performance_context
            )
        else:
            investment_thesis = {
                'investment_recommendation': 'Hold',
                'confidence_level': 0.5,
                'key_strengths': ['Basic analysis completed'],
                'key_concerns': ['Limited data for comprehensive analysis'],
                'market_suitability': {},
                'strategic_considerations': []
            }
        
        # Enhance with additional reasoning
        key_reasons = []
        if investment_thesis.get('key_strengths'):
            key_reasons.extend(investment_thesis['key_strengths'][:3])  # Top 3 strengths
        if investment_thesis.get('key_concerns'):
            key_reasons.extend([f"Concern: {concern}" for concern in investment_thesis['key_concerns'][:2]])  # Top 2 concerns
        
        final_recommendations = {
            'primary_recommendation': investment_thesis.get('investment_recommendation', 'Hold'),
            'confidence_level': investment_thesis.get('confidence_level', 0.5),
            'key_reasons': key_reasons,
            'detailed_thesis': investment_thesis,
            'risk_assessment': risk_profile.get('risk_category', 'Unknown'),
            'suitability_score': self._calculate_suitability_score(calculations),
            'strategic_outlook': self._generate_strategic_outlook(calculations)
        }
        
        return final_recommendations
    
    def _store_reasoning_pattern(self, query: str, traces: List[ReasoningTrace], results: Dict[str, Any]):
        """Store reasoning patterns for future learning and improvement."""
        pattern_key = self._generate_pattern_key(query)
        self.reasoning_memory[pattern_key] = {
            'query_pattern': query,
            'reasoning_steps': len(traces),
            'analysis_confidence': results.get('analysis_confidence', 0.5),
            'successful_components': list(results.get('calculations', {}).keys()),
            'timestamp': datetime.now(),
            'performance_score': self._calculate_reasoning_performance(traces, results)
        }
        
        # Keep only recent patterns (last 100)
        if len(self.reasoning_memory) > 100:
            oldest_key = min(self.reasoning_memory.keys(), 
                           key=lambda k: self.reasoning_memory[k]['timestamp'])
            del self.reasoning_memory[oldest_key]
    
    def _serialize_reasoning_trace(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """Serialize reasoning trace for JSON response."""
        return {
            'step_type': trace.step_type.value,
            'content': trace.content,
            'confidence': trace.confidence,
            'timestamp': trace.timestamp.isoformat(),
            'data_available': trace.data is not None
        }
    
    def _create_error_response(self, error_msg: str, query: str, traces: List[ReasoningTrace]) -> Dict[str, Any]:
        """Create error response with reasoning traces."""
        return {
            'success': False,
            'error': error_msg,
            'calculations': {},
            'dataframe_info': {},
            'query': query,
            'reasoning_traces': [self._serialize_reasoning_trace(trace) for trace in traces],
            'analysis_confidence': 0.0
        }
    
    def _create_dataframe(self, raw_data: List[List[Any]]) -> Optional[pd.DataFrame]:
        """
        Convert raw SQL data to pandas DataFrame.
        
        Args:
            raw_data: List of rows from SQL results
            
        Returns:
            Pandas DataFrame or None if conversion fails
        """
        try:
            if not raw_data:
                return None
            
            # Smart column detection for DataFrame creation
            if len(raw_data) > 0:
                num_cols = len(raw_data[0])
                
                # Try to determine if first row contains headers
                first_row = raw_data[0]
                if all(isinstance(cell, str) and not self._is_numeric_string(cell) for cell in first_row):
                    # First row likely contains column names
                    if len(raw_data) > 1:
                        columns = first_row
                        data = raw_data[1:]
                        df = pd.DataFrame(data, columns=columns)
                    else:
                        # Only header row, create empty DataFrame
                        df = pd.DataFrame(columns=first_row)
                else:
                    # Generate generic column names
                    if num_cols == 2:
                        columns = ['category', 'value']
                    else:
                        columns = [f'col_{i}' for i in range(num_cols)]
                    df = pd.DataFrame(raw_data, columns=columns)
                
                # Convert numeric columns
                df = self._convert_numeric_columns(df)
                
                logger.info(f"🐼 DataFrame created successfully: {df.shape}")
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating DataFrame: {e}")
            return None
    
    def _is_numeric_string(self, value: str) -> bool:
        """Check if a string represents a numeric value."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert string columns to numeric where possible."""
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                numeric_series = pd.to_numeric(df[col], errors='ignore')
                if not numeric_series.equals(df[col]):
                    df[col] = numeric_series
                    logger.debug(f"Converted column {col} to numeric")
        return df
    
    def _detect_calculation_type(self, query: str) -> Optional[str]:
        """
        Detect the type of calculation required based on the query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Calculation type string or None
        """
        query_lower = query.lower()
        
        # Financial risk calculations
        risk_keywords = ['risk', 'volatility', 'sharpe', 'beta', 'var', 'standard deviation', 'drawdown']
        if any(keyword in query_lower for keyword in risk_keywords):
            return 'risk_analysis'
        
        # Performance calculations
        performance_keywords = ['return', 'performance', 'growth', 'roi', 'gains', 'profit']
        if any(keyword in query_lower for keyword in performance_keywords):
            return 'performance_analysis'
        
        # Correlation analysis
        correlation_keywords = ['correlation', 'relationship', 'connected', 'correlated']
        if any(keyword in query_lower for keyword in correlation_keywords):
            return 'correlation_analysis'
        
        # Statistical analysis
        stats_keywords = ['average', 'mean', 'median', 'summary', 'statistics', 'stats']
        if any(keyword in query_lower for keyword in stats_keywords):
            return 'statistical_analysis'
        
        # Comparison analysis
        comparison_keywords = ['compare', 'vs', 'versus', 'against', 'difference', 'better', 'worse']
        if any(keyword in query_lower for keyword in comparison_keywords):
            return 'comparison_analysis'
        
        return None
    
    def _perform_calculations(self, df: pd.DataFrame, calc_type: str, query: str) -> Dict[str, Any]:
        """Perform calculations on the DataFrame based on the calculation type."""
        try:
            results = {}
            
            if calc_type == 'risk_analysis':
                results = self._calculate_risk_metrics(df)
            elif calc_type == 'performance_analysis':
                results = self._calculate_performance_metrics(df)
            elif calc_type == 'correlation_analysis':
                results = self._calculate_correlation_metrics(df)
            elif calc_type == 'statistical_analysis':
                results = self._calculate_statistical_metrics(df)
            elif calc_type == 'comparison_analysis':
                results = self._calculate_comparison_metrics(df)
            
            return results
            
        except Exception as e:
            logger.error(f"Calculation failed for {calc_type}: {e}")
            return {}
    
    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate financial risk metrics."""
        results = {}
        
        # Look for numeric columns that could represent returns or values
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                if 'return' in col.lower() or 'price' in col.lower() or 'value' in col.lower():
                    data = df[col].dropna()
                    
                    if len(data) > 1:
                        results[f'{col}_volatility'] = data.std()
                        results[f'{col}_mean_return'] = data.mean()
                        
                        # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
                        if data.std() != 0:
                            results[f'{col}_sharpe_ratio'] = data.mean() / data.std()
                        
                        # Max drawdown
                        if 'price' in col.lower() or 'value' in col.lower():
                            running_max = data.expanding().max()
                            drawdown = (data - running_max) / running_max
                            results[f'{col}_max_drawdown'] = drawdown.min()
        
        return results
    
    def _calculate_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics."""
        results = {}
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            
            if len(data) > 0:
                results[f'{col}_total'] = data.sum()
                results[f'{col}_average'] = data.mean()
                results[f'{col}_max'] = data.max()
                results[f'{col}_min'] = data.min()
                
                # Growth rate (if we have time series data)
                if len(data) > 1:
                    first_value = data.iloc[0]
                    last_value = data.iloc[-1]
                    if first_value != 0:
                        results[f'{col}_total_growth'] = ((last_value - first_value) / first_value) * 100
        
        return results
    
    def _calculate_correlation_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation metrics."""
        results = {}
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) > 1:
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr()
            
            # Find top correlations (excluding self-correlations)
            correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    correlation = corr_matrix.iloc[i, j]
                    
                    if not np.isnan(correlation):
                        correlations.append({
                            'pair': f"{col1} vs {col2}",
                            'correlation': correlation,
                            'strength': 'Strong' if abs(correlation) > 0.7 else 'Moderate' if abs(correlation) > 0.3 else 'Weak'
                        })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            results['top_correlations'] = correlations[:10]  # Top 10 correlations
            results['correlation_matrix'] = corr_matrix.to_dict()
        
        return results
    
    def _calculate_statistical_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical metrics."""
        results = {}
        
        # Basic statistics
        results['total_records'] = len(df)
        results['total_columns'] = len(df.columns)
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 0:
                results[f'{col}_mean'] = data.mean()
                results[f'{col}_median'] = data.median()
                results[f'{col}_std'] = data.std()
                results[f'{col}_min'] = data.min()
                results[f'{col}_max'] = data.max()
                results[f'{col}_q25'] = data.quantile(0.25)
                results[f'{col}_q75'] = data.quantile(0.75)
                results[f'{col}_skewness'] = data.skew()
                results[f'{col}_kurtosis'] = data.kurtosis()
        
        return results
    
    def _calculate_comparison_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comparison metrics."""
        results = {}
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) > 0:
            # Find best and worst performers for each numeric column
            for col in numeric_cols:
                data = df[col].dropna()
                if len(data) > 0:
                    max_idx = data.idxmax()
                    min_idx = data.idxmin()
                    
                    # Try to get category names if available
                    category_col = None
                    for potential_cat_col in df.columns:
                        if potential_cat_col != col and df[potential_cat_col].dtype == 'object':
                            category_col = potential_cat_col
                            break
                    
                    if category_col:
                        results['best_performer'] = df.loc[max_idx, category_col]
                        results['best_performer_value'] = data.max()
                        results['worst_performer'] = df.loc[min_idx, category_col]
                        results['worst_performer_value'] = data.min()
                    else:
                        results['best_performer'] = f"Row {max_idx}"
                        results['best_performer_value'] = data.max()
                        results['worst_performer'] = f"Row {min_idx}"
                        results['worst_performer_value'] = data.min()
                    
                    break  # Only do this for the first numeric column
        
        return results
    
    def _generate_insights(self, df: pd.DataFrame, calculations: Dict[str, Any], 
                          calc_type: Optional[str], query: str) -> List[str]:
        """Generate insights based on the calculations performed."""
        insights = []
        
        if not calculations or not calc_type:
            return insights
        
        try:
            if calc_type == 'risk_analysis':
                insights.append("## 🎯 **Risk Analysis Results**\n")
                risk_items = []
                for key, value in calculations.items():
                    if 'sharpe_ratio' in key:
                        col_name = key.replace('_sharpe_ratio', '').replace('_', ' ').title()
                        if value > 1:
                            risk_items.append(f"• 🟢 **{col_name}** has excellent risk-adjusted returns (Sharpe: ***{value:.2f}***)")
                        elif value > 0.5:
                            risk_items.append(f"• 🟡 **{col_name}** has good risk-adjusted returns (Sharpe: ***{value:.2f}***)")
                        else:
                            risk_items.append(f"• 🔴 **{col_name}** has poor risk-adjusted returns (Sharpe: ***{value:.2f}***)")
                    elif 'volatility' in key:
                        col_name = key.replace('_volatility', '').replace('_', ' ').title()
                        risk_items.append(f"• 📊 **{col_name}** volatility: ***{value:.2f}%***")
                    elif 'max_drawdown' in key:
                        risk_items.append(f"• 📉 **Maximum drawdown**: ***{value:.2%}***")
                
                if risk_items:
                    insights.extend(risk_items)
            
            elif calc_type == 'performance_analysis':
                insights.append("## 📈 **Performance Analysis Results**\n")
                perf_items = []
                for key, value in calculations.items():
                    if 'total_growth' in key:
                        col_name = key.replace('_total_growth', '').replace('_', ' ').title()
                        if value > 0:
                            perf_items.append(f"• 📈 **{col_name}** gained ***{value:.1f}%*** over the period")
                        else:
                            perf_items.append(f"• 📉 **{col_name}** declined ***{abs(value):.1f}%*** over the period")
                    elif 'average' in key:
                        col_name = key.replace('_average', '').replace('_', ' ').title()
                        perf_items.append(f"• 📊 **Average {col_name}**: ***{value:.2f}***")
                
                if perf_items:
                    insights.extend(perf_items)
            
            elif calc_type == 'comparison_analysis':
                insights.append("## 🏆 **Comparison Analysis Results**\n")
                comp_items = []
                if 'best_performer' in calculations:
                    best = calculations['best_performer']
                    best_value = calculations.get('best_performer_value', 0)
                    worst = calculations.get('worst_performer', '')
                    worst_value = calculations.get('worst_performer_value', 0)
                    
                    comp_items.append(f"• 🏆 **Best performer**: ***{best}*** ({best_value:.2f})")
                    if worst:
                        comp_items.append(f"• 📉 **Worst performer**: ***{worst}*** ({worst_value:.2f})")
                
                if comp_items:
                    insights.extend(comp_items)
            
            elif calc_type == 'statistical_analysis':
                insights.append("## 📊 **Statistical Analysis Results**\n")
                stat_items = []
                if 'total_records' in calculations:
                    stat_items.append(f"• 📊 **Dataset size**: ***{calculations['total_records']:,} records***")
                
                for key, value in calculations.items():
                    if 'mean' in key and not key.startswith('total'):
                        col_name = key.replace('_mean', '').replace('_', ' ').title()
                        stat_items.append(f"• 📈 **Average {col_name}**: ***{value:.2f}***")
                
                if stat_items:
                    insights.extend(stat_items)
            
            elif calc_type == 'correlation_analysis':
                insights.append("## 🔗 **Correlation Analysis Results**\n")
                if 'top_correlations' in calculations:
                    correlations = calculations['top_correlations']
                    if correlations:
                        insights.append("### **Strongest Correlations:**\n")
                        for i, corr in enumerate(correlations[:5], 1):  # Top 5
                            strength = "**Strong**" if abs(corr['correlation']) > 0.7 else "*Moderate*" if abs(corr['correlation']) > 0.3 else "Weak"
                            insights.append(f"{i}. {corr['pair']}: {strength} correlation (***{corr['correlation']:.3f}***)")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights.append("Analysis completed successfully.")
        
        return insights

    # ============ REACT FRAMEWORK HELPER METHODS ============
    
    def _perform_comparative_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comparative analysis to identify best and worst performers."""
        results = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                data = df[col].dropna()
                if len(data) > 0:
                    max_idx = data.idxmax()
                    min_idx = data.idxmin()
                    
                    # Try to get category names
                    category_col = None
                    for potential_cat_col in df.columns:
                        if potential_cat_col != col and df[potential_cat_col].dtype == 'object':
                            category_col = potential_cat_col
                            break
                    
                    if category_col:
                        results['best_performer'] = df.loc[max_idx, category_col]
                        results['best_performer_value'] = data.max()
                        results['worst_performer'] = df.loc[min_idx, category_col]
                        results['worst_performer_value'] = data.min()
                    else:
                        results['best_performer'] = f"Row {max_idx}"
                        results['best_performer_value'] = data.max()
                        results['worst_performer'] = f"Row {min_idx}"
                        results['worst_performer_value'] = data.min()
                    
                    break  # Only analyze first numeric column
        
        return results
    
    def _synthesize_key_findings(self, calculations: Dict[str, Any]) -> str:
        """Synthesize key findings from all calculations."""
        findings = []
        
        # Risk findings
        risk_profile = calculations.get('risk_profile', {})
        if risk_profile:
            risk_category = risk_profile.get('risk_category', 'Unknown')
            findings.append(f"Risk Profile: {risk_category}")
        
        # Performance findings
        performance_context = calculations.get('performance_context', {})
        if performance_context:
            trend_analysis = performance_context.get('trend_analysis', {})
            upward_trends = sum(1 for trend in trend_analysis.values() if trend.get('trend_direction') == 'Upward')
            if upward_trends > 0:
                findings.append(f"{upward_trends} metrics showing upward trends")
        
        return "; ".join(findings) if findings else "Standard quantitative analysis completed"
    
    def _perform_correlation_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform correlation analysis on the DataFrame."""
        return self._calculate_correlation_metrics(df)
    
    def _generate_correlation_insights(self, correlation_results: Dict[str, Any]) -> List[str]:
        """Generate insights from correlation analysis."""
        insights = []
        
        top_correlations = correlation_results.get('top_correlations', [])
        if top_correlations:
            for corr in top_correlations[:3]:  # Top 3 correlations
                pair = corr['pair']
                correlation = corr['correlation']
                strength = corr['strength']
                
                if correlation > 0.7:
                    insights.append(f"Strong positive correlation ({correlation:.2f}) between {pair}")
                elif correlation < -0.7:
                    insights.append(f"Strong negative correlation ({correlation:.2f}) between {pair}")
                elif abs(correlation) > 0.3:
                    insights.append(f"{strength} correlation ({correlation:.2f}) between {pair}")
        
        return insights
    
    def _derive_investment_implications(self, calculations: Dict[str, Any]) -> Dict[str, Any]:
        """Derive investment implications from the analysis."""
        implications = {
            'risk_level': 'Moderate',
            'investment_horizon': 'Medium to Long Term',
            'suitability': 'Moderate Risk Investors',
            'key_considerations': []
        }
        
        # Analyze risk metrics
        risk_assessment = calculations.get('risk_assessment', {})
        if risk_assessment:
            volatility = risk_assessment.get('volatility_analysis', {})
            if volatility:
                avg_volatility = volatility.get('average_volatility', 0)
                if avg_volatility > 20:
                    implications['risk_level'] = 'High'
                    implications['suitability'] = 'High Risk Tolerance Investors'
                elif avg_volatility < 10:
                    implications['risk_level'] = 'Low'
                    implications['suitability'] = 'Conservative Investors'
        
        # Analyze performance context
        performance_context = calculations.get('performance_context', {})
        if performance_context:
            trend_analysis = performance_context.get('trend_analysis', {})
            upward_trends = sum(1 for trend in trend_analysis.values() if trend.get('trend_direction') == 'Upward')
            total_trends = len(trend_analysis)
            
            if total_trends > 0:
                trend_ratio = upward_trends / total_trends
                if trend_ratio > 0.7:
                    implications['key_considerations'].append('Strong positive momentum across multiple metrics')
                elif trend_ratio < 0.3:
                    implications['key_considerations'].append('Concerning downward trends in key metrics')
        
        # Default considerations for small cap funds
        implications['key_considerations'].extend([
            'Small cap funds are typically more volatile than large cap funds',
            'Consider diversification across market capitalizations',
            'Regular monitoring recommended due to higher volatility'
        ])
        
        return implications
    
    def _calculate_analysis_confidence(self, calculations: Dict[str, Any]) -> float:
        """Calculate confidence level in the analysis based on data quality and completeness."""
        confidence_factors = []
        
        # Data completeness factor
        total_calculations = len(calculations)
        if total_calculations > 0:
            confidence_factors.append(min(total_calculations / 5.0, 1.0))  # Max confidence at 5+ calculations
        
        # Risk assessment completeness
        risk_assessment = calculations.get('risk_assessment', {})
        if risk_assessment:
            risk_metrics = len(risk_assessment)
            confidence_factors.append(min(risk_metrics / 3.0, 1.0))  # Max confidence at 3+ risk metrics
        
        # Performance context completeness
        performance_context = calculations.get('performance_context', {})
        if performance_context:
            perf_metrics = len(performance_context)
            confidence_factors.append(min(perf_metrics / 3.0, 1.0))  # Max confidence at 3+ performance metrics
        
        # Correlation analysis completeness
        correlation_analysis = calculations.get('correlation_analysis', {})
        if correlation_analysis and correlation_analysis.get('top_correlations'):
            confidence_factors.append(0.8)  # High confidence if correlations found
        
        # Calculate weighted average confidence
        if confidence_factors:
            base_confidence = sum(confidence_factors) / len(confidence_factors)
            
            # Adjust for synthetic data (lower confidence)
            if total_calculations == 1:  # Likely synthetic data
                base_confidence *= 0.7
            
            return min(max(base_confidence, 0.3), 0.95)  # Clamp between 30% and 95%
        
        return 0.5  # Default moderate confidence
    
    def _calculate_suitability_score(self, calculations: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """Calculate investment suitability score based on analysis and query context."""
        suitability = {
            'overall_score': 0.6,  # Default moderate suitability
            'risk_score': 0.5,
            'performance_score': 0.5,
            'recommendation': 'Hold',
            'confidence_level': 0.6,
            'reasoning': []
        }
        
        # Analyze risk factors
        risk_assessment = calculations.get('risk_assessment', {})
        if risk_assessment:
            volatility = risk_assessment.get('volatility_analysis', {})
            if volatility:
                avg_volatility = volatility.get('average_volatility', 15)
                if avg_volatility > 25:
                    suitability['risk_score'] = 0.3  # High risk
                    suitability['reasoning'].append('High volatility detected - suitable for aggressive investors only')
                elif avg_volatility < 10:
                    suitability['risk_score'] = 0.8  # Low risk
                    suitability['reasoning'].append('Low volatility - suitable for conservative investors')
                else:
                    suitability['risk_score'] = 0.6  # Moderate risk
                    suitability['reasoning'].append('Moderate volatility - suitable for balanced investors')
        
        # Analyze performance trends
        performance_context = calculations.get('performance_context', {})
        if performance_context:
            trend_analysis = performance_context.get('trend_analysis', {})
            upward_trends = sum(1 for trend in trend_analysis.values() if trend.get('trend_direction') == 'Upward')
            total_trends = len(trend_analysis)
            
            if total_trends > 0:
                trend_ratio = upward_trends / total_trends
                if trend_ratio > 0.7:
                    suitability['performance_score'] = 0.8
                    suitability['recommendation'] = 'Buy'
                    suitability['reasoning'].append('Strong positive performance trends detected')
                elif trend_ratio < 0.3:
                    suitability['performance_score'] = 0.3
                    suitability['recommendation'] = 'Sell'
                    suitability['reasoning'].append('Concerning negative performance trends')
        
        # Calculate overall score
        suitability['overall_score'] = (suitability['risk_score'] + suitability['performance_score']) / 2
        
        # Determine final recommendation based on overall score
        if suitability['overall_score'] > 0.7:
            suitability['recommendation'] = 'Buy'
        elif suitability['overall_score'] < 0.4:
            suitability['recommendation'] = 'Sell'
        else:
            suitability['recommendation'] = 'Hold'
        
        # Set confidence based on data quality
        suitability['confidence_level'] = self._calculate_analysis_confidence(calculations)
        
        return suitability
    
    def _generate_strategic_outlook(self, calculations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic investment outlook based on analysis."""
        outlook = {
            'market_suitability': 'Neutral',
            'time_horizon': 'Medium Term (3-5 years)',
            'key_factors': [],
            'market_conditions': 'Stable',
            'strategic_recommendations': []
        }
        
        # Analyze performance trends for market suitability
        performance_context = calculations.get('performance_context', {})
        if performance_context:
            trend_analysis = performance_context.get('trend_analysis', {})
            upward_trends = sum(1 for trend in trend_analysis.values() if trend.get('trend_direction') == 'Upward')
            total_trends = len(trend_analysis)
            
            if total_trends > 0:
                trend_ratio = upward_trends / total_trends
                if trend_ratio > 0.6:
                    outlook['market_suitability'] = 'Favorable'
                    outlook['market_conditions'] = 'Bullish'
                    outlook['key_factors'].append('Strong positive momentum in key metrics')
                elif trend_ratio < 0.4:
                    outlook['market_suitability'] = 'Challenging'
                    outlook['market_conditions'] = 'Bearish'
                    outlook['key_factors'].append('Concerning downward trends in performance')
        
        # Risk-based strategic recommendations
        risk_assessment = calculations.get('risk_assessment', {})
        if risk_assessment:
            volatility = risk_assessment.get('volatility_analysis', {})
            if volatility:
                avg_volatility = volatility.get('average_volatility', 15)
                if avg_volatility > 20:
                    outlook['strategic_recommendations'].extend([
                        'Consider dollar-cost averaging to reduce timing risk',
                        'Maintain smaller position size due to high volatility',
                        'Monitor closely for exit opportunities'
                    ])
                else:
                    outlook['strategic_recommendations'].extend([
                        'Suitable for core portfolio allocation',
                        'Consider systematic investment approach'
                    ])
        
        # Default strategic recommendations for small cap funds
        outlook['strategic_recommendations'].extend([
            'Diversify across market capitalizations',
            'Regular portfolio rebalancing recommended',
            'Consider economic cycle timing for entry/exit'
        ])
        
        outlook['key_factors'].extend([
            'Small cap segment typically outperforms in economic recovery phases',
            'Higher volatility requires longer investment horizon',
            'Liquidity considerations during market stress'
        ])
        
        return outlook
    
    def _generate_pattern_key(self, calculations: Dict[str, Any]) -> str:
        """Generate a unique pattern key for caching and learning purposes."""
        import hashlib
        
        # Create a pattern signature based on key calculation results
        pattern_elements = []
        
        # Add risk assessment signature
        risk_assessment = calculations.get('risk_assessment', {})
        if risk_assessment:
            volatility = risk_assessment.get('volatility_analysis', {})
            if volatility:
                avg_vol = volatility.get('average_volatility', 0)
                pattern_elements.append(f"vol_{int(avg_vol/5)*5}")  # Bucket volatility in 5% ranges
        
        # Add performance context signature
        performance_context = calculations.get('performance_context', {})
        if performance_context:
            trend_analysis = performance_context.get('trend_analysis', {})
            upward_trends = sum(1 for trend in trend_analysis.values() if trend.get('trend_direction') == 'Upward')
            total_trends = len(trend_analysis)
            if total_trends > 0:
                trend_ratio = upward_trends / total_trends
                pattern_elements.append(f"trend_{int(trend_ratio*10)}")  # Bucket trend ratio
        
        # Add correlation signature
        correlation_analysis = calculations.get('correlation_analysis', {})
        if correlation_analysis:
            top_correlations = correlation_analysis.get('top_correlations', [])
            if top_correlations:
                strong_corr_count = sum(1 for corr in top_correlations if abs(corr.get('correlation', 0)) > 0.7)
                pattern_elements.append(f"corr_{strong_corr_count}")
        
        # Create pattern key
        if pattern_elements:
            pattern_string = "_".join(pattern_elements)
            return hashlib.md5(pattern_string.encode()).hexdigest()[:8]
        
        return "default_pattern"
