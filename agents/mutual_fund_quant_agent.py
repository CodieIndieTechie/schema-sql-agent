#!/usr/bin/env python3
"""
Mutual Fund Quant Agent - Financial calculations and quantitative analysis

This agent handles:
- Pandas DataFrame operations and transformations
- Complex financial calculations (risk, performance, correlation)
- Quantitative analysis and metrics computation
- Statistical analysis and insights generation
"""

import logging
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MutualFundQuantAgent:
    """
    Mutual Fund Quant Agent focused on quantitative analysis and calculations.
    
    Responsibilities:
    - Converting SQL data to pandas DataFrames
    - Performing complex financial calculations
    - Risk analysis, performance metrics, correlation analysis
    - Statistical analysis and insights generation
    """
    
    def __init__(self):
        """Initialize the Mutual Fund Quant Agent."""
        self.calculation_cache = {}
        logger.info("🧮 Mutual Fund Quant Agent initialized")
    
    def process_data(self, sql_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Process SQL data and perform quantitative analysis.
        
        Args:
            sql_data: Data from Enhanced SQL Agent
            query: Original user query for context
            
        Returns:
            Dictionary containing calculations and analysis results
        """
        try:
            logger.info("🧮 Starting quantitative analysis")
            
            # Extract raw data
            raw_data = sql_data.get('sql_data', [])
            if not raw_data:
                logger.warning("No data received for analysis")
                return {
                    'success': False,
                    'error': 'No data available for analysis',
                    'calculations': {},
                    'dataframe_info': {},
                    'query': query
                }
            
            # Convert to pandas DataFrame
            df = self._create_dataframe(raw_data)
            if df is None or df.empty:
                logger.warning("Failed to create DataFrame or DataFrame is empty")
                return {
                    'success': False,
                    'error': 'Unable to process data into DataFrame',
                    'calculations': {},
                    'dataframe_info': {},
                    'query': query
                }
            
            logger.info(f"📊 DataFrame created: {df.shape} (rows x columns)")
            
            # Detect calculation type based on query
            calc_type = self._detect_calculation_type(query)
            logger.info(f"🔍 Detected calculation type: {calc_type}")
            
            # Perform calculations based on type
            calculations = {}
            if calc_type:
                calculations = self._perform_calculations(df, calc_type, query)
                logger.info(f"📈 Completed {calc_type} calculations: {len(calculations)} metrics")
            
            # Generate insights
            insights = self._generate_insights(df, calculations, calc_type, query)
            
            # Prepare response for Data Formatter Agent
            response_data = {
                'success': True,
                'dataframe': df.to_dict('records'),  # Convert DataFrame to dict for JSON serialization
                'dataframe_info': {
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'memory_usage': df.memory_usage(deep=True).sum(),
                    'null_counts': df.isnull().sum().to_dict()
                },
                'calculations': calculations,
                'calculation_type': calc_type,
                'insights': insights,
                'query': query,
                'original_sql_data': sql_data
            }
            
            logger.info("✅ Quantitative analysis completed successfully")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Quantitative analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'calculations': {},
                'dataframe_info': {},
                'query': query
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
