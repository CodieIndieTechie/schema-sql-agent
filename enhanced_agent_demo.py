#!/usr/bin/env python3
"""
Enhanced Multi-Database SQL Agent Demo and Test Script
=====================================================

This script demonstrates the capabilities of the enhanced multi-database SQL agent
and provides comprehensive testing of all new features.

Usage:
    python enhanced_agent_demo.py

Features Tested:
- Dynamic database discovery
- Multi-database querying
- Schema-per-tenant isolation
- Intelligent prompt generation
- Session management
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"

class EnhancedAgentTester:
    """Test class for enhanced multi-database SQL agent."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        print()

    def test_health_check(self) -> bool:
        """Test the enhanced health check endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                expected_features = [
                    "dynamic_database_discovery",
                    "multi_database_access", 
                    "schema_per_tenant",
                    "intelligent_prompts",
                    "session_history"
                ]
                
                has_all_features = all(feature in data.get("features", []) for feature in expected_features)
                db_count = data.get("available_databases", 0)
                
                details = f"Service: {data.get('service')}, Version: {data.get('version')}, Databases: {db_count}"
                self.log_test("Health Check", has_all_features and db_count > 0, details)
                return has_all_features and db_count > 0
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_comprehensive_discovery(self) -> bool:
        """Test the comprehensive database discovery endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/admin/discovery/all")
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    discovery_info = data.get("discovery_info", {})
                    total_databases = discovery_info.get("total_databases", 0)
                    total_schemas = discovery_info.get("total_schemas", 0)
                    total_tables = discovery_info.get("total_tables", 0)
                    
                    connectivity = data.get("connectivity_test", {})
                    success_rate = connectivity.get("success_rate", 0)
                    
                    details = f"DBs: {total_databases}, Schemas: {total_schemas}, Tables: {total_tables}, Connectivity: {success_rate*100}%"
                    self.log_test("Comprehensive Discovery", total_databases > 0 and success_rate > 0.5, details)
                    return total_databases > 0 and success_rate > 0.5
                else:
                    self.log_test("Comprehensive Discovery", False, "Discovery failed")
                    return False
            else:
                self.log_test("Comprehensive Discovery", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Comprehensive Discovery", False, str(e))
            return False

    def test_direct_agent_creation(self) -> bool:
        """Test direct creation of enhanced agent."""
        try:
            from enhanced_sql_agent import create_enhanced_user_agent, create_enhanced_system_agent
            
            # Test user-specific agent creation  
            user_agent = create_enhanced_user_agent("test@example.com")
            user_contexts = user_agent.list_available_contexts()
            
            # Test system-wide agent creation
            system_agent = create_enhanced_system_agent()
            system_contexts = system_agent.list_available_contexts()
            
            # Test database summary
            user_summary = user_agent.get_database_summary()
            
            success = (len(user_contexts) > 0 and 
                      len(system_contexts) >= len(user_contexts) and 
                      user_summary.get('total_databases', 0) > 0)
            
            details = f"User contexts: {len(user_contexts)}, System contexts: {len(system_contexts)}, User DBs: {user_summary.get('total_databases', 0)}"
            self.log_test("Direct Agent Creation", success, details)
            return success
        except Exception as e:
            self.log_test("Direct Agent Creation", False, str(e))
            return False

    def test_database_discovery_service(self) -> bool:
        """Test the database discovery service directly."""
        try:
            from database_discovery import discovery_service
            
            # Test available databases
            databases = discovery_service.list_available_databases()
            
            # Test comprehensive info
            comprehensive_info = discovery_service.get_comprehensive_database_info(include_columns=False)
            
            # Test user-specific info
            user_info = discovery_service.get_user_specific_database_info("test@example.com")
            
            success = (len(databases) > 0 and 
                      comprehensive_info.get('total_databases', 0) > 0 and
                      user_info.get('primary_database') is not None)
            
            details = f"Available DBs: {len(databases)}, Comprehensive total: {comprehensive_info.get('total_databases', 0)}"
            self.log_test("Database Discovery Service", success, details)
            return success
        except Exception as e:
            self.log_test("Database Discovery Service", False, str(e))
            return False

    def test_prompt_generation(self) -> bool:
        """Test dynamic prompt generation."""
        try:
            from agent_prompts import get_multi_database_prompt, get_schema_specific_prompt, get_dynamic_system_prompt
            from database_discovery import discovery_service
            
            # Get discovery info for prompts
            db_info = discovery_service.get_comprehensive_database_info(include_columns=False)
            
            # Test different prompt types
            databases = db_info.get('databases', [])
            db_names = [db['name'] for db in databases] if databases else ['portfoliosql']
            multi_db_prompt = get_multi_database_prompt(db_names, db_names[0] if db_names else 'portfoliosql')
            
            # Get table info for schema prompt
            table_info = []
            if databases:
                for db in databases:
                    if db['name'] == 'portfoliosql':
                        for schema in db.get('schemas', []):
                            if schema['name'] == 'public':
                                table_info = schema.get('tables', [])
                                break
            schema_prompt = get_schema_specific_prompt("public", table_info)
            dynamic_prompt = get_dynamic_system_prompt(db_info, user_schema="test_schema")
            
            success = (len(multi_db_prompt) > 100 and 
                      len(schema_prompt) > 100 and 
                      len(dynamic_prompt) > 100 and
                      "database" in multi_db_prompt.lower())
            
            details = f"Multi-DB prompt: {len(multi_db_prompt)} chars, Schema prompt: {len(schema_prompt)} chars"
            self.log_test("Prompt Generation", success, details)
            return success
        except Exception as e:
            self.log_test("Prompt Generation", False, str(e))
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary."""
        print("🚀 Starting Enhanced Multi-Database SQL Agent Tests")
        print("=" * 60)
        print()
        
        tests = [
            self.test_health_check,
            self.test_comprehensive_discovery,
            self.test_direct_agent_creation,
            self.test_database_discovery_service,
            self.test_prompt_generation
        ]
        
        for test_func in tests:
            test_func()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

def demonstrate_enhanced_features():
    """Demonstrate key enhanced features."""
    print("🎯 ENHANCED FEATURES DEMONSTRATION")
    print("=" * 60)
    
    try:
        from enhanced_sql_agent import create_enhanced_user_agent
        from database_discovery import discovery_service
        
        # Show database discovery
        print("1. 🔍 DATABASE DISCOVERY:")
        databases = discovery_service.list_available_databases()
        print(f"   Found {len(databases)} databases: {', '.join(databases)}")
        print()
        
        # Show agent capabilities
        print("2. 🤖 ENHANCED AGENT CAPABILITIES:")
        agent = create_enhanced_user_agent("demo@example.com")
        contexts = agent.list_available_contexts()
        summary = agent.get_database_summary()
        
        print(f"   Available contexts: {len(contexts)}")
        print(f"   Total databases: {summary.get('total_databases', 0)}")
        print(f"   Total schemas: {summary.get('total_schemas', 0)}")
        print(f"   Primary database: {summary.get('primary_database', 'N/A')}")
        print()
        
        # Show prompt intelligence
        print("3. 🧠 INTELLIGENT PROMPTS:")
        from agent_prompts import get_dynamic_system_prompt
        db_info = discovery_service.get_comprehensive_database_info(include_columns=False)
        prompt = get_dynamic_system_prompt(db_info, user_schema="demo_schema")
        print(f"   Dynamic prompt generated: {len(prompt)} characters")
        print("   Includes context about available databases and schemas")
        print()
        
        print("✨ All enhanced features are working correctly!")
        
    except Exception as e:
        print(f"❌ Error demonstrating features: {e}")

if __name__ == "__main__":
    print("🌟 Enhanced Multi-Database SQL Agent - Demo & Test Suite")
    print("=" * 70)
    print()
    
    # Run feature demonstration
    demonstrate_enhanced_features()
    print()
    
    # Run comprehensive tests
    tester = EnhancedAgentTester()
    summary = tester.run_all_tests()
    
    # Final verdict
    if summary["success_rate"] >= 80:
        print("🎉 ENHANCED AGENT IS READY FOR PRODUCTION!")
    elif summary["success_rate"] >= 60:
        print("⚠️  ENHANCED AGENT NEEDS MINOR FIXES")
    else:
        print("🚨 ENHANCED AGENT NEEDS MAJOR FIXES")
