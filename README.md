# 🚀 Multi-Tenant SQL Agent

> A production-ready, AI-powered SQL agent with multi-tenant architecture, featuring natural language querying, file upload processing, and modern Gemini-style UI.

## ✨ Overview

This sophisticated multi-tenant SQL agent enables users to query databases using natural language through an AI-powered interface. The system supports both shared portfolio data and user-specific uploaded datasets, providing a comprehensive data analysis solution with enterprise-grade architecture.

## 🎯 Key Features

### 🏢 **Multi-Tenant Architecture**
- **Schema-per-Tenant**: Advanced multi-tenant isolation with dedicated database schemas
- **Database-per-Tenant**: Backward compatibility with legacy user databases
- **Smart Migration**: Automatic migration between architectures with zero downtime
- **Session Management**: Secure JWT-based authentication with Google OAuth
- **Feature Flags**: Gradual rollout capabilities for new features

### 🤖 **AI-Powered SQL Generation**
- **Natural Language Processing**: Ask questions in plain English, get SQL results
- **Intelligent Database Routing**: Automatically determines which database/schema to query
- **Context-Aware Responses**: Understands data relationships and provides meaningful insights
- **Advanced Query Optimization**: Generates efficient SQL with proper joins and filters
- **Error Handling**: Intelligent error recovery and query refinement

### 📁 **File Upload & Processing**
- **Multi-Format Support**: Excel (.xlsx, .xls) and CSV files
- **Multi-Sheet Processing**: Handles Excel files with multiple sheets automatically
- **Asynchronous Processing**: Celery-based background processing with Redis
- **Real-time Status**: WebSocket-like updates on upload progress
- **Data Validation**: Comprehensive validation and error handling
- **Schema Detection**: Automatic data type inference and table creation

### 🎨 **Modern Gemini-Style UI**
- **Clean Interface**: Google Gemini-inspired design with collapsible sidebar
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Real-time Chat**: Modern chat interface with message history
- **File Management**: Integrated file upload with attachment preview
- **Data Preview**: Right sidebar showing database table contents
- **Authentication**: Seamless Google OAuth integration

### 🏗️ **Production-Ready Architecture**
- **FastAPI Backend**: High-performance async API with automatic OpenAPI docs
- **Next.js Frontend**: Server-side rendering with TypeScript
- **PostgreSQL**: Robust database with multi-tenant support
- **Celery + Redis**: Distributed task processing with monitoring
- **Docker Integration**: Containerized services for easy deployment
- **Monitoring**: Flower dashboard for task monitoring

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Next.js App<br/>Port: 3001] --> B[Authentication<br/>Google OAuth]
        A --> C[Chat Interface<br/>Gemini Style]
        A --> D[File Upload<br/>Drag & Drop]
    end
    
    subgraph "API Layer"
        E[FastAPI Server<br/>Port: 8001] --> F[JWT Auth<br/>Middleware]
        E --> G[SQL Agent<br/>LangChain]
        E --> H[File Processing<br/>Endpoints]
    end
    
    subgraph "Task Processing"
        I[Celery Workers<br/>Background Tasks] --> J[File Processing<br/>Queue]
        I --> K[Query Processing<br/>Queue]
        I --> L[Maintenance<br/>Queue]
        M[Redis Broker<br/>Port: 6379] --> I
        N[Flower Dashboard<br/>Port: 5555] --> I
    end
    
    subgraph "Database Layer"
        O[PostgreSQL<br/>Multi-tenant]
        P[portfoliosql<br/>Shared Schema]
        Q[user_schema_*<br/>Tenant Schemas]
        R[user_db_*<br/>Legacy DBs]
    end
    
    A --> E
    E --> I
    E --> O
    O --> P
    O --> Q
    O --> R
```

### 🗄️ Database Architecture

**Multi-Tenant Database Strategy:**

1. **portfoliosql**: Central database with schema-per-tenant architecture
   - `public` schema: Shared portfolio/financial data
   - `user_schema_{id}`: Individual tenant schemas for uploaded data
   - `tenants` table: Tenant management and mapping
   - `chat_history` table: Persistent chat history storage

2. **user_db_{hash}**: Legacy database-per-tenant (backward compatibility)
   - Individual PostgreSQL databases for existing users
   - Automatic migration to schema-per-tenant available
   - Zero-downtime migration with feature flags

3. **Smart Database Routing**: Intelligent selection between architectures
   - Feature flags control migration rollout
   - Automatic fallback to legacy system
   - Seamless user experience during transition

## 🚀 Quick Start

### 📋 Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 12+**
- **Redis 6+** (for task processing)
- **Docker** (optional, for Redis)

### ⚙️ Environment Setup

**1. Clone and Setup Python Environment:**
```bash
git clone <repository-url>
cd sql_agent_project_v4_multitenant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure Environment Variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required Environment Variables:**
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key  # Optional for tracing

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/portfoliosql
PORTFOLIOSQL_DATABASE_URI=postgresql://username:password@localhost:5432/portfoliosql
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=True

# Security
SECRET_KEY=your_secret_key_here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Feature Flags
ENABLE_SCHEMA_PER_TENANT=true
ENABLE_AUTO_MIGRATION=true
```

**3. Database Setup:**
```sql
-- Create the central database
CREATE DATABASE portfoliosql;

-- Initialize schema-per-tenant structure
python initialize_schema_per_tenant.py
```

**4. Redis Setup:**
```bash
# Option 1: Using Docker (Recommended)
docker-compose up -d redis

# Option 2: Local Redis installation
# Install Redis locally and start service
```

**5. Frontend Setup:**
```bash
cd frontend
npm install
npm run build
cd ..
```

## 🎬 Running the Application

### 🔥 **Option 1: Production Mode (Recommended)**
```bash
python start_production.py
```
**Starts all services:**
- ✅ Redis broker
- ✅ FastAPI backend (http://localhost:8001)
- ✅ Next.js frontend (http://localhost:3001)
- ✅ Celery workers (background processing)
- ✅ Celery beat (scheduled tasks)
- ✅ Flower dashboard (http://localhost:5555)

### 🛠️ **Option 2: Development Mode**
```bash
python start_multitenant.py
```
**Starts basic services:**
- ✅ FastAPI backend (http://localhost:8001)
- ✅ Next.js frontend (http://localhost:3001)
- ⚠️ **Note**: Start Celery workers separately for full functionality

### ⚡ **Option 3: Individual Components**
```bash
# Terminal 1: Backend API
python -m uvicorn multitenant_api:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Celery Worker (Essential for file uploads)
python start_celery_worker.py

# Terminal 3: Celery Beat (Optional - for maintenance tasks)
python start_celery_beat.py

# Terminal 4: Flower Monitoring (Optional)
python start_celery_flower.py

# Terminal 5: Frontend
cd frontend && npm run dev
```

### 🌐 Access Points
- **🎨 Frontend Application**: http://localhost:3001
- **🔧 API Documentation**: http://localhost:8001/docs
- **📚 API Redoc**: http://localhost:8001/redoc
- **🌸 Flower Dashboard**: http://localhost:5555 (admin/password)
- **⚡ Redis**: localhost:6379

## 📚 API Documentation

### 🔑 Authentication Endpoints
```http
GET /auth/google/login
# Initiate Google OAuth login flow

GET /auth/google/callback
# Handle Google OAuth callback

GET /auth/me
# Get current user information
Authorization: Bearer {jwt_token}
```

### 📁 File Upload Endpoints
```http
POST /upload-files
# Upload Excel/CSV files for processing
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}
Body: files[]
```

```http
GET /task-status/{task_id}
# Check background task status
Authorization: Bearer {jwt_token}
```

### 🔍 Query Endpoints
```http
POST /query
# Natural language database queries
Authorization: Bearer {jwt_token}
Content-Type: application/json
{
  "query": "Show me the top 10 products by sales",
  "session_id": "optional_session_id"
}
```

### 🗄️ User Data Management
```http
GET /user/tables
# List user's uploaded tables
Authorization: Bearer {jwt_token}

GET /user/databases
# List available databases for user
Authorization: Bearer {jwt_token}
```

### 🔄 Migration Endpoints
```http
GET /migration/status
# Check user's migration status
Authorization: Bearer {jwt_token}

POST /migration/trigger
# Manually trigger migration to schema-per-tenant
Authorization: Bearer {jwt_token}
```

### ❤️ Health Check
```http
GET /health
# API health status (no authentication required)
```

### 📦 Response Formats

**Successful Query Response:**
```json
{
  "success": true,
  "result": [
    {"product": "Widget A", "sales": 15000},
    {"product": "Widget B", "sales": 12000}
  ],
  "query_used": "SELECT product, sales FROM products ORDER BY sales DESC LIMIT 2",
  "explanation": "Retrieved top products by sales from your uploaded data.",
  "execution_time": 0.043
}
```

**File Upload Task Status:**
```json
{
  "task_id": "60021753-7e6e-4e5c-aee4-39f55eedd934",
  "status": "SUCCESS",
  "progress": 100,
  "message": "File processing completed successfully",
  "result": {
    "tables_created": 6,
    "total_rows": 97,
    "processing_time": 2.34,
    "sheets": ["Products", "Orders", "Customers"]
  }
}
```

**Authentication Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

## 🎆 Usage Examples

### 🔑 **Authentication Flow**
1. Visit **http://localhost:3001**
2. Click **"Continue with Google"**
3. Complete OAuth flow in popup
4. Automatically redirected to chat interface

### 📁 **File Upload Workflow**
1. **Click attachment button** (📎) in chat input
2. **Select Excel/CSV files** (supports multi-sheet Excel)
3. **Files upload automatically** with real-time progress
4. **Background processing** creates database tables
5. **Chat confirmation** shows tables created and row counts

### 💬 **Chat Interface Usage**

**Query Your Uploaded Data:**
```
📋 "Show me the top 10 products by sales volume"
📊 "What's the average order value by customer segment?"
📈 "Create a summary of monthly revenue trends"
🎯 "Which customers have the highest lifetime value?"
```

**Query Portfolio/Market Data:**
```
💹 "What tech stocks are performing best this quarter?"
💰 "Show me dividend-paying stocks with yield > 3%"
📉 "Compare sector performance year-to-date"
🌍 "What are the top emerging market investments?"
```

**Cross-Database Analysis:**
```
🔄 "How does my business revenue correlate with market trends?"
🤝 "Compare my sales performance with industry benchmarks"
🔍 "Find patterns between my customer data and economic indicators"
```

### 🎨 **Modern UI Features**
- **🧠 Sidebar Navigation**: Hover to expand, shows chat history
- **📝 Message Bubbles**: Clean Gemini-style conversation flow
- **📏 File Attachments**: Drag-and-drop or click to upload
- **🔄 Real-time Updates**: Live progress tracking
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🌙 Dark/Light Theme**: Automatic theme detection

## ⚙️ Configuration

### 🗄️ **Database Architecture**
- **Central Database**: `portfoliosql` with schema-per-tenant
- **Legacy Support**: `user_db_{hash}` databases with migration path
- **Smart Routing**: Automatic selection based on feature flags
- **Connection Pooling**: SQLAlchemy with async support

### 🔒 **Security Configuration**
- **JWT Authentication**: 8-hour token expiry
- **Google OAuth**: Secure third-party authentication
- **Environment Variables**: All secrets externalized
- **CORS Policy**: Restricted to allowed origins
- **Session Security**: Secure HTTP-only cookies

### ⚡ **Performance Features**
- **Celery + Redis**: Background task processing
- **Async Operations**: Non-blocking file uploads
- **Connection Pooling**: Efficient database connections
- **Caching Strategy**: Query and session caching
- **Load Balancing**: Ready for horizontal scaling

### 📡 **Task Processing Queues**
- **file_processing**: Excel/CSV upload processing
- **query_processing**: Natural language SQL queries  
- **maintenance**: Cleanup and health checks
- **default**: General background tasks

## 🏗️ Project Structure

```
sql_agent_project_v4_multitenant/
├── README.md                    # 📚 Project documentation
├── requirements.txt             # 🐍 Python dependencies  
├── settings.py                 # ⚙️ Configuration (pydantic-settings)
├── .env                        # 🔒 Environment variables (not in git)
├── .env.example               # 📝 Environment template
├── .gitignore                 # 🚫 Git ignore rules
├── docker-compose.yml         # 🐳 Redis container config
│
├── multitenant_api.py         # 🖥️ Main FastAPI app & SQL agent
├── auth_endpoints.py          # 🔑 Authentication endpoints
├── auth_service.py            # 🛡️ Authentication service
├── user_service.py            # 👥 User and session management
├── multi_sheet_uploader.py    # 📁 Excel/CSV upload processing
│
├── celery_config.py           # 🌿 Celery configuration
├── celery_tasks.py            # ⚡ Background task definitions
├── schema_dependencies.py     # 🗄️ Schema-per-tenant dependencies
├── data_migration.py          # 🔄 Database migration utilities
├── initialize_schema_per_tenant.py # 🏗 Schema initialization
│
├── start_production.py        # 🚀 Production deployment
├── start_multitenant.py       # 🛠️ Development startup
├── start_celery_worker.py     # ⚡ Worker startup
├── start_celery_beat.py       # ⏰ Scheduler startup
├── start_celery_flower.py     # 🌸 Monitoring dashboard
│
├── frontend/                  # ⚙️ Next.js 15 + TypeScript + Tailwind
│   ├── package.json          # 📦 Node.js dependencies
│   ├── tailwind.config.js    # 🎨 Tailwind CSS config
│   ├── next.config.js        # ⚡ Next.js configuration
│   ├── app/
│   │   ├── layout.tsx        # 🏠 Root layout (Gemini-style)
│   │   ├── page.tsx          # 🏠 Main chat interface
│   │   └── globals.css       # 🎨 Global styles
│   └── components/           # ⚙️ Reusable React components
│
└── venv/                     # 🐍 Python virtual environment
```

### 🔧 **Core Components**

**🔥 Backend Architecture:**
- **multitenant_api.py**: FastAPI server with SQL agent integration
- **celery_tasks.py**: Background processing (file uploads, queries)
- **schema_dependencies.py**: Smart database routing & multi-tenant logic
- **auth_service.py**: Google OAuth + JWT authentication
- **multi_sheet_uploader.py**: Excel/CSV processing with pandas

**🎨 Frontend Architecture:**
- **Next.js 15**: React 18+ with TypeScript
- **Tailwind CSS**: Modern utility-first styling
- **Gemini-style UI**: Chat interface with sidebar navigation
- **Real-time Updates**: WebSocket-like task progress tracking

**📡 Task Processing:**
- **Celery + Redis**: Production-ready async task queue
- **Flower Dashboard**: Task monitoring and debugging
- **Queue Management**: Separate queues for different task types

## 🛠️ Development Guide

### 🎆 **Adding New Features**

**1. New API Endpoints:**
```python
# In multitenant_api.py
@app.post("/your-endpoint")
async def your_endpoint(request: YourRequest, current_user: dict = Depends(get_current_user)):
    # Your logic here
    return {"result": "success"}
```

**2. Background Tasks:**
```python
# In celery_tasks.py
@celery_app.task(bind=True)
def your_background_task(self, data):
    # Long-running task logic
    return {"status": "completed"}
```

**3. Frontend Components:**
```typescript
// In frontend/components/YourComponent.tsx
export function YourComponent() {
  return <div className="p-4 bg-white rounded-lg">Your content</div>
}
```

### 📝 **Testing & Validation**

**API Testing:**
```bash
# Health check
curl http://localhost:8001/health

# Authentication test
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8001/auth/me

# Upload test (with file)
curl -X POST -F "files=@test.xlsx" -H "Authorization: Bearer TOKEN" http://localhost:8001/upload-files
```

**Database Validation:**
```bash
# Initialize schema-per-tenant
python initialize_schema_per_tenant.py

# Run migration script
python data_migration.py

# Check migration status
curl -H "Authorization: Bearer TOKEN" http://localhost:8001/migration/status
```

### 🔍 **Debugging & Troubleshooting**

**Common Issues & Solutions:**

🐛 **"401 Unauthorized" errors**
```bash
# Solution: Refresh browser to get new JWT token (8-hour expiry)
# Check token status
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/auth/me
```

🐛 **File upload processing fails**
```bash
# Solution: Restart Celery workers
python start_celery_worker.py

# Check task status
curl http://localhost:8001/task-status/YOUR_TASK_ID
```

🐛 **Celery worker not starting**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Check Redis connection
redis-cli ping

# Restart Redis via Docker
docker-compose restart redis
```

🐛 **Database connection errors**
```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check database exists
psql -U your_user -l | grep portfoliosql

# Initialize schema if needed
python initialize_schema_per_tenant.py
```

**Monitoring & Logs:**
- **API Logs**: Console output from FastAPI server
- **Celery Logs**: Worker output shows task processing
- **Frontend Logs**: Browser DevTools Console
- **Task Monitoring**: http://localhost:5555 (Flower dashboard)
- **Database Logs**: Enable query logging in PostgreSQL

## 🔒 Security & Best Practices

### 🛡️ **Data Protection**
- **Multi-Tenant Isolation**: Schema-per-tenant with proper access controls
- **JWT Security**: 8-hour token expiry with secure HTTP-only cookies
- **Input Sanitization**: SQL injection prevention via parameterized queries
- **File Validation**: Comprehensive Excel/CSV upload validation
- **User Data Isolation**: Each tenant's data completely isolated

### 🔐 **Environment Security**
- **Secret Management**: All credentials in environment variables
- **Database Security**: Connection pooling with proper authentication
- **CORS Policy**: Restricted to allowed frontend origins
- **Google OAuth**: Secure third-party authentication flow
- **API Rate Limiting**: Built-in FastAPI security features

### 📊 **Performance & Monitoring**
- **Async Processing**: Non-blocking file uploads and queries
- **Connection Pooling**: Efficient database connection management
- **Task Queues**: Separate queues for different operation types
- **Monitoring Dashboard**: Real-time task and system monitoring
- **Error Tracking**: Comprehensive logging and error reporting

## 🚀 Production Deployment

### 🏗️ **Production Setup**

**1. Environment Configuration:**
```bash
# Production environment variables
export DEBUG=false
export API_HOST=0.0.0.0
export API_PORT=8001
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
export ENABLE_SCHEMA_PER_TENANT=true
export ENABLE_AUTO_MIGRATION=true

# Database URLs for production
export DATABASE_URL="postgresql://user:pass@prod-db:5432/portfoliosql"
export PORTFOLIOSQL_DATABASE_URI="postgresql://user:pass@prod-db:5432/portfoliosql"

# Redis configuration
export REDIS_URL="redis://prod-redis:6379/0"
export CELERY_BROKER_URL="redis://prod-redis:6379/0"
export CELERY_RESULT_BACKEND="redis://prod-redis:6379/0"
```

**2. Production Deployment:**
```bash
# All-in-one production startup
python start_production.py

# Or with process manager
pm2 start start_production.py --name "sql-agent-prod"

# Monitor processes
pm2 monit
```

**3. Docker Deployment:**
```bash
# Start Redis container
docker-compose up -d redis

# Build and run application
docker build -t sql-agent .
docker run -d --name sql-agent-app -p 8001:8001 sql-agent
```

### 📈 **Scaling & Performance**
- **Horizontal Scaling**: Add more Celery workers across machines
- **Database Scaling**: PostgreSQL read replicas for query performance
- **Load Balancing**: Multiple FastAPI instances behind load balancer
- **Caching**: Redis for session and query result caching
- **CDN**: Static asset delivery for frontend

## 🎆 Features & Roadmap

### ✅ **Current Features**
- 📁 **Multi-format Upload**: Excel, CSV with multi-sheet support
- 🤖 **AI-Powered Queries**: Natural language to SQL conversion
- 👥 **Multi-Tenant Architecture**: Secure data isolation
- 🔄 **Zero-Downtime Migration**: Database architecture migration
- 🎨 **Modern UI**: Gemini-style chat interface
- 🔑 **Google OAuth**: Secure authentication
- ⚡ **Background Processing**: Async file processing
- 📈 **Task Monitoring**: Real-time progress tracking
- 📱 **Responsive Design**: Mobile-friendly interface

### 🔮 **Future Enhancements**
- 🧠 **Advanced Analytics**: Data visualization and insights
- 📊 **Dashboard Builder**: Custom dashboard creation
- 🔄 **API Integrations**: Connect external data sources
- 🤖 **Enhanced AI**: More sophisticated query understanding
- 📱 **Mobile App**: Native mobile application
- 🌍 **Multi-Language**: Internationalization support

---

## 📝 **Support & Documentation**

- **📚 Full Documentation**: This README.md
- **🔧 API Docs**: http://localhost:8001/docs (Interactive Swagger UI)
- **📚 API Reference**: http://localhost:8001/redoc (ReDoc format)
- **🌸 Task Monitor**: http://localhost:5555 (Flower dashboard)
- **🐛 Issue Tracking**: Report bugs via GitHub issues
- **✨ Feature Requests**: Suggest enhancements via GitHub discussions

**Built with ❤️ by the team** | **Powered by OpenAI GPT, FastAPI, Next.js & PostgreSQL**

### Scaling Considerations
- **Database**: Use connection pooling and read replicas
- **Task Queue**: Scale RabbitMQ workers horizontally
- **Frontend**: Deploy to CDN for static assets
- **API**: Use load balancer for multiple backend instances

## 🔧 Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Check database connectivity
psql -h localhost -U your_user -d portfoliosql
```

**File Upload Failures**:
- Check file size limits
- Verify file format compatibility
- Monitor RabbitMQ worker logs

**Query Errors**:
- Verify database schema
- Check user permissions
- Review SQL generation logs

**Frontend Issues**:
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Performance Issues
- Monitor database query performance
- Check RabbitMQ queue status
- Review memory usage of workers
- Optimize database indexes

### Getting Help
- Check API documentation at `/docs`
- Review application logs
- Verify environment configuration
- Test with minimal examples

## 📈 Performance Metrics

### Benchmarks
- **File Upload**: ~1MB/second processing rate
- **Query Response**: <2 seconds for complex queries
- **Concurrent Users**: Tested with 50+ simultaneous users
- **Database Operations**: Optimized for <100ms response time

### Monitoring
- **API Metrics**: Built-in FastAPI metrics
- **Database Performance**: Query execution time logging
- **Task Queue**: RabbitMQ management interface
- **Resource Usage**: Memory and CPU monitoring

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **TypeScript**: Use strict type checking
- **SQL**: Use parameterized queries
- **Documentation**: Update README for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT integration
- FastAPI team for the excellent framework
- Next.js team for the frontend framework
- PostgreSQL community for the robust database
- RabbitMQ team for the message queue system

---

**Version**: 4.0  
**Last Updated**: 2025-06-26  
**Maintained By**: Development Team
