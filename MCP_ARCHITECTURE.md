# MCP Architecture Documentation

## Overview

This document describes the Model Context Protocol (MCP) based architecture implemented for the SQL Agent system. The MCP architecture provides enhanced security, modularity, and scalability by isolating AI agents into separate server processes.

## Architecture Components

### 1. MCP Servers

#### SQL Database MCP Server (`mcp_servers/sql_database_server.py`)
- **Port**: 8100
- **Responsibilities**:
  - Database discovery and connection management
  - SQL query execution with validation
  - Schema-per-tenant isolation
  - Query safety validation and sanitization
  - Database metadata retrieval

#### Financial Analytics MCP Server (`mcp_servers/financial_analytics_server.py`)
- **Port**: 8101
- **Responsibilities**:
  - Portfolio metrics calculation
  - Risk analysis (volatility, Sharpe ratio, max drawdown)
  - Correlation analysis
  - Mutual fund performance analysis
  - Financial insights generation

#### Visualization MCP Server (`mcp_servers/visualization_server.py`)
- **Port**: 8102
- **Responsibilities**:
  - Plotly chart generation
  - Data table formatting
  - Report generation
  - Chart file management
  - Multiple chart type support

### 2. MCP Client Infrastructure

#### MCP Client Manager (`services/mcp_client_manager.py`)
- Manages connections to all MCP servers
- Handles client initialization and lifecycle
- Provides unified interface for tool calls
- Implements health checks and reconnection logic
- Manages connection pooling and timeouts

#### MCP Orchestrator (`services/mcp_orchestrator.py`)
- **Drop-in replacement** for the original AgentOrchestrator
- Maintains exact same API for seamless migration
- Routes queries to appropriate MCP servers
- Combines results from multiple servers
- Preserves all existing functionality

### 3. Configuration and Management

#### MCP Configuration (`mcp_config.py`)
- Centralized configuration management
- Server port and connection settings
- Security and performance parameters
- Environment variable integration
- Configuration validation

#### Startup Scripts
- `start_mcp_servers.py`: Starts all MCP servers
- `start_mcp_system.py`: Complete system startup
- Process monitoring and health checks
- Graceful shutdown handling

## Security Enhancements

### 1. Process Isolation
- Each agent runs in separate process
- Prevents prompt injection between agents
- Isolated memory spaces
- Independent failure domains

### 2. Input Validation
- SQL query sanitization and validation
- Parameter validation at MCP server level
- Schema isolation enforcement
- Query safety checks

### 3. Communication Security
- MCP protocol for secure inter-process communication
- Structured message passing
- Error isolation and handling
- Audit logging capabilities

## API Compatibility

### Preserved Endpoints
All existing FastAPI endpoints remain unchanged:
- `POST /query` - Natural language query processing
- `GET /health` - System health check
- `POST /upload-files` - File upload functionality
- `GET /discovery/summary` - Database discovery
- `POST /agent/refresh` - Agent refresh

### Response Format Compatibility
The MCP orchestrator maintains exact compatibility with existing response formats:
```python
{
    "response": str,           # Generated response text
    "chart_files": List[str],  # Chart file paths
    "metadata": Dict[str, Any] # Additional metadata
}
```

## Deployment Guide

### 1. Environment Setup
```bash
# Install MCP dependencies
pip install -r requirements.txt

# Set required environment variables
export DATABASE_URL="your_database_url"
export OPENAI_API_KEY="your_openai_key"
export MCP_BASE_PORT=8100
export MCP_LOG_LEVEL=INFO
```

### 2. Start MCP System
```bash
# Option 1: Start complete system
python start_mcp_system.py

# Option 2: Start components separately
python start_mcp_servers.py  # Start MCP servers
python -m uvicorn multitenant_api:app --host 0.0.0.0 --port 8001  # Start API
```

### 3. Health Monitoring
```bash
# Check system health
curl http://localhost:8001/health

# Check MCP server status
curl http://localhost:8001/discovery/summary
```

## Migration Benefits

### 1. Enhanced Security
- **Process isolation** prevents prompt injection attacks
- **Input validation** at MCP server level
- **Schema isolation** enforced per tenant
- **Audit logging** for all operations

### 2. Improved Scalability
- **Horizontal scaling** of individual MCP servers
- **Load balancing** across server instances
- **Resource isolation** per agent type
- **Independent deployment** of servers

### 3. Better Maintainability
- **Modular architecture** with clear separation
- **Independent testing** of each component
- **Easier debugging** with isolated processes
- **Version management** per server

### 4. Zero Downtime Migration
- **Drop-in replacement** orchestrator
- **Backward compatible** API
- **Preserved functionality** without changes
- **Gradual rollout** capability

## Performance Considerations

### 1. Connection Management
- Connection pooling for MCP clients
- Persistent connections to reduce latency
- Health check monitoring
- Automatic reconnection on failures

### 2. Caching Strategy
- Query result caching at orchestrator level
- Schema metadata caching
- Chart file caching
- Configurable TTL settings

### 3. Resource Optimization
- Memory usage per isolated process
- CPU allocation per MCP server
- Network bandwidth for IPC
- Disk I/O for chart generation

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failures**
   - Check server process status
   - Verify port availability
   - Review server logs
   - Validate configuration

2. **Import Errors**
   - Ensure MCP dependencies installed
   - Check Python path configuration
   - Verify module imports

3. **Performance Issues**
   - Monitor connection pool usage
   - Check server resource utilization
   - Review query execution times
   - Optimize caching settings

### Monitoring Commands
```bash
# Check MCP server processes
ps aux | grep mcp_servers

# Monitor server logs
tail -f logs/mcp.log

# Test server connectivity
python -c "from services.mcp_client_manager import get_mcp_client_manager; print(get_mcp_client_manager().get_connection_status())"
```

## Development Workflow

### 1. Local Development
```bash
# Start development environment
python start_mcp_system.py

# Run tests
python -c "from services.mcp_orchestrator import get_mcp_orchestrator; print('MCP Integration OK')"

# Access API documentation
open http://localhost:8001/docs
```

### 2. Adding New MCP Servers
1. Create server class in `mcp_servers/`
2. Add configuration to `mcp_config.py`
3. Update client manager with new server
4. Add routing logic to orchestrator
5. Update startup scripts

### 3. Testing Strategy
- Unit tests for individual MCP servers
- Integration tests for client-server communication
- End-to-end tests for complete workflows
- Performance tests for scalability

## Future Enhancements

### Planned Features
1. **Load Balancing**: Multiple instances per server type
2. **Service Discovery**: Dynamic server registration
3. **Metrics Collection**: Prometheus integration
4. **Circuit Breakers**: Fault tolerance patterns
5. **API Gateway**: Centralized routing and auth

### Extensibility
- Plugin architecture for new agent types
- Custom MCP server implementations
- Third-party service integrations
- Multi-cloud deployment support

## Conclusion

The MCP-based architecture provides a robust, secure, and scalable foundation for the SQL Agent system while maintaining complete backward compatibility. The modular design enables independent scaling, enhanced security, and easier maintenance without disrupting existing workflows.
