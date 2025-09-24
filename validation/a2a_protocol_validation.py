#!/usr/bin/env python3
"""
A2A Protocol Validation - Comprehensive validation suite for A2A protocol implementation

This validation suite tests all aspects of the A2A protocol including:
- Message passing and agent communication
- Conditional agent invocation
- Query analysis and routing
- Error handling and recovery
- Performance monitoring
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.a2a_protocol import (
    A2AProtocol, A2AMessage, AgentType, MessageType, AgentCapability,
    QueryAnalyzer, QueryAnalysis, get_a2a_protocol
)
from agents.a2a_orchestrator import A2AOrchestrator
from services.a2a_service import A2AService, get_a2a_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class A2AProtocolValidator:
    """
    Comprehensive validation suite for A2A protocol implementation.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.protocol = get_a2a_protocol()
        self.service = get_a2a_service()
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': []
        }
        
        logger.info("A2A Protocol Validator initialized")
    
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.results['total_tests'] += 1
        if passed:
            self.results['passed_tests'] += 1
            status = "✅ PASSED"
        else:
            self.results['failed_tests'] += 1
            status = "❌ FAILED"
        
        result = {
            'test_name': test_name,
            'status': status,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['test_results'].append(result)
        logger.info(f"{status}: {test_name} - {message}")
    
    def validate_query_analyzer(self) -> bool:
        """Validate query analyzer functionality."""
        logger.info("🔍 Validating Query Analyzer...")
        
        try:
            # Test 1: Database query detection
            db_query = "Show me the top 10 mutual funds by performance"
            analysis = QueryAnalyzer.analyze_query(db_query)
            
            if analysis.requires_database:
                self.log_test_result("Query Analyzer - Database Detection", True, 
                                   "Correctly identified database requirement")
            else:
                self.log_test_result("Query Analyzer - Database Detection", False, 
                                   "Failed to identify database requirement")
                return False
            
            # Test 2: Analysis requirement detection
            analysis_query = "Analyze the risk-adjusted returns of SBI Small Cap Fund"
            analysis = QueryAnalyzer.analyze_query(analysis_query)
            
            if analysis.requires_analysis:
                self.log_test_result("Query Analyzer - Analysis Detection", True, 
                                   "Correctly identified analysis requirement")
            else:
                self.log_test_result("Query Analyzer - Analysis Detection", False, 
                                   "Failed to identify analysis requirement")
                return False
            
            # Test 3: Visualization requirement detection
            viz_query = "Create a bar chart showing fund performance comparison"
            analysis = QueryAnalyzer.analyze_query(viz_query)
            
            if analysis.requires_visualization:
                self.log_test_result("Query Analyzer - Visualization Detection", True, 
                                   "Correctly identified visualization requirement")
            else:
                self.log_test_result("Query Analyzer - Visualization Detection", False, 
                                   "Failed to identify visualization requirement")
                return False
            
            # Test 4: PDF export detection
            pdf_query = "Generate a detailed PDF report on mutual fund analysis"
            analysis = QueryAnalyzer.analyze_query(pdf_query)
            
            if analysis.requires_pdf_export:
                self.log_test_result("Query Analyzer - PDF Export Detection", True, 
                                   "Correctly identified PDF export requirement")
            else:
                self.log_test_result("Query Analyzer - PDF Export Detection", False, 
                                   "Failed to identify PDF export requirement")
                return False
            
            # Test 5: Query type classification
            mf_query = "What are the best mutual funds for long-term investment?"
            analysis = QueryAnalyzer.analyze_query(mf_query)
            
            if analysis.query_type == "mutual_fund":
                self.log_test_result("Query Analyzer - Type Classification", True, 
                                   f"Correctly classified as {analysis.query_type}")
            else:
                self.log_test_result("Query Analyzer - Type Classification", False, 
                                   f"Incorrectly classified as {analysis.query_type}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Query Analyzer - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_a2a_protocol(self) -> bool:
        """Validate A2A protocol message passing."""
        logger.info("📡 Validating A2A Protocol...")
        
        try:
            # Test 1: Agent registration
            initial_agents = len(self.protocol.agent_registry)
            
            self.protocol.register_agent(
                AgentType.ENHANCED_SQL,
                [AgentCapability.DATABASE_QUERY],
                None
            )
            
            if len(self.protocol.agent_registry) > initial_agents:
                self.log_test_result("A2A Protocol - Agent Registration", True, 
                                   "Successfully registered agent")
            else:
                self.log_test_result("A2A Protocol - Agent Registration", False, 
                                   "Failed to register agent")
                return False
            
            # Test 2: Message creation
            message = self.protocol.create_message(
                sender=AgentType.ENHANCED_SQL,
                recipient=AgentType.MUTUAL_FUND_QUANT,
                message_type=MessageType.ANALYSIS_REQUEST,
                payload={'query': 'test query', 'data': []}
            )
            
            if message and message.message_id:
                self.log_test_result("A2A Protocol - Message Creation", True, 
                                   f"Created message with ID: {message.message_id}")
            else:
                self.log_test_result("A2A Protocol - Message Creation", False, 
                                   "Failed to create message")
                return False
            
            # Test 3: Message history tracking
            initial_messages = len(self.protocol.message_history)
            
            response_message = self.protocol.create_message(
                sender=AgentType.MUTUAL_FUND_QUANT,
                recipient=AgentType.ENHANCED_SQL,
                message_type=MessageType.ANALYSIS_RESPONSE,
                payload={'result': 'test result'},
                parent_message_id=message.message_id
            )
            
            if len(self.protocol.message_history) > initial_messages:
                self.log_test_result("A2A Protocol - Message History", True, 
                                   "Message history updated correctly")
            else:
                self.log_test_result("A2A Protocol - Message History", False, 
                                   "Message history not updated")
                return False
            
            # Test 4: Message threading
            thread_messages = self.protocol.get_message_thread(message.message_id)
            
            if len(thread_messages) >= 2:  # Original + response
                self.log_test_result("A2A Protocol - Message Threading", True, 
                                   f"Retrieved {len(thread_messages)} messages in thread")
            else:
                self.log_test_result("A2A Protocol - Message Threading", False, 
                                   "Failed to retrieve message thread")
                return False
            
            # Test 5: Performance metrics
            metrics = self.protocol.get_performance_metrics()
            
            if metrics and 'total_messages' in metrics:
                self.log_test_result("A2A Protocol - Performance Metrics", True, 
                                   f"Retrieved metrics: {metrics['total_messages']} total messages")
            else:
                self.log_test_result("A2A Protocol - Performance Metrics", False, 
                                   "Failed to retrieve performance metrics")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("A2A Protocol - Exception", False, f"Exception: {str(e)}")
            return False
    
    async def validate_a2a_orchestrator(self) -> bool:
        """Validate A2A orchestrator functionality."""
        logger.info("🎼 Validating A2A Orchestrator...")
        
        try:
            # Test 1: Orchestrator initialization
            orchestrator = A2AOrchestrator(user_email="test@example.com")
            
            if orchestrator and orchestrator.user_email == "test@example.com":
                self.log_test_result("A2A Orchestrator - Initialization", True, 
                                   "Orchestrator initialized successfully")
            else:
                self.log_test_result("A2A Orchestrator - Initialization", False, 
                                   "Failed to initialize orchestrator")
                return False
            
            # Test 2: Health status
            health = orchestrator.get_health_status()
            
            if health and health.get('orchestrator_status') == 'healthy':
                self.log_test_result("A2A Orchestrator - Health Status", True, 
                                   "Health status retrieved successfully")
            else:
                self.log_test_result("A2A Orchestrator - Health Status", False, 
                                   "Failed to retrieve health status")
                return False
            
            # Test 3: Capabilities
            capabilities = orchestrator.get_capabilities()
            
            if capabilities and 'agent_capabilities' in capabilities:
                self.log_test_result("A2A Orchestrator - Capabilities", True, 
                                   "Capabilities retrieved successfully")
            else:
                self.log_test_result("A2A Orchestrator - Capabilities", False, 
                                   "Failed to retrieve capabilities")
                return False
            
            # Test 4: Query processing (mock test)
            try:
                # This would normally process a real query, but we'll test the structure
                test_query = "Show me information about mutual funds"
                
                # We can't actually process without database connection, 
                # but we can test the method exists and accepts parameters
                if hasattr(orchestrator, 'process_query'):
                    self.log_test_result("A2A Orchestrator - Query Processing Interface", True, 
                                       "Query processing method available")
                else:
                    self.log_test_result("A2A Orchestrator - Query Processing Interface", False, 
                                       "Query processing method not available")
                    return False
                
            except Exception as e:
                self.log_test_result("A2A Orchestrator - Query Processing", False, 
                                   f"Query processing failed: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("A2A Orchestrator - Exception", False, f"Exception: {str(e)}")
            return False
    
    async def validate_a2a_service(self) -> bool:
        """Validate A2A service functionality."""
        logger.info("🔧 Validating A2A Service...")
        
        try:
            # Test 1: Service initialization
            if self.service:
                self.log_test_result("A2A Service - Initialization", True, 
                                   "Service initialized successfully")
            else:
                self.log_test_result("A2A Service - Initialization", False, 
                                   "Failed to initialize service")
                return False
            
            # Test 2: Query analysis capabilities
            analysis_result = self.service.analyze_query_capabilities(
                "Analyze the performance of top mutual funds with charts"
            )
            
            if analysis_result and analysis_result.get('success'):
                self.log_test_result("A2A Service - Query Analysis", True, 
                                   "Query analysis completed successfully")
            else:
                self.log_test_result("A2A Service - Query Analysis", False, 
                                   "Query analysis failed")
                return False
            
            # Test 3: Service health
            health = self.service.get_service_health()
            
            if health and health.get('service_status') == 'healthy':
                self.log_test_result("A2A Service - Health Check", True, 
                                   "Service health check passed")
            else:
                self.log_test_result("A2A Service - Health Check", False, 
                                   "Service health check failed")
                return False
            
            # Test 4: Service capabilities
            capabilities = self.service.get_service_capabilities()
            
            if capabilities and 'supported_operations' in capabilities:
                self.log_test_result("A2A Service - Capabilities", True, 
                                   "Service capabilities retrieved")
            else:
                self.log_test_result("A2A Service - Capabilities", False, 
                                   "Failed to retrieve service capabilities")
                return False
            
            # Test 5: Orchestrator management
            orchestrator = self.service.get_orchestrator("test@example.com")
            
            if orchestrator:
                self.log_test_result("A2A Service - Orchestrator Management", True, 
                                   "Orchestrator created/retrieved successfully")
            else:
                self.log_test_result("A2A Service - Orchestrator Management", False, 
                                   "Failed to create/retrieve orchestrator")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("A2A Service - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_conditional_invocation(self) -> bool:
        """Validate conditional agent invocation logic."""
        logger.info("🔀 Validating Conditional Agent Invocation...")
        
        try:
            # Test 1: Database-only query
            db_only_query = "List all mutual fund schemes"
            analysis = QueryAnalyzer.analyze_query(db_only_query)
            
            expected_agents = ['enhanced_sql']
            actual_agents = self.service._estimate_agents_needed(analysis)
            
            if actual_agents == expected_agents:
                self.log_test_result("Conditional Invocation - Database Only", True, 
                                   f"Correctly identified agents: {actual_agents}")
            else:
                self.log_test_result("Conditional Invocation - Database Only", False, 
                                   f"Expected {expected_agents}, got {actual_agents}")
                return False
            
            # Test 2: Database + Analysis query
            analysis_query = "Analyze the risk profile of HDFC Equity Fund"
            analysis = QueryAnalyzer.analyze_query(analysis_query)
            
            expected_agents = ['enhanced_sql', 'mutual_fund_quant']
            actual_agents = self.service._estimate_agents_needed(analysis)
            
            if actual_agents == expected_agents:
                self.log_test_result("Conditional Invocation - Database + Analysis", True, 
                                   f"Correctly identified agents: {actual_agents}")
            else:
                self.log_test_result("Conditional Invocation - Database + Analysis", False, 
                                   f"Expected {expected_agents}, got {actual_agents}")
                return False
            
            # Test 3: Full pipeline query
            full_query = "Create a detailed PDF report with charts analyzing mutual fund performance"
            analysis = QueryAnalyzer.analyze_query(full_query)
            
            expected_agents = ['enhanced_sql', 'mutual_fund_quant', 'data_formatter']
            actual_agents = self.service._estimate_agents_needed(analysis)
            
            if actual_agents == expected_agents:
                self.log_test_result("Conditional Invocation - Full Pipeline", True, 
                                   f"Correctly identified agents: {actual_agents}")
            else:
                self.log_test_result("Conditional Invocation - Full Pipeline", False, 
                                   f"Expected {expected_agents}, got {actual_agents}")
                return False
            
            # Test 4: Visualization-only query
            viz_query = "Show me a bar chart of the data from my previous query"
            analysis = QueryAnalyzer.analyze_query(viz_query)
            
            expected_agents = ['enhanced_sql', 'data_formatter']
            actual_agents = self.service._estimate_agents_needed(analysis)
            
            if actual_agents == expected_agents:
                self.log_test_result("Conditional Invocation - Visualization", True, 
                                   f"Correctly identified agents: {actual_agents}")
            else:
                self.log_test_result("Conditional Invocation - Visualization", False, 
                                   f"Expected {expected_agents}, got {actual_agents}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Conditional Invocation - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_performance_estimation(self) -> bool:
        """Validate performance estimation logic."""
        logger.info("⏱️ Validating Performance Estimation...")
        
        try:
            # Test 1: Simple query estimation
            simple_query = "List mutual funds"
            analysis = QueryAnalyzer.analyze_query(simple_query)
            estimated_time = self.service._estimate_processing_time(analysis)
            
            if 1.0 <= estimated_time <= 5.0:  # Reasonable range for simple query
                self.log_test_result("Performance Estimation - Simple Query", True, 
                                   f"Estimated time: {estimated_time:.2f}s")
            else:
                self.log_test_result("Performance Estimation - Simple Query", False, 
                                   f"Unrealistic time estimate: {estimated_time:.2f}s")
                return False
            
            # Test 2: Complex query estimation
            complex_query = "Generate a comprehensive PDF report with detailed analysis and multiple charts"
            analysis = QueryAnalyzer.analyze_query(complex_query)
            estimated_time = self.service._estimate_processing_time(analysis)
            
            if 8.0 <= estimated_time <= 20.0:  # Reasonable range for complex query
                self.log_test_result("Performance Estimation - Complex Query", True, 
                                   f"Estimated time: {estimated_time:.2f}s")
            else:
                self.log_test_result("Performance Estimation - Complex Query", False, 
                                   f"Unrealistic time estimate: {estimated_time:.2f}s")
                return False
            
            # Test 3: Time scaling with complexity
            simple_analysis = QueryAnalyzer.analyze_query("Show funds")
            complex_analysis = QueryAnalyzer.analyze_query("Analyze and visualize fund performance with PDF report")
            
            simple_time = self.service._estimate_processing_time(simple_analysis)
            complex_time = self.service._estimate_processing_time(complex_analysis)
            
            if complex_time > simple_time:
                self.log_test_result("Performance Estimation - Complexity Scaling", True, 
                                   f"Complex query ({complex_time:.2f}s) > Simple query ({simple_time:.2f}s)")
            else:
                self.log_test_result("Performance Estimation - Complexity Scaling", False, 
                                   f"Time scaling incorrect: Complex={complex_time:.2f}s, Simple={simple_time:.2f}s")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Performance Estimation - Exception", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("🚀 Starting A2A Protocol Validation Suite...")
        
        # Run all validation tests
        validations = [
            ("Query Analyzer", self.validate_query_analyzer()),
            ("A2A Protocol", self.validate_a2a_protocol()),
            ("A2A Orchestrator", await self.validate_a2a_orchestrator()),
            ("A2A Service", await self.validate_a2a_service()),
            ("Conditional Invocation", self.validate_conditional_invocation()),
            ("Performance Estimation", self.validate_performance_estimation())
        ]
        
        # Process results
        all_passed = True
        for validation_name, result in validations:
            if not result:
                all_passed = False
                logger.error(f"❌ {validation_name} validation failed")
            else:
                logger.info(f"✅ {validation_name} validation passed")
        
        # Generate summary
        self.results['all_passed'] = all_passed
        self.results['success_rate'] = (
            self.results['passed_tests'] / self.results['total_tests'] * 100
            if self.results['total_tests'] > 0 else 0
        )
        
        logger.info(f"🏁 Validation Complete: {self.results['passed_tests']}/{self.results['total_tests']} tests passed ({self.results['success_rate']:.1f}%)")
        
        return self.results
    
    def print_detailed_report(self):
        """Print detailed validation report."""
        print("\n" + "="*80)
        print("🔍 A2A PROTOCOL VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   Passed: {self.results['passed_tests']}")
        print(f"   Failed: {self.results['failed_tests']}")
        print(f"   Success Rate: {self.results['success_rate']:.1f}%")
        print(f"   Overall Status: {'✅ PASSED' if self.results['all_passed'] else '❌ FAILED'}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.results['test_results']:
            print(f"   {result['status']} {result['test_name']}")
            if result['message']:
                print(f"      └─ {result['message']}")
        
        print("\n" + "="*80)


async def main():
    """Main validation function."""
    validator = A2AProtocolValidator()
    
    try:
        results = await validator.run_all_validations()
        validator.print_detailed_report()
        
        # Return appropriate exit code
        return 0 if results['all_passed'] else 1
        
    except Exception as e:
        logger.error(f"Validation suite failed with exception: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
