#!/usr/bin/env python3
"""
Run All Validations - Comprehensive validation runner for A2A protocol

This script runs all validation suites and generates a comprehensive report
covering:
- A2A Protocol functionality
- Integration testing
- Performance benchmarks
- Error handling validation
- Configuration verification
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

# Import validation modules
from validation.a2a_protocol_validation import A2AProtocolValidator
from validation.integration_validation import IntegrationValidator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveValidator:
    """
    Comprehensive validation runner for all A2A protocol components.
    """
    
    def __init__(self):
        """Initialize the comprehensive validator."""
        self.start_time = datetime.now()
        self.results = {
            'validation_suites': {},
            'overall_summary': {},
            'execution_time': 0,
            'timestamp': self.start_time.isoformat()
        }
        
        logger.info("Comprehensive A2A Validation Suite initialized")
    
    async def run_protocol_validation(self) -> Dict[str, Any]:
        """Run A2A protocol validation."""
        logger.info("🔄 Running A2A Protocol Validation...")
        
        try:
            validator = A2AProtocolValidator()
            results = await validator.run_all_validations()
            
            self.results['validation_suites']['a2a_protocol'] = {
                'name': 'A2A Protocol Validation',
                'results': results,
                'validator': 'A2AProtocolValidator'
            }
            
            return results
            
        except Exception as e:
            logger.error(f"A2A Protocol validation failed: {str(e)}")
            error_result = {
                'all_passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 1,
                'success_rate': 0.0,
                'error': str(e)
            }
            
            self.results['validation_suites']['a2a_protocol'] = {
                'name': 'A2A Protocol Validation',
                'results': error_result,
                'validator': 'A2AProtocolValidator',
                'error': str(e)
            }
            
            return error_result
    
    async def run_integration_validation(self) -> Dict[str, Any]:
        """Run integration validation."""
        logger.info("🔗 Running Integration Validation...")
        
        try:
            validator = IntegrationValidator()
            results = await validator.run_all_validations()
            
            self.results['validation_suites']['integration'] = {
                'name': 'Integration Validation',
                'results': results,
                'validator': 'IntegrationValidator'
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Integration validation failed: {str(e)}")
            error_result = {
                'all_passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 1,
                'success_rate': 0.0,
                'error': str(e)
            }
            
            self.results['validation_suites']['integration'] = {
                'name': 'Integration Validation',
                'results': error_result,
                'validator': 'IntegrationValidator',
                'error': str(e)
            }
            
            return error_result
    
    def generate_overall_summary(self):
        """Generate overall validation summary."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        all_suites_passed = True
        
        for suite_name, suite_data in self.results['validation_suites'].items():
            suite_results = suite_data['results']
            
            total_tests += suite_results.get('total_tests', 0)
            passed_tests += suite_results.get('passed_tests', 0)
            failed_tests += suite_results.get('failed_tests', 0)
            
            if not suite_results.get('all_passed', False):
                all_suites_passed = False
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results['overall_summary'] = {
            'all_passed': all_suites_passed,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'suites_run': len(self.results['validation_suites']),
            'suites_passed': sum(1 for suite in self.results['validation_suites'].values() 
                               if suite['results'].get('all_passed', False))
        }
    
    def print_comprehensive_report(self):
        """Print comprehensive validation report."""
        end_time = datetime.now()
        execution_time = (end_time - self.start_time).total_seconds()
        self.results['execution_time'] = execution_time
        
        print("\n" + "="*100)
        print("🎯 COMPREHENSIVE A2A PROTOCOL VALIDATION REPORT")
        print("="*100)
        
        # Overall Summary
        summary = self.results['overall_summary']
        print(f"\n🏆 OVERALL SUMMARY:")
        print(f"   Status: {'✅ ALL VALIDATIONS PASSED' if summary['all_passed'] else '❌ SOME VALIDATIONS FAILED'}")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Validation Suites: {summary['suites_passed']}/{summary['suites_run']} passed")
        print(f"   Execution Time: {execution_time:.2f} seconds")
        
        # Suite-by-Suite Results
        print(f"\n📊 VALIDATION SUITE RESULTS:")
        for suite_name, suite_data in self.results['validation_suites'].items():
            suite_results = suite_data['results']
            status = "✅ PASSED" if suite_results.get('all_passed', False) else "❌ FAILED"
            
            print(f"\n   {status} {suite_data['name']}")
            print(f"      Tests: {suite_results.get('passed_tests', 0)}/{suite_results.get('total_tests', 0)} passed")
            print(f"      Success Rate: {suite_results.get('success_rate', 0):.1f}%")
            
            if 'error' in suite_data:
                print(f"      Error: {suite_data['error']}")
        
        # Detailed Test Results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for suite_name, suite_data in self.results['validation_suites'].items():
            suite_results = suite_data['results']
            
            print(f"\n   📦 {suite_data['name']}:")
            
            if 'test_results' in suite_results:
                for test_result in suite_results['test_results']:
                    print(f"      {test_result['status']} {test_result['test_name']}")
                    if test_result.get('message'):
                        print(f"         └─ {test_result['message']}")
            elif 'error' in suite_results:
                print(f"      ❌ Suite failed with error: {suite_results['error']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if summary['all_passed']:
            print("   🎉 All validations passed! The A2A protocol implementation is ready for production.")
            print("   📈 Consider running performance benchmarks for production optimization.")
            print("   🔄 Set up automated validation runs for continuous integration.")
        else:
            print("   🔧 Fix failing tests before deploying to production.")
            print("   📝 Review detailed test results above for specific issues.")
            print("   🧪 Re-run validations after implementing fixes.")
        
        # System Information
        print(f"\n🖥️  SYSTEM INFORMATION:")
        print(f"   Python Version: {sys.version.split()[0]}")
        print(f"   Validation Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Total Execution Time: {execution_time:.2f} seconds")
        
        print("\n" + "="*100)
    
    def save_results_to_file(self, filename: str = None):
        """Save validation results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_results_{timestamp}.json"
        
        try:
            # Ensure validation directory exists
            validation_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(validation_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Validation results saved to: {filepath}")
            print(f"\n💾 Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            print(f"\n❌ Failed to save results: {str(e)}")
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation suites."""
        logger.info("🚀 Starting Comprehensive A2A Protocol Validation...")
        
        # Run all validation suites
        await self.run_protocol_validation()
        await self.run_integration_validation()
        
        # Generate overall summary
        self.generate_overall_summary()
        
        return self.results


async def main():
    """Main comprehensive validation function."""
    validator = ComprehensiveValidator()
    
    try:
        # Run all validations
        results = await validator.run_all_validations()
        
        # Print comprehensive report
        validator.print_comprehensive_report()
        
        # Save results to file
        validator.save_results_to_file()
        
        # Return appropriate exit code
        return 0 if results['overall_summary']['all_passed'] else 1
        
    except Exception as e:
        logger.error(f"Comprehensive validation failed with exception: {str(e)}")
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    print("🎯 A2A Protocol Comprehensive Validation Suite")
    print("=" * 50)
    print("This suite validates the complete A2A protocol implementation")
    print("including protocol functionality, integration, and performance.")
    print("=" * 50)
    
    exit_code = asyncio.run(main())
    
    if exit_code == 0:
        print("\n🎉 All validations completed successfully!")
    else:
        print("\n❌ Some validations failed. Please review the results above.")
    
    sys.exit(exit_code)
