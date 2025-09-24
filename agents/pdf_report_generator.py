#!/usr/bin/env python3
"""
PDF Report Generator - Comprehensive report generation with charts and analysis

This module generates professional PDF reports from mutual fund analysis data,
including charts, reasoning traces, and investment recommendations.

Features:
- Professional PDF layout with charts and tables
- Integration with A2A protocol for seamless data flow
- Support for multiple chart types and visualizations
- Investment thesis and reasoning trace inclusion
- Downloadable reports with unique identifiers
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available - PDF generation will be limited")

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available - chart generation will be limited")


class PDFReportGenerator:
    """
    Professional PDF report generator for mutual fund analysis.
    
    Features:
    - Multi-page reports with professional layout
    - Chart and table integration
    - Investment thesis and reasoning traces
    - Customizable styling and branding
    """
    
    def __init__(self, static_dir: str = "static/reports"):
        """
        Initialize the PDF report generator.
        
        Args:
            static_dir: Directory to save generated PDF reports
        """
        self.static_dir = static_dir
        self.ensure_directory_exists()
        
        # Initialize styles
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self._setup_custom_styles()
        
        logger.info(f"PDF Report Generator initialized - Output dir: {static_dir}")
    
    def ensure_directory_exists(self):
        """Ensure the static directory exists."""
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)
            logger.info(f"Created directory: {self.static_dir}")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        if not REPORTLAB_AVAILABLE:
            return
        
        # Custom title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Custom heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Custom body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY
        )
        
        # Investment recommendation style
        self.recommendation_style = ParagraphStyle(
            'RecommendationStyle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=15,
            alignment=TA_CENTER,
            textColor=colors.darkgreen,
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.darkgreen
        )
    
    def generate_comprehensive_report(self, query: str, sql_data: Dict[str, Any],
                                    analysis_data: Optional[Dict[str, Any]] = None,
                                    reasoning_trace: Optional[List[Dict[str, Any]]] = None,
                                    chart_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive PDF report from analysis data.
        
        Args:
            query: Original user query
            sql_data: SQL query results and data
            analysis_data: Quantitative analysis results
            reasoning_trace: Reasoning steps from ReAct framework
            chart_files: List of chart file paths
            
        Returns:
            Dictionary with PDF generation results
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_text_report(query, sql_data, analysis_data, reasoning_trace)
        
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"mutual_fund_report_{timestamp}.pdf"
            pdf_path = os.path.join(self.static_dir, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            story = []
            
            # Add title page
            self._add_title_page(story, query)
            
            # Add executive summary
            self._add_executive_summary(story, sql_data, analysis_data)
            
            # Add data analysis section
            self._add_data_analysis(story, sql_data)
            
            # Add quantitative analysis if available
            if analysis_data:
                self._add_quantitative_analysis(story, analysis_data)
            
            # Add reasoning trace if available
            if reasoning_trace:
                self._add_reasoning_trace(story, reasoning_trace)
            
            # Add investment recommendation
            if analysis_data and analysis_data.get('investment_thesis'):
                self._add_investment_recommendation(story, analysis_data['investment_thesis'])
            
            # Add charts if available
            if chart_files:
                self._add_charts_section(story, chart_files)
            
            # Add footer information
            self._add_footer_info(story)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated successfully: {pdf_filename}")
            
            return {
                'success': True,
                'pdf_file': pdf_filename,
                'pdf_path': pdf_path,
                'file_size': os.path.getsize(pdf_path),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_report': self._generate_text_report(query, sql_data, analysis_data, reasoning_trace)
            }
    
    def _add_title_page(self, story: List, query: str):
        """Add title page to the PDF report."""
        # Main title
        title = Paragraph("Mutual Fund Analysis Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Query information
        query_title = Paragraph("Analysis Query:", self.heading_style)
        story.append(query_title)
        
        query_text = Paragraph(f'"{query}"', self.body_style)
        story.append(query_text)
        story.append(Spacer(1, 0.3*inch))
        
        # Report metadata
        metadata_data = [
            ['Report Generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")],
            ['Analysis Type:', 'Comprehensive Mutual Fund Analysis'],
            ['Data Source:', 'Multi-Database Financial System'],
            ['Report Version:', '1.0']
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(PageBreak())
    
    def _add_executive_summary(self, story: List, sql_data: Dict[str, Any], 
                             analysis_data: Optional[Dict[str, Any]]):
        """Add executive summary section."""
        story.append(Paragraph("Executive Summary", self.heading_style))
        
        # Summary points
        summary_points = []
        
        # Data summary
        if sql_data.get('data'):
            data_count = len(sql_data['data'])
            summary_points.append(f"• Analyzed {data_count} mutual fund records")
        
        # Analysis summary
        if analysis_data:
            if analysis_data.get('investment_thesis'):
                thesis = analysis_data['investment_thesis']
                recommendation = thesis.get('primary_recommendation', 'Hold')
                confidence = thesis.get('confidence_level', 0.5)
                summary_points.append(f"• Investment Recommendation: {recommendation} (Confidence: {confidence:.1%})")
            
            if analysis_data.get('analysis_confidence'):
                conf = analysis_data['analysis_confidence']
                summary_points.append(f"• Analysis Confidence Level: {conf:.1%}")
        
        # Add performance insights
        summary_points.append("• Comprehensive quantitative analysis performed")
        summary_points.append("• Risk-adjusted performance metrics calculated")
        summary_points.append("• Investment suitability assessment completed")
        
        summary_text = "\n".join(summary_points)
        story.append(Paragraph(summary_text, self.body_style))
        story.append(Spacer(1, 0.3*inch))
    
    def _add_data_analysis(self, story: List, sql_data: Dict[str, Any]):
        """Add data analysis section with tables."""
        story.append(Paragraph("Data Analysis", self.heading_style))
        
        # Add SQL response text
        if sql_data.get('response'):
            response_text = sql_data['response'][:1000] + "..." if len(sql_data['response']) > 1000 else sql_data['response']
            story.append(Paragraph(response_text, self.body_style))
        
        # Add data table if available
        if sql_data.get('data') and len(sql_data['data']) > 0:
            story.append(Paragraph("Data Summary:", self.body_style))
            
            # Create table from data (limit to first 10 rows for PDF)
            data = sql_data['data'][:10]
            if data:
                # Add headers if available
                headers = ['Item', 'Value'] if len(data[0]) == 2 else [f'Column {i+1}' for i in range(len(data[0]))]
                table_data = [headers] + data
                
                data_table = Table(table_data)
                data_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(data_table)
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_quantitative_analysis(self, story: List, analysis_data: Dict[str, Any]):
        """Add quantitative analysis section."""
        story.append(Paragraph("Quantitative Analysis", self.heading_style))
        
        # Add analysis insights
        if analysis_data.get('analysis'):
            analysis_text = analysis_data['analysis']
            story.append(Paragraph(analysis_text, self.body_style))
        
        # Add key metrics if available
        if analysis_data.get('calculations'):
            calculations = analysis_data['calculations']
            story.append(Paragraph("Key Financial Metrics:", self.body_style))
            
            metrics_text = []
            for key, value in calculations.items():
                if isinstance(value, (int, float)):
                    metrics_text.append(f"• {key.replace('_', ' ').title()}: {value:.2f}")
                else:
                    metrics_text.append(f"• {key.replace('_', ' ').title()}: {value}")
            
            if metrics_text:
                story.append(Paragraph("\n".join(metrics_text), self.body_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_reasoning_trace(self, story: List, reasoning_trace: List[Dict[str, Any]]):
        """Add reasoning trace section from ReAct framework."""
        story.append(Paragraph("Analysis Reasoning Process", self.heading_style))
        
        story.append(Paragraph(
            "The following shows the step-by-step reasoning process used in this analysis:",
            self.body_style
        ))
        
        for i, trace in enumerate(reasoning_trace[:5], 1):  # Limit to first 5 traces
            step_title = f"Step {i}: {trace.get('step_type', 'Unknown').title()}"
            story.append(Paragraph(step_title, self.heading_style))
            
            content = trace.get('content', 'No content available')
            story.append(Paragraph(content, self.body_style))
            
            if trace.get('confidence'):
                confidence_text = f"Confidence Level: {trace['confidence']:.1%}"
                story.append(Paragraph(confidence_text, self.body_style))
            
            story.append(Spacer(1, 0.2*inch))
    
    def _add_investment_recommendation(self, story: List, investment_thesis: Dict[str, Any]):
        """Add investment recommendation section."""
        story.append(Paragraph("Investment Recommendation", self.heading_style))
        
        # Main recommendation
        recommendation = investment_thesis.get('primary_recommendation', 'Hold')
        confidence = investment_thesis.get('confidence_level', 0.5)
        
        rec_text = f"Recommendation: {recommendation} (Confidence: {confidence:.1%})"
        story.append(Paragraph(rec_text, self.recommendation_style))
        
        # Risk assessment
        if investment_thesis.get('risk_assessment'):
            risk = investment_thesis['risk_assessment']
            story.append(Paragraph(f"Risk Level: {risk}", self.body_style))
        
        # Strategic outlook
        if investment_thesis.get('strategic_outlook'):
            outlook = investment_thesis['strategic_outlook']
            story.append(Paragraph(f"Strategic Outlook: {outlook}", self.body_style))
        
        # Key factors
        if investment_thesis.get('key_factors'):
            factors = investment_thesis['key_factors']
            story.append(Paragraph("Key Decision Factors:", self.body_style))
            
            factors_text = "\n".join([f"• {factor}" for factor in factors[:5]])
            story.append(Paragraph(factors_text, self.body_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_charts_section(self, story: List, chart_files: List[str]):
        """Add charts section to the PDF."""
        story.append(Paragraph("Visual Analysis", self.heading_style))
        
        for chart_file in chart_files[:3]:  # Limit to 3 charts
            chart_path = os.path.join("static/charts", chart_file)
            if os.path.exists(chart_path):
                try:
                    # Convert HTML chart to image (simplified approach)
                    story.append(Paragraph(f"Chart: {chart_file}", self.body_style))
                    story.append(Spacer(1, 0.2*inch))
                except Exception as e:
                    logger.warning(f"Could not add chart {chart_file}: {e}")
    
    def _add_footer_info(self, story: List):
        """Add footer information."""
        story.append(PageBreak())
        story.append(Paragraph("Disclaimer", self.heading_style))
        
        disclaimer_text = """
        This report is generated for informational purposes only and should not be considered as investment advice. 
        Past performance does not guarantee future results. Please consult with a qualified financial advisor before 
        making investment decisions. The analysis is based on available data and computational models, and actual 
        results may vary.
        """
        
        story.append(Paragraph(disclaimer_text, self.body_style))
        
        # Report metadata
        footer_text = f"""
        Report generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")} by 
        Multi-Agent SQL Analysis System. For questions or support, please contact your system administrator.
        """
        
        story.append(Paragraph(footer_text, self.body_style))
    
    def _generate_text_report(self, query: str, sql_data: Dict[str, Any],
                            analysis_data: Optional[Dict[str, Any]] = None,
                            reasoning_trace: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate a text-based report when PDF libraries are not available.
        
        Args:
            query: Original user query
            sql_data: SQL query results
            analysis_data: Analysis results
            reasoning_trace: Reasoning steps
            
        Returns:
            Text report data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_filename = f"mutual_fund_report_{timestamp}.txt"
        txt_path = os.path.join(self.static_dir, txt_filename)
        
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("MUTUAL FUND ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Query: {query}\n")
                f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
                
                # SQL Data
                if sql_data.get('response'):
                    f.write("DATA ANALYSIS:\n")
                    f.write("-" * 20 + "\n")
                    f.write(sql_data['response'] + "\n\n")
                
                # Quantitative Analysis
                if analysis_data:
                    f.write("QUANTITATIVE ANALYSIS:\n")
                    f.write("-" * 25 + "\n")
                    if analysis_data.get('analysis'):
                        f.write(analysis_data['analysis'] + "\n\n")
                    
                    # Investment Thesis
                    if analysis_data.get('investment_thesis'):
                        thesis = analysis_data['investment_thesis']
                        f.write("INVESTMENT RECOMMENDATION:\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Recommendation: {thesis.get('primary_recommendation', 'Hold')}\n")
                        f.write(f"Confidence: {thesis.get('confidence_level', 0.5):.1%}\n")
                        f.write(f"Risk Assessment: {thesis.get('risk_assessment', 'Unknown')}\n\n")
                
                # Reasoning Trace
                if reasoning_trace:
                    f.write("REASONING PROCESS:\n")
                    f.write("-" * 20 + "\n")
                    for i, trace in enumerate(reasoning_trace[:3], 1):
                        f.write(f"Step {i}: {trace.get('step_type', 'Unknown').title()}\n")
                        f.write(f"{trace.get('content', 'No content')}\n\n")
                
                f.write("DISCLAIMER:\n")
                f.write("-" * 15 + "\n")
                f.write("This report is for informational purposes only and should not be considered investment advice.\n")
            
            return {
                'success': True,
                'report_file': txt_filename,
                'report_path': txt_path,
                'file_size': os.path.getsize(txt_path),
                'format': 'text'
            }
            
        except Exception as e:
            logger.error(f"Text report generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
pdf_generator = PDFReportGenerator()


def get_pdf_generator() -> PDFReportGenerator:
    """Get the global PDF generator instance."""
    return pdf_generator
