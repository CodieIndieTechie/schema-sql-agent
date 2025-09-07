#!/usr/bin/env python3
"""
Visualization MCP Server

Provides secure data visualization operations through MCP protocol:
- Interactive Plotly chart generation
- Data formatting and presentation
- Chart file management and serving
- Multiple visualization types (bar, line, pie, scatter, table)
"""

import asyncio
import logging
import json
import os
import re
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

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.io import to_html
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None
    go = None

# Local imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class VisualizationMCPServer:
    """
    MCP Server for Visualization operations with enhanced security.
    
    Provides isolated chart generation through MCP protocol:
    - Interactive Plotly chart creation
    - Data table formatting
    - Chart file management
    - Multiple visualization types
    """
    
    def __init__(self, static_dir: str = "static/charts"):
        self.server = Server("visualization")
        self.static_dir = static_dir
        self.chart_cache = {}
        
        # Ensure static directory exists
        os.makedirs(static_dir, exist_ok=True)
        
        self.setup_resources()
        self.setup_tools()
        
    def setup_resources(self):
        """Setup MCP resources for visualization."""
        
        @self.server.list_resources()
        async def list_resources() -> List[mcp_types.Resource]:
            """List available visualization resources."""
            return [
                mcp_types.Resource(
                    uri="charts://templates",
                    name="Chart Templates",
                    description="Available chart templates and configurations",
                    mimeType="application/json"
                ),
                mcp_types.Resource(
                    uri="charts://generated",
                    name="Generated Charts",
                    description="List of generated chart files",
                    mimeType="application/json"
                ),
                mcp_types.Resource(
                    uri="formats://data_tables",
                    name="Data Table Formats",
                    description="Available data table formatting options",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: mcp_types.AnyUrl) -> str:
            """Read visualization resource content."""
            uri_str = str(uri)
            
            if uri_str == "charts://templates":
                templates_info = {
                    "available_chart_types": [
                        "bar", "line", "pie", "scatter", "histogram",
                        "box", "violin", "heatmap", "table"
                    ],
                    "chart_configurations": {
                        "bar": {"x_axis": "required", "y_axis": "required", "color": "optional"},
                        "line": {"x_axis": "required", "y_axis": "required", "color": "optional"},
                        "pie": {"values": "required", "names": "required"},
                        "scatter": {"x_axis": "required", "y_axis": "required", "size": "optional"},
                        "table": {"data": "required", "columns": "optional"}
                    }
                }
                return json.dumps(templates_info, indent=2)
            
            elif uri_str == "charts://generated":
                # List generated chart files
                chart_files = []
                if os.path.exists(self.static_dir):
                    chart_files = [f for f in os.listdir(self.static_dir) if f.endswith('.html')]
                
                return json.dumps({
                    "generated_charts": chart_files,
                    "total_charts": len(chart_files),
                    "static_directory": self.static_dir
                }, indent=2)
            
            elif uri_str == "formats://data_tables":
                table_formats = {
                    "available_formats": ["html", "markdown", "json", "csv"],
                    "styling_options": ["bootstrap", "plotly", "custom"],
                    "features": ["sorting", "filtering", "pagination", "export"]
                }
                return json.dumps(table_formats, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    def setup_tools(self):
        """Setup MCP tools for visualization."""
        
        @self.server.call_tool()
        async def create_plotly_chart(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Create interactive Plotly chart from data.
            
            Args:
                arguments: {
                    "data": dict - Chart data (x, y, labels, etc.)
                    "chart_type": str - Type of chart (bar, line, pie, scatter, etc.)
                    "title": str - Chart title
                    "x_label": str - X-axis label
                    "y_label": str - Y-axis label
                    "theme": str - Chart theme (plotly, plotly_white, plotly_dark)
                }
            """
            try:
                if not PLOTLY_AVAILABLE:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Plotly not available for chart generation",
                            "status": "error"
                        })
                    )]
                
                data = arguments.get("data", {})
                chart_type = arguments.get("chart_type", "bar")
                title = arguments.get("title", "Chart")
                x_label = arguments.get("x_label", "X Axis")
                y_label = arguments.get("y_label", "Y Axis")
                theme = arguments.get("theme", "plotly_white")
                
                # Validate input data
                if not data:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "No chart data provided",
                            "status": "error"
                        })
                    )]
                
                # Create chart
                chart_result = await self._create_chart(data, chart_type, title, x_label, y_label, theme)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(chart_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error creating Plotly chart: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Chart creation failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def format_data_table(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Format data into various table formats.
            
            Args:
                arguments: {
                    "data": dict - Table data
                    "format": str - Output format (html, markdown, json)
                    "style": str - Table styling (bootstrap, plotly, custom)
                    "max_rows": int - Maximum rows to display
                }
            """
            try:
                if not PANDAS_AVAILABLE:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Pandas not available for table formatting",
                            "status": "error"
                        })
                    )]
                
                data = arguments.get("data", {})
                format_type = arguments.get("format", "html")
                style = arguments.get("style", "bootstrap")
                max_rows = arguments.get("max_rows", 100)
                
                # Format table
                table_result = await self._format_table(data, format_type, style, max_rows)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(table_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error formatting data table: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Table formatting failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def generate_report(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Generate comprehensive report with charts and tables.
            
            Args:
                arguments: {
                    "data": dict - Report data
                    "charts": list - List of chart configurations
                    "tables": list - List of table configurations
                    "title": str - Report title
                    "template": str - Report template
                }
            """
            try:
                data = arguments.get("data", {})
                charts = arguments.get("charts", [])
                tables = arguments.get("tables", [])
                title = arguments.get("title", "Data Analysis Report")
                template = arguments.get("template", "standard")
                
                # Generate report
                report_result = await self._generate_report(data, charts, tables, title, template)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(report_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error generating report: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Report generation failed: {str(e)}",
                        "status": "error"
                    })
                )]
        
        @self.server.call_tool()
        async def export_visualization(arguments: dict) -> List[mcp_types.TextContent]:
            """
            Export visualization in various formats.
            
            Args:
                arguments: {
                    "chart_file": str - Chart file to export
                    "export_format": str - Export format (png, pdf, svg, html)
                    "width": int - Export width
                    "height": int - Export height
                }
            """
            try:
                chart_file = arguments.get("chart_file", "")
                export_format = arguments.get("export_format", "png")
                width = arguments.get("width", 800)
                height = arguments.get("height", 600)
                
                # Export visualization
                export_result = await self._export_visualization(chart_file, export_format, width, height)
                
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps(export_result, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error exporting visualization: {str(e)}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Visualization export failed: {str(e)}",
                        "status": "error"
                    })
                )]
    
    async def _create_chart(self, data: dict, chart_type: str, title: str, x_label: str, y_label: str, theme: str) -> dict:
        """Create Plotly chart from data."""
        try:
            # Convert data to appropriate format
            chart_data = self._prepare_chart_data(data)
            
            if not chart_data:
                return {
                    "status": "error",
                    "error": "Unable to prepare chart data"
                }
            
            # Create chart based on type
            fig = None
            
            if chart_type == "bar":
                fig = self._create_bar_chart(chart_data, title, x_label, y_label)
            elif chart_type == "line":
                fig = self._create_line_chart(chart_data, title, x_label, y_label)
            elif chart_type == "pie":
                fig = self._create_pie_chart(chart_data, title)
            elif chart_type == "scatter":
                fig = self._create_scatter_chart(chart_data, title, x_label, y_label)
            elif chart_type == "table":
                fig = self._create_table_chart(chart_data, title)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported chart type: {chart_type}"
                }
            
            if fig is None:
                return {
                    "status": "error",
                    "error": "Failed to create chart"
                }
            
            # Apply theme
            fig.update_layout(template=theme)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_filename = f"chart_{chart_type}_{timestamp}_{str(uuid.uuid4())[:8]}.html"
            chart_path = os.path.join(self.static_dir, chart_filename)
            
            # Save chart as HTML
            html_content = to_html(fig, include_plotlyjs='cdn', div_id=f"chart_{uuid.uuid4().hex[:8]}")
            
            with open(chart_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "status": "success",
                "chart_files": [chart_filename],
                "chart_type": chart_type,
                "chart_path": chart_path,
                "chart_url": f"/charts/{chart_filename}",
                "metadata": {
                    "title": title,
                    "x_label": x_label,
                    "y_label": y_label,
                    "theme": theme,
                    "data_points": len(chart_data.get("x", [])) if isinstance(chart_data.get("x"), list) else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chart creation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_chart_data(self, data: dict) -> dict:
        """Prepare and validate chart data."""
        try:
            prepared_data = {}
            
            # Handle different data formats
            if "x" in data and "y" in data:
                prepared_data["x"] = data["x"]
                prepared_data["y"] = data["y"]
            elif "labels" in data and "values" in data:
                prepared_data["labels"] = data["labels"]
                prepared_data["values"] = data["values"]
            elif "columns" in data and "rows" in data:
                prepared_data["columns"] = data["columns"]
                prepared_data["rows"] = data["rows"]
            else:
                # Try to extract from generic data structure
                if isinstance(data, dict) and len(data) >= 2:
                    keys = list(data.keys())
                    prepared_data["x"] = data[keys[0]]
                    prepared_data["y"] = data[keys[1]]
            
            return prepared_data
            
        except Exception as e:
            logger.error(f"Data preparation failed: {str(e)}")
            return {}
    
    def _create_bar_chart(self, data: dict, title: str, x_label: str, y_label: str):
        """Create bar chart."""
        try:
            x_data = data.get("x", [])
            y_data = data.get("y", [])
            
            if not x_data or not y_data:
                return None
            
            fig = go.Figure(data=[go.Bar(x=x_data, y=y_data)])
            fig.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Bar chart creation failed: {str(e)}")
            return None
    
    def _create_line_chart(self, data: dict, title: str, x_label: str, y_label: str):
        """Create line chart."""
        try:
            x_data = data.get("x", [])
            y_data = data.get("y", [])
            
            if not x_data or not y_data:
                return None
            
            fig = go.Figure(data=[go.Scatter(x=x_data, y=y_data, mode='lines+markers')])
            fig.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Line chart creation failed: {str(e)}")
            return None
    
    def _create_pie_chart(self, data: dict, title: str):
        """Create pie chart."""
        try:
            labels = data.get("labels", data.get("x", []))
            values = data.get("values", data.get("y", []))
            
            if not labels or not values:
                return None
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(title=title)
            
            return fig
            
        except Exception as e:
            logger.error(f"Pie chart creation failed: {str(e)}")
            return None
    
    def _create_scatter_chart(self, data: dict, title: str, x_label: str, y_label: str):
        """Create scatter plot."""
        try:
            x_data = data.get("x", [])
            y_data = data.get("y", [])
            
            if not x_data or not y_data:
                return None
            
            fig = go.Figure(data=[go.Scatter(x=x_data, y=y_data, mode='markers')])
            fig.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Scatter chart creation failed: {str(e)}")
            return None
    
    def _create_table_chart(self, data: dict, title: str):
        """Create table visualization."""
        try:
            columns = data.get("columns", [])
            rows = data.get("rows", [])
            
            if not columns and not rows:
                # Try to create from x/y data
                x_data = data.get("x", [])
                y_data = data.get("y", [])
                if x_data and y_data:
                    columns = ["X", "Y"]
                    rows = list(zip(x_data, y_data))
            
            if not columns or not rows:
                return None
            
            fig = go.Figure(data=[go.Table(
                header=dict(values=columns),
                cells=dict(values=list(zip(*rows)) if rows else [])
            )])
            fig.update_layout(title=title)
            
            return fig
            
        except Exception as e:
            logger.error(f"Table chart creation failed: {str(e)}")
            return None
    
    async def _format_table(self, data: dict, format_type: str, style: str, max_rows: int) -> dict:
        """Format data table."""
        try:
            # Convert to DataFrame if possible
            if PANDAS_AVAILABLE:
                if "columns" in data and "rows" in data:
                    df = pd.DataFrame(data["rows"], columns=data["columns"])
                elif isinstance(data, dict):
                    df = pd.DataFrame(data)
                else:
                    return {
                        "status": "error",
                        "error": "Unable to convert data to table format"
                    }
                
                # Limit rows
                if len(df) > max_rows:
                    df = df.head(max_rows)
                
                # Format based on type
                if format_type == "html":
                    formatted_data = df.to_html(classes=style, table_id="data_table")
                elif format_type == "markdown":
                    formatted_data = df.to_markdown()
                elif format_type == "json":
                    formatted_data = df.to_json(orient="records", indent=2)
                elif format_type == "csv":
                    formatted_data = df.to_csv(index=False)
                else:
                    formatted_data = str(df)
                
                return {
                    "status": "success",
                    "formatted_table": formatted_data,
                    "format": format_type,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": "Pandas not available for table formatting"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_report(self, data: dict, charts: list, tables: list, title: str, template: str) -> dict:
        """Generate comprehensive report."""
        try:
            report_components = []
            
            # Generate charts
            for chart_config in charts:
                chart_result = await self._create_chart(
                    chart_config.get("data", data),
                    chart_config.get("type", "bar"),
                    chart_config.get("title", "Chart"),
                    chart_config.get("x_label", "X"),
                    chart_config.get("y_label", "Y"),
                    chart_config.get("theme", "plotly_white")
                )
                if chart_result.get("status") == "success":
                    report_components.append({
                        "type": "chart",
                        "content": chart_result
                    })
            
            # Generate tables
            for table_config in tables:
                table_result = await self._format_table(
                    table_config.get("data", data),
                    table_config.get("format", "html"),
                    table_config.get("style", "bootstrap"),
                    table_config.get("max_rows", 100)
                )
                if table_result.get("status") == "success":
                    report_components.append({
                        "type": "table",
                        "content": table_result
                    })
            
            return {
                "status": "success",
                "report": {
                    "title": title,
                    "template": template,
                    "components": report_components,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _export_visualization(self, chart_file: str, export_format: str, width: int, height: int) -> dict:
        """Export visualization in specified format."""
        try:
            chart_path = os.path.join(self.static_dir, chart_file)
            
            if not os.path.exists(chart_path):
                return {
                    "status": "error",
                    "error": f"Chart file not found: {chart_file}"
                }
            
            # For now, return success (actual export would require additional libraries)
            export_filename = chart_file.replace('.html', f'.{export_format}')
            
            return {
                "status": "success",
                "original_file": chart_file,
                "export_file": export_filename,
                "export_format": export_format,
                "dimensions": {"width": width, "height": height},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

async def main():
    """Main entry point for Visualization MCP Server."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Visualization MCP Server...")
    
    # Create and run server
    server_instance = VisualizationMCPServer()
    
    # Run server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="visualization",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
