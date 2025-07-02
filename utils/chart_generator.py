#!/usr/bin/env python3
"""
Dynamic Chart Generator

Generates interactive charts from SQL query results using Plotly.
"""

import logging
import plotly.graph_objs as go
import plotly.express as px
from plotly.io import to_html
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import uuid
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generates interactive charts from SQL data using Plotly."""
    
    def __init__(self, charts_dir: str = "static/charts"):
        """
        Initialize chart generator.
        
        Args:
            charts_dir: Directory to save chart HTML files
        """
        self.charts_dir = charts_dir
        os.makedirs(charts_dir, exist_ok=True)
        
    def generate_chart(
        self, 
        data: List[Dict[str, Any]], 
        columns: List[str],
        chart_type: str = "auto",
        title: str = "Chart"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a chart from SQL query results.
        
        Args:
            data: List of dictionaries representing rows
            columns: List of column names
            chart_type: Type of chart ('auto', 'bar', 'line', 'pie', 'scatter')
            title: Chart title
            
        Returns:
            Dictionary with chart info or None if generation failed
        """
        try:
            if not data or not columns:
                logger.warning("No data or columns provided for chart generation")
                return None
                
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(data)
            
            if df.empty:
                logger.warning("DataFrame is empty")
                return None
                
            # Auto-detect chart type if needed
            if chart_type == "auto":
                chart_type = self._detect_chart_type(df, columns)
                
            # Generate chart based on type
            fig = self._create_chart(df, chart_type, title)
            
            if fig is None:
                logger.warning(f"Failed to create chart of type: {chart_type}")
                return None
                
            # Save chart as HTML
            chart_id = str(uuid.uuid4())
            chart_filename = f"chart_{chart_id}.html"
            chart_path = os.path.join(self.charts_dir, chart_filename)
            
            # Configure chart for embedding
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
            }
            
            html_content = to_html(
                fig, 
                include_plotlyjs='cdn',
                config=config,
                div_id=f"chart-{chart_id}"
            )
            
            with open(chart_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"Chart generated successfully: {chart_filename}")
            
            return {
                "chart_id": chart_id,
                "chart_file": chart_filename,
                "chart_path": chart_path,
                "chart_type": chart_type,
                "title": title,
                "data_points": len(df),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate chart: {str(e)}")
            return None
    
    def _detect_chart_type(self, df: pd.DataFrame, columns: List[str]) -> str:
        """Auto-detect the best chart type for the data."""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            # Check for time series data
            if datetime_cols and numeric_cols:
                return "line"
                
            # Check for percentage/weight data (pie chart)
            if len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                numeric_col = numeric_cols[0]
                if any(keyword in numeric_col.lower() for keyword in ['weight', 'percent', 'share', 'allocation']):
                    return "pie"
                    
            # Check for comparison data (bar chart)
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                return "bar"
                
            # Check for correlation data (scatter)
            if len(numeric_cols) >= 2:
                return "scatter"
                
            # Default to bar chart
            return "bar"
            
        except Exception as e:
            logger.error(f"Error detecting chart type: {str(e)}")
            return "bar"
    
    def _create_chart(self, df: pd.DataFrame, chart_type: str, title: str) -> Optional[go.Figure]:
        """Create a Plotly figure based on chart type."""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if chart_type == "bar":
                return self._create_bar_chart(df, categorical_cols, numeric_cols, title)
            elif chart_type == "line":
                return self._create_line_chart(df, categorical_cols, numeric_cols, title)
            elif chart_type == "pie":
                return self._create_pie_chart(df, categorical_cols, numeric_cols, title)
            elif chart_type == "scatter":
                return self._create_scatter_chart(df, numeric_cols, title)
            else:
                logger.warning(f"Unknown chart type: {chart_type}, defaulting to bar")
                return self._create_bar_chart(df, categorical_cols, numeric_cols, title)
                
        except Exception as e:
            logger.error(f"Error creating {chart_type} chart: {str(e)}")
            return None
    
    def _create_bar_chart(self, df: pd.DataFrame, cat_cols: List[str], num_cols: List[str], title: str) -> Optional[go.Figure]:
        """Create a bar chart."""
        if not cat_cols or not num_cols:
            return None
            
        x_col = cat_cols[0]
        y_col = num_cols[0]
        
        # Limit to top 20 categories for readability
        if len(df) > 20:
            df = df.nlargest(20, y_col)
            
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()}
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            margin=dict(b=150)
        )
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame, cat_cols: List[str], num_cols: List[str], title: str) -> Optional[go.Figure]:
        """Create a line chart."""
        if not num_cols:
            return None
            
        x_col = cat_cols[0] if cat_cols else df.columns[0]
        y_col = num_cols[0]
        
        fig = px.line(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()}
        )
        
        fig.update_layout(height=500)
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, cat_cols: List[str], num_cols: List[str], title: str) -> Optional[go.Figure]:
        """Create a pie chart."""
        if not cat_cols or not num_cols:
            return None
            
        names_col = cat_cols[0]
        values_col = num_cols[0]
        
        # Limit to top 10 segments for readability
        if len(df) > 10:
            top_df = df.nlargest(9, values_col)
            others_sum = df.nsmallest(len(df) - 9, values_col)[values_col].sum()
            
            if others_sum > 0:
                others_row = pd.DataFrame({names_col: ['Others'], values_col: [others_sum]})
                df = pd.concat([top_df, others_row], ignore_index=True)
            else:
                df = top_df
        
        fig = px.pie(
            df, 
            names=names_col, 
            values=values_col,
            title=title
        )
        
        fig.update_layout(height=500)
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, num_cols: List[str], title: str) -> Optional[go.Figure]:
        """Create a scatter chart."""
        if len(num_cols) < 2:
            return None
            
        x_col = num_cols[0]
        y_col = num_cols[1]
        
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()}
        )
        
        fig.update_layout(height=500)
        return fig

# Global chart generator instance
chart_generator = ChartGenerator()
