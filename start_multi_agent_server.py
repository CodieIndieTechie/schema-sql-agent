#!/usr/bin/env python3
"""
Multi-Agent System Server Startup Script

This script starts the FastAPI server with the integrated multi-agent system.
It provides both the existing SQL agent functionality and new multi-agent capabilities.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the multi-agent system server"""
    
    print("🚀 Starting Multi-Agent Financial Analysis System...")
    print("=" * 60)
    print("📊 Features Available:")
    print("  • Enhanced Multi-Database SQL Agent")
    print("  • Multi-Agent Financial Analysis")
    print("  • Mutual Fund Expert Insights")
    print("  • Web Research Integration")
    print("  • Data Visualization & Formatting")
    print("  • Schema-per-Tenant Architecture")
    print("  • Real-Time Streaming Updates")
    print("=" * 60)
    
    # Environment checks
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set. Multi-agent features will not work.")
    
    # Configuration summary
    print("🔧 Configuration:")
    print(f"  • Max Agent Iterations: {os.getenv('MAX_AGENT_ITERATIONS', '10')}")
    print(f"  • Agent Timeout: {os.getenv('AGENT_TIMEOUT_SECONDS', '300')}s")
    print(f"  • Web Research: {'Enabled' if os.getenv('ENABLE_WEB_RESEARCH', 'true').lower() == 'true' else 'Disabled'}")
    print(f"  • Chart Generation: {'Enabled' if os.getenv('ENABLE_CHART_GENERATION', 'true').lower() == 'true' else 'Disabled'}")
    print(f"  • Agent Caching: {'Enabled' if os.getenv('ENABLE_AGENT_CACHING', 'true').lower() == 'true' else 'Disabled'}")
    print()
    
    print("🌐 Server Starting:")
    print("  • API Server: http://localhost:8001")
    print("  • API Documentation: http://localhost:8001/docs")
    print("  • Multi-Agent Endpoints: http://localhost:8001/multi-agent/")
    print("  • Health Check: http://localhost:8001/multi-agent/health")
    print()
    
    # Start the server
    try:
        uvicorn.run(
            "multitenant_api:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Multi-Agent System Server stopped.")
    except Exception as e:
        print(f"\n❌ Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
