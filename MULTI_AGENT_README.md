# Multi-Agent Financial Analysis System

## Overview

This project extends the existing multi-database SQL agent with a comprehensive multi-agent system for financial data analysis. The system coordinates multiple specialized agents to provide intelligent, context-aware responses to financial queries about Indian mutual funds and market data.

## Architecture

### Core Components

1. **Multi-Agent Orchestrator** - Coordinates all agents and manages workflows
2. **SQL Agent Wrapper** - Integrates existing SQL agent with multi-agent system
3. **Mutual Fund Expert Agent** - Provides specialized financial analysis
4. **Web Research Agent** - Gathers current market information
5. **Data Formatter Agent** - Creates beautiful visualizations and reports

### Key Features

- **Dynamic Workflow Selection** - Automatically chooses appropriate agents based on query complexity
- **Schema-per-Tenant Architecture** - Maintains user isolation and data security
- **Real-Time Streaming** - Provides live updates during query processing
- **Comprehensive Configuration** - Environment-based configuration management
- **Health Monitoring** - Built-in health checks and system monitoring
- **Intelligent Caching** - Optimized performance with multi-level caching

## API Endpoints

### Multi-Agent System Endpoints

#### Core Query Processing
- `POST /multi-agent/query` - Process queries through multi-agent system
- `POST /multi-agent/query/stream` - Stream real-time processing updates

#### System Management
- `GET /multi-agent/health` - Get system health status
- `GET /multi-agent/workflows` - Get available workflows and capabilities
- `GET /multi-agent/config` - Get current system configuration

#### Agent Management
- `POST /multi-agent/agents/refresh/{user_email}` - Refresh user's cached agents
- `GET /multi-agent/agents/status` - Get detailed agent status

#### Testing
- `POST /multi-agent/test` - Test multi-agent system functionality

## Configuration

The system is configured through environment variables:

### Core Configuration
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
AGENT_MODEL=gpt-4o
AGENT_TEMPERATURE=0.3
AGENT_MAX_TOKENS=3000

# Orchestrator Configuration
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300
ENABLE_AGENT_CACHING=true

# Feature Toggles
ENABLE_WEB_RESEARCH=true
WEB_SEARCH_ENABLED=false
ENABLE_CHART_GENERATION=true
MUTUAL_FUND_EXPERT_ENABLED=true

# Web Agent Configuration
WEB_SCRAPING_TIMEOUT=30
MAX_WEB_SOURCES=5

# Data Formatter Configuration
MAX_CHART_DATA_POINTS=100

# Expert Agent Configuration
FINANCIAL_ANALYSIS_DEPTH=comprehensive
```

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the Server**
   ```bash
   python start_multi_agent_server.py
   ```

4. **Access the API**
   - API Documentation: http://localhost:8001/docs
   - Health Check: http://localhost:8001/multi-agent/health

## Usage Examples

### Simple Query
```python
import requests

response = requests.post("http://localhost:8001/multi-agent/query", json={
    "query": "What are the top performing large cap mutual funds?",
    "user_email": "user@example.com",
    "enable_caching": true
})

print(response.json())
```

### Streaming Query
```python
import requests

response = requests.post("http://localhost:8001/multi-agent/query/stream", json={
    "query": "Compare HDFC Top 100 and ICICI Prudential Bluechip funds",
    "user_email": "user@example.com"
}, stream=True)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

### Health Check
```python
import requests

health = requests.get("http://localhost:8001/multi-agent/health")
print(health.json())
```

## Workflows

The system supports multiple workflow types:

1. **Simple Query** - Direct SQL queries for basic data retrieval
2. **Full Analysis with Web** - Comprehensive analysis with current market data
3. **Comparison Analysis** - Side-by-side comparison of financial instruments
4. **Portfolio Analysis** - Portfolio-level insights and recommendations

## Agent Descriptions

### SQL Agent Wrapper
- Integrates existing enhanced SQL agent
- Handles multi-database queries
- Manages schema-per-tenant isolation
- Provides database schema information

### Mutual Fund Expert Agent
- Specialized in Indian mutual fund analysis
- Provides investment insights and recommendations
- Supports performance analysis and comparison
- Generates expert commentary

### Web Research Agent
- Gathers current market information
- Researches financial news and trends
- Provides real-time market context
- Supports configurable data sources

### Data Formatter Agent
- Creates beautiful charts and visualizations
- Formats data into professional reports
- Supports multiple output formats
- Generates executive summaries

## Integration with Existing System

The multi-agent system seamlessly integrates with the existing SQL agent infrastructure:

- **Schema-per-Tenant**: Maintains existing user isolation
- **Database Discovery**: Uses existing database discovery service
- **Authentication**: Integrates with existing auth system
- **File Uploads**: Works with existing file processing
- **Celery Tasks**: Compatible with background processing

## Development

### Project Structure
```
agents/
├── __init__.py                 # Agent exports
├── base_agent.py              # Abstract base class
├── agent_configs.py           # Configuration and prompts
├── sql_agent_wrapper.py       # SQL agent integration
├── mutual_fund_expert.py      # Financial expert agent
├── web_agent.py               # Web research agent
├── data_formatter.py          # Data formatting agent
└── multi_agent_orchestrator.py # Main orchestrator

api/
├── __init__.py                # API exports
└── multi_agent_api.py         # FastAPI endpoints

config/
├── __init__.py                # Config exports
└── multi_agent_config.py      # Configuration management

services/
├── __init__.py                # Service exports
└── multi_agent_service.py     # Business logic layer
```

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement required methods (`process_message`, `get_capabilities`)
3. Add agent to orchestrator initialization
4. Update configuration if needed

### Testing

Run the test endpoint to verify system functionality:
```bash
curl -X POST http://localhost:8001/multi-agent/test
```

## Monitoring and Debugging

### Health Monitoring
- System health endpoint provides comprehensive status
- Individual agent health checks
- Performance metrics and statistics
- Error tracking and logging

### Logging
- Structured logging throughout the system
- Configurable log levels
- Agent-specific log contexts
- Performance timing logs

### Debugging
- Debug mode available in development
- Detailed error messages
- Agent interaction tracing
- Configuration validation

## Production Deployment

### Performance Optimization
- Agent caching for improved response times
- Database connection pooling
- Async processing for scalability
- Configuration-based feature toggles

### Security
- Environment-based configuration
- API key management
- User session isolation
- Input validation and sanitization

### Monitoring
- Health check endpoints
- Performance metrics
- Error rate monitoring
- System resource tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the health check endpoint
3. Check system logs for errors
4. Contact the development team
