# MCP-Based SQL Analysis System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.3.4-black.svg)](https://nextjs.org)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A secure, modular multi-agent system for natural language SQL analysis using Model Context Protocol (MCP) architecture. Features enhanced security through process isolation, dynamic database discovery, interactive chart generation, and schema-per-tenant architecture. Built with FastAPI, Next.js, and powered by OpenAI GPT-4o.

## 🎯 Overview

This system provides an intelligent SQL agent that can:
- **Discover databases dynamically** across multiple PostgreSQL instances
- **Process natural language queries** and convert them to SQL
- **Generate interactive visualizations** using Plotly
- **Handle file uploads** with multi-sheet Excel/CSV processing
- **Maintain user isolation** through schema-per-tenant architecture
- **Provide real-time responses** with streaming support

## 🏗️ MCP Architecture

### 🔒 Enhanced Security Through Process Isolation

The system now uses **Model Context Protocol (MCP)** to isolate AI agents into separate server processes, providing enhanced security against prompt injection attacks and improved modularity.

### MCP Servers (Isolated Processes)
1. **SQL Database MCP Server** (`mcp_servers/sql_database_server.py`) - Port 8100
   - Database discovery and connection management
   - SQL query generation and execution with validation
   - Multi-database context switching
   - Schema-per-tenant isolation enforcement
   - Query safety validation and sanitization

2. **Financial Analytics MCP Server** (`mcp_servers/financial_analytics_server.py`) - Port 8101
   - Financial analysis and calculations
   - Risk metrics and performance analysis (Sharpe ratio, volatility, max drawdown)
   - Portfolio optimization algorithms
   - Correlation analysis and insights

3. **Visualization MCP Server** (`mcp_servers/visualization_server.py`) - Port 8102
   - Interactive Plotly chart generation
   - Data visualization and formatting
   - Professional report creation
   - Chart file management and serving

### MCP Infrastructure
- **MCP Client Manager** (`services/mcp_client_manager.py`)
  - Manages connections to all MCP servers
  - Handles client lifecycle and health monitoring
  - Provides unified interface for tool calls

- **MCP Orchestrator** (`services/mcp_orchestrator.py`)
  - **Drop-in replacement** for original orchestrator
  - Routes queries to appropriate MCP servers
  - Combines results from multiple servers
  - Maintains backward compatibility

## 🚀 Features

### 🔐 MCP Security Benefits
- ✅ **Process Isolation** - Each agent runs in separate process, preventing prompt injection
- ✅ **Input Validation** - SQL query sanitization and validation at MCP server level
- ✅ **Schema Isolation** - Enforced tenant separation with audit logging
- ✅ **Fault Tolerance** - Independent failure domains for each agent type

### Core Capabilities
- ✅ **Dynamic Database Discovery** - Automatically discovers 4+ databases, 48+ schemas, 3,362+ tables
- ✅ **Natural Language Processing** - Convert plain English to SQL queries
- ✅ **Interactive Visualizations** - Generate charts, graphs, and plots automatically
- ✅ **Multi-Database Support** - Query across multiple PostgreSQL databases
- ✅ **Schema-per-Tenant** - User isolation with individual database schemas
- ✅ **File Upload Processing** - Handle Excel/CSV files with background processing
- ✅ **Real-time Streaming** - Live query results and status updates
- ✅ **Google OAuth Integration** - Secure authentication with Google accounts

### Advanced Features
- **Financial Analysis** - Specialized mutual fund and portfolio analysis
- **Chart Generation** - Automatic visualization based on query context
- **Background Processing** - Celery-based task queue for file uploads
- **Session Management** - Conversation history and context preservation
- **Health Monitoring** - Comprehensive system health checks
- **Admin Dashboard** - System statistics and management tools

## 📊 System Status

### Current Architecture State
- **Single Enhanced SQL Agent** - Streamlined from complex multi-agent system
- **Clean Codebase** - Removed 80% of obsolete code while preserving functionality
- **Production Ready** - Verified healthy with comprehensive testing
- **Zero Feature Loss** - All capabilities maintained in simplified architecture

### Database Connectivity
- **3 Active Databases** - portfoliosql, chatfolio_db, stockdata_db
- **Schema-per-Tenant** - User isolation with email-based schemas
- **Dynamic Discovery** - Automatic table and column detection
- **Cross-Database Queries** - Query multiple databases in single request

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration and agent framework
- **OpenAI GPT-4o** - Natural language processing
- **PostgreSQL** - Primary database with multi-tenant support
- **SQLAlchemy** - Database ORM and connection management
- **Celery + Redis** - Background task processing
- **Plotly** - Interactive chart generation

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **Google OAuth** - Authentication integration

## 🚦 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+
- OpenAI API key

### Backend Setup

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd sql_agent_project_v6
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration:
# - OPENAI_API_KEY
# - DATABASE_URL
# - GOOGLE_CLIENT_ID
# - GOOGLE_CLIENT_SECRET

# MCP-specific configuration (optional)
# - MCP_BASE_PORT=8100
# - MCP_LOG_LEVEL=INFO
# - MCP_ENABLE_CACHING=true
```

3. **Start MCP-based system**
```bash
# Option 1: Start complete MCP system (recommended)
python start_mcp_system.py

# Option 2: Start components separately
python start_mcp_servers.py  # Start MCP servers (ports 8100-8102)
uvicorn multitenant_api:app --reload --host 0.0.0.0 --port 8001  # Start API

# Option 3: Start Celery worker for background tasks (if needed)
python start_celery_worker.py
```

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Configure environment**
```bash
cp .env.local.example .env.local
# Add your Google OAuth credentials
```

3. **Start development server**
```bash
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **MCP Servers**: http://localhost:8100-8102 (SQL, Analytics, Visualization)

## 📡 API Endpoints

### Core Endpoints
- `POST /query` - Process natural language queries
- `POST /upload-files` - Upload Excel/CSV files
- `GET /user/tables` - List user's tables
- `GET /health` - System health check

### Discovery & Management
- `GET /discovery/databases` - Get database discovery info
- `GET /discovery/summary` - Agent status and database summary
- `POST /agent/refresh` - Refresh agent with updated discovery
- `GET /agent/contexts` - List available database contexts

### Chart & Visualization
- `GET /charts/{filename}` - Serve generated chart files
- `GET /charts/{filename}/embed` - Embeddable chart content

### Authentication
- `POST /auth/google` - Google OAuth login
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - User logout

### Admin Endpoints
- `GET /admin/sessions` - Active session statistics
- `GET /admin/databases` - Database information
- `GET /admin/discovery/all` - Comprehensive discovery

## 💾 Database Schema

### Schema-per-Tenant Architecture
Each user gets an isolated schema based on their email:
```sql
-- User: user@example.com gets schema: user_12345678
CREATE SCHEMA user_12345678;
-- All user tables created in their isolated schema
```

### Multi-Database Support
- **portfoliosql** - Main application database
- **chatfolio_db** - Chat and session data
- **stockdata_db** - Financial market data
- **Mutual_Fund_Holdings** - Mutual fund portfolio data

## 📈 Chart Generation

### Automatic Visualization
The system automatically generates charts when queries contain visualization keywords:
- `chart`, `graph`, `plot`, `visualize`, `show me`, `display`

### Chart Types
- **Bar Charts** - Categorical data comparison
- **Line Charts** - Time series and trends
- **Pie Charts** - Proportional data
- **Scatter Plots** - Correlation analysis
- **Tables** - Structured data display

### Example Queries
```
"Create a chart of sales by region"
"Show me a line graph of portfolio performance over time"
"Visualize the top 10 mutual funds by AUM"
"Display a pie chart of asset allocation"
```

## 🔧 Configuration

### Environment Variables
```bash
# Core Configuration
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/portfoliosql

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Optional
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3001
```

### Agent Configuration
Agents are configured through `agent_prompts.py`:
- **System prompts** for each agent type
- **Database context** templates
- **Response formatting** instructions

## 🧪 Testing

### Backend Testing
```bash
# Health check
curl http://localhost:8001/health

# Test query (no auth required)
curl -X POST http://localhost:8001/query-no-auth \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all tables"}'
```

### Frontend Testing
```bash
cd frontend
npm run build  # Test production build
npm run lint   # Check code quality
```

## 🚀 Deployment

### Production Deployment
1. **Environment Setup**
```bash
# Use production environment file
cp .env.example .env.production
# Configure production values
```

2. **Start Production Server**
```bash
python start_production.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3001
# - Backend: http://localhost:8001
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

## 📊 Performance & Monitoring

### System Health
- **Health Endpoint**: `/health` provides comprehensive system status
- **Database Connectivity**: Monitors all database connections
- **Agent Status**: Tracks active agents and their performance
- **Memory Usage**: Monitors system resource utilization

### Optimization Features
- **Agent Caching** - Reuse agents per user for performance
- **Connection Pooling** - Efficient database connection management
- **Query Optimization** - Intelligent SQL generation and execution
- **Background Processing** - Non-blocking file upload processing

## 🔍 Troubleshooting

### Common Issues

#### "No response received" Error
- **Cause**: Agent configuration or database connectivity issues
- **Solution**: Check health endpoint, verify database connections

#### Chart Generation Failures
- **Cause**: Missing Plotly dependencies or file permissions
- **Solution**: Ensure `plotly` and `kaleido` are installed, check `static/charts/` directory

#### File Upload Not Processing
- **Cause**: Celery worker not running or Redis connection issues
- **Solution**: Start Celery worker, verify Redis connectivity

#### Authentication Issues
- **Cause**: Google OAuth configuration problems
- **Solution**: Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in environment

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python multitenant_api.py
```

### Health Checks
Monitor system health:
```bash
# Check all services
curl http://localhost:8001/health

# Check specific components
curl http://localhost:8001/discovery/summary
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- **Python**: Follow PEP 8 guidelines
- **TypeScript**: Use ESLint configuration
- **Documentation**: Update README for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - GPT-4o language model
- **LangChain** - Agent orchestration framework
- **FastAPI** - Modern Python web framework
- **Next.js** - React application framework
- **Plotly** - Interactive visualization library

## 📞 Support

For support and questions:
- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint on running server
- **Health Status**: `/health` endpoint for system diagnostics

---

**Built with ❤️ for intelligent data analysis and visualization**
