# 🏦 Intelligent Mutual Fund Analysis Platform

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.3.4-black.svg)](https://nextjs.org)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive AI-powered platform for mutual fund analysis and investment research. Features natural language querying of 6M+ mutual fund records, advanced risk analytics, rolling returns analysis, and interactive visualizations. Built with MCP architecture for enhanced security, FastAPI backend, Next.js frontend, and powered by OpenAI GPT-4o.

## 🎯 Overview

This platform provides comprehensive mutual fund analysis capabilities through an intelligent AI agent that can:
- **Analyze 6M+ mutual fund records** across 1,478 schemes from 10 interconnected tables
- **Process natural language queries** about fund performance, risk metrics, and investment options
- **Generate advanced analytics** including rolling returns, Sharpe ratios, volatility analysis, and drawdown metrics
- **Create interactive visualizations** with automatic chart generation using Plotly
- **Provide investment insights** with peer group comparisons and index benchmarking
- **Support portfolio analysis** with risk-adjusted performance evaluation
- **Maintain data security** through schema-per-tenant architecture and MCP isolation

## 📊 Mutual Fund Database

### Comprehensive Data Coverage
The platform contains a complete mutual fund database with **6,078,093+ records** across **10 interconnected tables**:

#### Core Fund Information (1,478 schemes)
- **Schemes**: Complete fund details, categories, AUM, NAV, risk levels
- **Performance Returns**: 1D to 10Y returns across all time periods
- **BSE Trading**: Transaction capabilities, exit loads, lock-in periods
- **SIP Configurations**: Systematic investment parameters and limits
- **Transaction Rules**: Purchase and redemption guidelines

#### Advanced Analytics (3M+ records)
- **Historical NAV**: 3,037,708 daily NAV records (Apr 2006 - Sep 2025)
- **Historical Returns**: 3,036,230 records with daily and rolling returns
  - 88% coverage for 1-year rolling returns
  - 69% coverage for 3-year rolling returns  
  - 55% coverage for 5-year rolling returns
- **Risk Metrics**: 4,155+ comprehensive risk analysis records
  - Volatility, maximum drawdown, Value at Risk (VaR)
  - Sharpe and Sortino ratios with 6% risk-free rate
  - Beta/Alpha analysis vs peer groups and index benchmarks
  - Skewness, kurtosis, and distribution analysis

### Fund Categories Covered
- **Equity Funds**: Large Cap, Mid Cap, Small Cap, Multi Cap, Sectoral
- **Debt Funds**: Liquid, Ultra Short, Short Duration, Medium Duration, Long Duration
- **Hybrid Funds**: Conservative, Balanced, Aggressive, Dynamic Asset Allocation
- **Solution Oriented**: ELSS, Retirement Funds, Children's Funds
- **Other Schemes**: Index Funds, ETFs, FoFs, International Funds

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

### 🚀 Advanced Mutual Fund Analytics
- **Performance Analysis** - Rolling returns, absolute returns, and benchmark comparisons
- **Risk Assessment** - Volatility, drawdown, VaR, and risk-adjusted metrics
- **Peer Comparison** - Category-wise performance and risk analysis
- **Index Benchmarking** - Alpha/Beta analysis against appropriate index proxies
- **Portfolio Construction** - Multi-factor fund selection and diversification analysis
- **SIP Analysis** - Systematic investment planning and optimization
- **Market Timing** - Historical performance during different market cycles
- **Fund Screening** - Advanced filtering by performance, risk, and investment criteria

### 📈 Investment Research Capabilities
- **Natural Language Queries** - "Show me top performing large cap funds with low volatility"
- **Automated Insights** - AI-generated investment recommendations and analysis
- **Interactive Visualizations** - Performance charts, risk-return scatter plots, correlation matrices
- **Comparative Analysis** - Side-by-side fund comparisons with detailed metrics
- **Historical Backtesting** - Performance simulation across different time periods
- **Risk Profiling** - Comprehensive risk assessment with multiple metrics

## 📊 System Status

### Current Architecture State
- **Single Enhanced SQL Agent** - Streamlined from complex multi-agent system
- **Clean Codebase** - Removed 80% of obsolete code while preserving functionality
- **Production Ready** - Verified healthy with comprehensive testing
- **Zero Feature Loss** - All capabilities maintained in simplified architecture

### Database Architecture
- **Mutual Fund Database** - Primary database with 10 tables and 6M+ records
- **Schema-per-Tenant** - User isolation with email-based schemas for security
- **Optimized Indexes** - High-performance queries on large datasets
- **Real-time Updates** - Live data from MF APIs Club and MFApi.in
- **Cross-Table Analytics** - Complex joins across historical and current data

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

### Database Schema Details
- **mutual_fund** - Comprehensive mutual fund database with 10 interconnected tables
- **portfoliosql** - User portfolio and application data
- **Schema Isolation** - Each user gets dedicated schema for data privacy
- **Data Sources** - MF APIs Club, MFApi.in, and AMFI official data

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

### Example Mutual Fund Queries
```
"Show me top 10 large cap funds with highest 5-year returns"
"Find debt funds with lowest volatility and no exit load"
"Compare Sharpe ratios of mid cap vs small cap funds"
"Which ELSS funds have best risk-adjusted returns?"
"Show rolling returns chart for top performing hybrid funds"
"Find funds that outperformed during 2020 market crash"
"Display correlation matrix of top 5 equity fund categories"
"Which SIP options are available for funds under ₹1000 minimum?"
```

### Advanced Analytics Queries
```
"Calculate portfolio diversification using correlation analysis"
"Show maximum drawdown comparison across fund categories"
"Find funds with consistent performance over multiple market cycles"
"Analyze beta and alpha of funds vs their category benchmarks"
"Display Value at Risk (VaR) for high-risk equity funds"
"Compare Sortino ratios for downside risk assessment"
"Show funds with best risk-return profile using Sharpe ratios"
"Identify funds with lowest tail risk and stable returns"
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

## 📊 Performance & Analytics Features

### Query Performance
- **Optimized Indexes** - Fast queries on 6M+ records with sub-second response times
- **Intelligent Caching** - Agent and query result caching for improved performance
- **Parallel Processing** - Concurrent analysis across multiple fund categories
- **Smart Query Routing** - Automatic table selection based on query context

### Advanced Analytics Engine
- **Rolling Returns Calculation** - 1Y, 3Y, 5Y rolling performance analysis
- **Risk Metrics Computation** - Real-time volatility, drawdown, and VaR calculations
- **Benchmark Analysis** - Automated peer group and index comparisons
- **Statistical Analysis** - Correlation, regression, and distribution analysis
- **Performance Attribution** - Factor-based return decomposition

### Data Quality & Coverage
- **Historical Depth** - 19+ years of NAV data (April 2006 onwards)
- **Data Completeness** - 88% coverage for 1Y rolling returns across all schemes
- **Real-time Updates** - Live data integration from multiple sources
- **Data Validation** - Automated quality checks and anomaly detection

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

## 🎯 Use Cases

### For Individual Investors
- **Fund Research** - Comprehensive analysis before investment decisions
- **Portfolio Review** - Regular performance and risk assessment
- **SIP Planning** - Optimal systematic investment strategies
- **Risk Profiling** - Understanding fund risk characteristics

### For Financial Advisors
- **Client Recommendations** - Data-driven fund selection and advice
- **Portfolio Construction** - Diversified portfolio building with risk management
- **Performance Reporting** - Detailed client portfolio analysis and reporting
- **Market Research** - Staying updated with fund performance trends

### For Institutional Users
- **Due Diligence** - Comprehensive fund analysis for institutional investments
- **Benchmark Analysis** - Performance comparison against various benchmarks
- **Risk Management** - Portfolio risk assessment and monitoring
- **Research & Analytics** - Advanced quantitative analysis and insights

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
- **Database**: Follow PostgreSQL best practices for schema design

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MF APIs Club** - Comprehensive mutual fund data source
- **MFApi.in** - Additional mutual fund data and APIs
- **AMFI** - Official mutual fund industry data
- **OpenAI** - GPT-4o language model for natural language processing
- **LangChain** - Agent orchestration and SQL generation framework
- **FastAPI** - Modern Python web framework for high-performance APIs
- **Next.js** - React application framework for responsive frontend
- **Plotly** - Interactive visualization library for financial charts
- **PostgreSQL** - Robust database system for handling large datasets

## 📞 Support

For support and questions:
- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint on running server
- **Health Status**: `/health` endpoint for system diagnostics

---

**Built with ❤️ for intelligent data analysis and visualization**
