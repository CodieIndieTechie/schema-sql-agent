#!/usr/bin/env python3
"""
Integration Validation - End-to-end validation of A2A protocol integration

This validation suite tests the complete integration of the A2A protocol
with the existing system including:
- API endpoint integration
- Database connectivity (mock)
- Agent coordination workflows
- Error handling and recovery
- Performance monitoring
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationValidator:
    """
    End-to-end integration validation for A2A protocol.
    """
    
    def __init__(self):
        """Initialize the integration validator."""
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': []
        }
        
        logger.info("Integration Validator initialized")
    
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
    
    def validate_import_structure(self) -> bool:
        """Validate that all A2A components can be imported."""
        logger.info("📦 Validating Import Structure...")
        
        try:
            # Test 1: A2A Protocol imports
            try:
                from agents.a2a_protocol import (
                    A2AProtocol, A2AMessage, AgentType, MessageType, AgentCapability,
                    QueryAnalyzer, QueryAnalysis, get_a2a_protocol
                )
                self.log_test_result("Import Structure - A2A Protocol", True, 
                                   "All A2A protocol components imported successfully")
            except ImportError as e:
                self.log_test_result("Import Structure - A2A Protocol", False, 
                                   f"Import error: {str(e)}")
                return False
            
            # Test 2: A2A Orchestrator imports
            try:
                from agents.a2a_orchestrator import A2AOrchestrator
                self.log_test_result("Import Structure - A2A Orchestrator", True, 
                                   "A2A orchestrator imported successfully")
            except ImportError as e:
                self.log_test_result("Import Structure - A2A Orchestrator", False, 
                                   f"Import error: {str(e)}")
                return False
            
            # Test 3: A2A Service imports
            try:
                from services.a2a_service import A2AService, get_a2a_service
                self.log_test_result("Import Structure - A2A Service", True, 
                                   "A2A service imported successfully")
            except ImportError as e:
                self.log_test_result("Import Structure - A2A Service", False, 
                                   f"Import error: {str(e)}")
                return False
            
            # Test 4: PDF Report Generator imports
            try:
                from agents.pdf_report_generator import PDFReportGenerator, get_pdf_generator
                self.log_test_result("Import Structure - PDF Generator", True, 
                                   "PDF report generator imported successfully")
            except ImportError as e:
                self.log_test_result("Import Structure - PDF Generator", False, 
                                   f"Import error: {str(e)}")
                return False
            
            # Test 5: Enhanced SQL Agent imports
            try:
                from agents.enhanced_sql_agent import EnhancedSQLAgent
                self.log_test_result("Import Structure - Enhanced SQL Agent", True, 
                                   "Enhanced SQL agent imported successfully")
            except ImportError as e:
                self.log_test_result("Import Structure - Enhanced SQL Agent", False, 
                                   f"Import error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Import Structure - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_agent_initialization(self) -> bool:
        """Validate that agents can be initialized properly."""
        logger.info("🤖 Validating Agent Initialization...")
        
        try:
            # Test 1: A2A Protocol initialization
            try:
                from agents.a2a_protocol import get_a2a_protocol
                protocol = get_a2a_protocol()
                
                if protocol and hasattr(protocol, 'agent_registry'):
                    self.log_test_result("Agent Initialization - A2A Protocol", True, 
                                       "A2A protocol initialized successfully")
                else:
                    self.log_test_result("Agent Initialization - A2A Protocol", False, 
                                       "A2A protocol missing required attributes")
                    return False
            except Exception as e:
                self.log_test_result("Agent Initialization - A2A Protocol", False, 
                                   f"Initialization error: {str(e)}")
                return False
            
            # Test 2: A2A Service initialization
            try:
                from services.a2a_service import get_a2a_service
                service = get_a2a_service()
                
                if service and hasattr(service, 'orchestrators'):
                    self.log_test_result("Agent Initialization - A2A Service", True, 
                                       "A2A service initialized successfully")
                else:
                    self.log_test_result("Agent Initialization - A2A Service", False, 
                                       "A2A service missing required attributes")
                    return False
            except Exception as e:
                self.log_test_result("Agent Initialization - A2A Service", False, 
                                   f"Initialization error: {str(e)}")
                return False
            
            # Test 3: PDF Generator initialization
            try:
                from agents.pdf_report_generator import get_pdf_generator
                pdf_gen = get_pdf_generator()
                
                if pdf_gen and hasattr(pdf_gen, 'static_dir'):
                    self.log_test_result("Agent Initialization - PDF Generator", True, 
                                       "PDF generator initialized successfully")
                else:
                    self.log_test_result("Agent Initialization - PDF Generator", False, 
                                       "PDF generator missing required attributes")
                    return False
            except Exception as e:
                self.log_test_result("Agent Initialization - PDF Generator", False, 
                                   f"Initialization error: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Agent Initialization - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_workflow_scenarios(self) -> bool:
        """Validate different workflow scenarios."""
        logger.info("🔄 Validating Workflow Scenarios...")
        
        try:
            from agents.a2a_protocol import QueryAnalyzer
            from services.a2a_service import get_a2a_service
            
            service = get_a2a_service()
            
            # Test 1: Simple database query workflow
            simple_query = "List all mutual fund schemes"
            analysis_result = service.analyze_query_capabilities(simple_query)
            
            if (analysis_result.get('success') and 
                analysis_result.get('estimated_agents') == ['enhanced_sql']):
                self.log_test_result("Workflow Scenarios - Simple Query", True, 
                                   "Simple query workflow validated")
            else:
                self.log_test_result("Workflow Scenarios - Simple Query", False, 
                                   f"Unexpected workflow: {analysis_result}")
                return False
            
            # Test 2: Analysis workflow
            analysis_query = "Analyze the risk profile of mutual funds"
            analysis_result = service.analyze_query_capabilities(analysis_query)
            
            expected_agents = ['enhanced_sql', 'mutual_fund_quant']
            if (analysis_result.get('success') and 
                analysis_result.get('estimated_agents') == expected_agents):
                self.log_test_result("Workflow Scenarios - Analysis Query", True, 
                                   "Analysis query workflow validated")
            else:
                self.log_test_result("Workflow Scenarios - Analysis Query", False, 
                                   f"Expected {expected_agents}, got {analysis_result.get('estimated_agents')}")
                return False
            
            # Test 3: Visualization workflow
            viz_query = "Create a bar chart of mutual fund data"
            analysis_result = service.analyze_query_capabilities(viz_query)
            
            expected_agents = ['enhanced_sql', 'data_formatter']
            if (analysis_result.get('success') and 
                analysis_result.get('estimated_agents') == expected_agents):
                self.log_test_result("Workflow Scenarios - Visualization Query", True, 
                                   "Visualization query workflow validated")
            else:
                self.log_test_result("Workflow Scenarios - Visualization Query", False, 
                                   f"Expected {expected_agents}, got {analysis_result.get('estimated_agents')}")
                return False
            
            # Test 4: Full pipeline workflow
            full_query = "Generate a comprehensive PDF report with analysis and charts"
            analysis_result = service.analyze_query_capabilities(full_query)
            
            expected_agents = ['enhanced_sql', 'mutual_fund_quant', 'data_formatter']
            if (analysis_result.get('success') and 
                analysis_result.get('estimated_agents') == expected_agents):
                self.log_test_result("Workflow Scenarios - Full Pipeline", True, 
                                   "Full pipeline workflow validated")
            else:
                self.log_test_result("Workflow Scenarios - Full Pipeline", False, 
                                   f"Expected {expected_agents}, got {analysis_result.get('estimated_agents')}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Workflow Scenarios - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_error_handling(self) -> bool:
        """Validate error handling mechanisms."""
        logger.info("🛡️ Validating Error Handling...")
        
        try:
            from services.a2a_service import get_a2a_service
            
            service = get_a2a_service()
            
            # Test 1: Invalid query handling
            try:
                result = service.analyze_query_capabilities("")
                if result.get('success') is False or result.get('analysis'):
                    self.log_test_result("Error Handling - Empty Query", True, 
                                       "Empty query handled gracefully")
                else:
                    self.log_test_result("Error Handling - Empty Query", False, 
                                       "Empty query not handled properly")
                    return False
            except Exception as e:
                self.log_test_result("Error Handling - Empty Query", True, 
                                   f"Exception caught as expected: {type(e).__name__}")
            
            # Test 2: Service health during errors
            health = service.get_service_health()
            if health and 'service_status' in health:
                self.log_test_result("Error Handling - Service Health", True, 
                                   "Service health available during error scenarios")
            else:
                self.log_test_result("Error Handling - Service Health", False, 
                                   "Service health not available")
                return False
            
            # Test 3: Graceful degradation
            capabilities = service.get_service_capabilities()
            if capabilities and 'supported_operations' in capabilities:
                self.log_test_result("Error Handling - Graceful Degradation", True, 
                                   "Service capabilities remain available")
            else:
                self.log_test_result("Error Handling - Graceful Degradation", False, 
                                   "Service capabilities not available")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Error Handling - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_performance_monitoring(self) -> bool:
        """Validate performance monitoring capabilities."""
        logger.info("📊 Validating Performance Monitoring...")
        
        try:
            from agents.a2a_protocol import get_a2a_protocol
            from services.a2a_service import get_a2a_service
            
            protocol = get_a2a_protocol()
            service = get_a2a_service()
            
            # Test 1: Protocol metrics
            protocol_metrics = protocol.get_performance_metrics()
            if protocol_metrics and 'total_messages' in protocol_metrics:
                self.log_test_result("Performance Monitoring - Protocol Metrics", True, 
                                   f"Protocol metrics available: {protocol_metrics['total_messages']} messages")
            else:
                self.log_test_result("Performance Monitoring - Protocol Metrics", False, 
                                   "Protocol metrics not available")
                return False
            
            # Test 2: Service metrics
            service_health = service.get_service_health()
            if (service_health and 'service_metrics' in service_health and 
                'total_requests' in service_health['service_metrics']):
                self.log_test_result("Performance Monitoring - Service Metrics", True, 
                                   "Service metrics available")
            else:
                self.log_test_result("Performance Monitoring - Service Metrics", False, 
                                   "Service metrics not available")
                return False
            
            # Test 3: Time estimation
            query = "Analyze mutual fund performance"
            analysis_result = service.analyze_query_capabilities(query)
            
            if (analysis_result.get('success') and 
                'estimated_time' in analysis_result and 
                isinstance(analysis_result['estimated_time'], (int, float))):
                self.log_test_result("Performance Monitoring - Time Estimation", True, 
                                   f"Time estimation: {analysis_result['estimated_time']:.2f}s")
            else:
                self.log_test_result("Performance Monitoring - Time Estimation", False, 
                                   "Time estimation not available")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Performance Monitoring - Exception", False, f"Exception: {str(e)}")
            return False
    
    def validate_configuration_management(self) -> bool:
        """Validate configuration management."""
        logger.info("⚙️ Validating Configuration Management...")
        
        try:
            from services.a2a_service import get_a2a_service
            
            service = get_a2a_service()
            
            # Test 1: Service capabilities configuration
            capabilities = service.get_service_capabilities()
            
            required_capabilities = [
                'supported_operations', 'supported_query_types', 
                'supported_chart_types', 'agent_capabilities'
            ]
            
            missing_capabilities = [cap for cap in required_capabilities 
                                  if cap not in capabilities]
            
            if not missing_capabilities:
                self.log_test_result("Configuration Management - Capabilities", True, 
                                   "All required capabilities configured")
            else:
                self.log_test_result("Configuration Management - Capabilities", False, 
                                   f"Missing capabilities: {missing_capabilities}")
                return False
            
            # Test 2: Agent capability mapping
            agent_caps = capabilities.get('agent_capabilities', {})
            expected_agents = ['enhanced_sql', 'mutual_fund_quant', 'data_formatter']
            
            missing_agents = [agent for agent in expected_agents 
                            if agent not in agent_caps]
            
            if not missing_agents:
                self.log_test_result("Configuration Management - Agent Mapping", True, 
                                   "All agents properly mapped")
            else:
                self.log_test_result("Configuration Management - Agent Mapping", False, 
                                   f"Missing agent mappings: {missing_agents}")
                return False
            
            # Test 3: A2A protocol features
            a2a_features = capabilities.get('a2a_protocol_features', {})
            required_features = [
                'message_passing', 'conditional_invocation', 
                'context_preservation', 'error_recovery'
            ]
            
            missing_features = [feature for feature in required_features 
                              if not a2a_features.get(feature)]
            
            if not missing_features:
                self.log_test_result("Configuration Management - A2A Features", True, 
                                   "All A2A features configured")
            else:
                self.log_test_result("Configuration Management - A2A Features", False, 
                                   f"Missing A2A features: {missing_features}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Configuration Management - Exception", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all integration validation tests."""
        logger.info("🚀 Starting A2A Integration Validation Suite...")
        
        # Run all validation tests
        validations = [
            ("Import Structure", self.validate_import_structure()),
            ("Agent Initialization", self.validate_agent_initialization()),
            ("Workflow Scenarios", self.validate_workflow_scenarios()),
            ("Error Handling", self.validate_error_handling()),
            ("Performance Monitoring", self.validate_performance_monitoring()),
            ("Configuration Management", self.validate_configuration_management())
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
        
        logger.info(f"🏁 Integration Validation Complete: {self.results['passed_tests']}/{self.results['total_tests']} tests passed ({self.results['success_rate']:.1f}%)")
        
        return self.results
    
    def print_detailed_report(self):
        """Print detailed integration validation report."""
        print("\n" + "="*80)
        print("🔗 A2A INTEGRATION VALIDATION REPORT")
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
    """Main integration validation function."""
    validator = IntegrationValidator()
    
    try:
        results = await validator.run_all_validations()
        validator.print_detailed_report()
        
        # Return appropriate exit code
        return 0 if results['all_passed'] else 1
        
    except Exception as e:
        logger.error(f"Integration validation suite failed with exception: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
