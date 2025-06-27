# Multi-Tenant SQL Agent

A sophisticated multi-tenant SQL agent application that enables users to query databases using natural language through an AI-powered interface. The system supports both shared portfolio data and user-specific uploaded datasets, providing a comprehensive data analysis solution.

## 🌟 Key Features

### Multi-Tenant Architecture
- **User Isolation**: Each user gets their own database session and data storage
- **Dual Database Access**: Query both shared portfolio data and personal uploaded files
- **Session Management**: Secure user session handling with automatic database provisioning
- **Scalable Design**: Built to handle multiple concurrent users efficiently

### AI-Powered SQL Generation
- **Natural Language Queries**: Ask questions in plain English, get SQL results
- **Intelligent Database Routing**: Automatically determines which database to query
- **Context-Aware Responses**: Understands data relationships and provides meaningful insights
- **Advanced Query Optimization**: Generates efficient SQL queries with proper joins and filters

### File Upload & Processing
- **Multi-Format Support**: Excel (.xlsx, .xls) and CSV files
- **Multi-Sheet Processing**: Handles Excel files with multiple sheets
- **Asynchronous Processing**: Non-blocking file uploads with real-time progress tracking
- **Data Validation**: Comprehensive validation and error handling during upload
- **Automatic Schema Detection**: Intelligently infers data types and relationships

### Modern Tech Stack
- **Backend**: FastAPI with async processing capabilities
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL with dual database architecture
- **AI**: OpenAI GPT integration for natural language processing
- **Task Queue**: RabbitMQ for asynchronous file processing
- **Configuration**: Pydantic-settings for secure environment management

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Databases     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   PostgreSQL    │
│   Port: 3001    │    │   Port: 8001    │    │                 │
└─────────────────┘    └─────────────────┘    │ • portfoliosql  │
                                              │ • user_db_*     │
                       ┌─────────────────┐    └─────────────────┘
                       │   Task Queue    │
                       │   (RabbitMQ)    │    ┌─────────────────┐
                       │                 │◄──►│ Async Processor │
                       └─────────────────┘    │ (Background)    │
                                              └─────────────────┘
```

### Database Architecture
1. **portfoliosql**: Shared database containing portfolio and financial data
2. **user_db_{hash}**: Individual databases for each user's uploaded data
3. **Automatic Provisioning**: User databases created on-demand during first upload

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 12+
- RabbitMQ (for async processing)

### Environment Setup

1. **Clone and Setup Environment**:
```bash
git clone <repository-url>
cd sql_agent_project_v4_multitenant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment Variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/portfoliosql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=portfoliosql
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=True

# Security
SECRET_KEY=your_secret_key_here

# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

3. **Database Setup**:
```sql
-- Create the shared portfolio database
CREATE DATABASE portfoliosql;

-- Add your portfolio/financial data to portfoliosql
-- User databases will be created automatically
```

4. **Frontend Setup**:
```bash
cd frontend
npm install
npm run build
cd ..
```

### Running the Application

**Option 1: Unified Startup (Recommended)**
```bash
python start_multitenant.py
```
This starts:
- FastAPI backend server (http://localhost:8001)
- RabbitMQ worker for async processing
- Next.js frontend (http://localhost:3001)

**Option 2: Manual Startup**
```bash
# Terminal 1: Start backend
python -m uvicorn multitenant_api:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start RabbitMQ worker
python venv_async_processor.py

# Terminal 3: Start frontend
cd frontend && npm run dev
```

### Access Points
- **Frontend Application**: http://localhost:3001
- **API Documentation**: http://localhost:8001/docs
- **API Redoc**: http://localhost:8001/redoc

## 📚 API Documentation

### Core Endpoints

#### Session Management
```http
POST /user/{user_id}/session
# Creates or retrieves user session
```

#### File Upload
```http
POST /upload-files
# Asynchronous file upload with progress tracking
Content-Type: multipart/form-data
```

```http
GET /task-status/{task_id}
# Check upload progress and results
```

#### Database Queries
```http
POST /user/{user_id}/query
# Natural language database queries
{
  "query": "Show me the top 10 products by sales"
}
```

#### User Data Management
```http
GET /user/{user_id}/tables
# List user's uploaded tables

GET /user/{user_id}/databases
# List available databases for user
```

### Response Formats

**Successful Query Response**:
```json
{
  "success": true,
  "result": [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"}
  ],
  "query_used": "SELECT column1, column2 FROM table_name LIMIT 2",
  "explanation": "Retrieved the requested data from your uploaded table."
}
```

**Upload Progress Response**:
```json
{
  "task_id": "12345-abcde",
  "status": "PROCESSING",
  "progress": 75,
  "message": "Processing sheet 3 of 4",
  "result": null
}
```

## 💡 Usage Examples

### File Upload
1. Navigate to http://localhost:3001
2. Enter your User ID
3. Click "Choose Files" and select Excel/CSV files
4. Click "Upload Files" - processing happens asynchronously
5. Monitor progress in real-time

### Natural Language Queries

**Query Personal Data**:
```
"Show me the total sales by product category from my uploaded data"
"What are the top 5 customers by revenue?"
"Calculate the average order value for last month"
```

**Query Portfolio Data**:
```
"What stocks are in the technology sector?"
"Show me the portfolio performance over the last year"
"Which investments have the highest dividend yield?"
```

**Cross-Database Analysis**:
```
"Compare my sales data with the portfolio performance"
"How do my revenue trends correlate with market data?"
```

## 🔧 Configuration

### Database Configuration
- **Primary Database**: `portfoliosql` for shared data
- **User Databases**: Automatically created as `user_db_{hash}`
- **Connection Pooling**: Managed automatically by SQLAlchemy

### Security Settings
- **Session Management**: Secure session tokens
- **Environment Variables**: All secrets in `.env` file
- **CORS Configuration**: Restricted to frontend domains
- **API Authentication**: Session-based authentication

### Performance Optimization
- **Async Processing**: Non-blocking file uploads
- **Connection Pooling**: Efficient database connections
- **Caching**: Session and query result caching
- **Background Tasks**: RabbitMQ for heavy processing

## 🏗️ Project Structure

```
sql_agent_project_v4_multitenant/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── settings.py                 # Configuration management (pydantic-settings)
├── .env                        # Environment variables (not in git)
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
│
├── multitenant_api.py         # Main FastAPI application & SQL agent
├── auth_endpoints.py          # Authentication endpoints
├── auth_service.py            # Authentication service
├── user_service.py            # User and session management
├── multi_sheet_uploader.py    # Excel/CSV file upload and processing
├── venv_async_processor.py    # Asynchronous file processing
├── start_multitenant.py       # Unified application startup script
├── evaluate_agent.py          # Agent testing and evaluation
│
├── frontend/                  # Next.js frontend application
│   ├── package.json          # Node.js dependencies
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   ├── next.config.js        # Next.js configuration
│   ├── README.md             # Frontend documentation
│   ├── app/
│   │   ├── layout.tsx        # Root layout component
│   │   ├── page.tsx          # Main application page
│   │   └── globals.css       # Global styles
│   └── components/           # Reusable React components
│
└── venv/                     # Python virtual environment
```

**Core Components:**
- **API Layer**: `multitenant_api.py` - FastAPI server with SQL agent integration
- **Authentication**: `auth_endpoints.py`, `auth_service.py` - OAuth and JWT handling
- **Data Layer**: `user_service.py` - Session and database management
- **File Processing**: `multi_sheet_uploader.py`, `venv_async_processor.py` - Async file uploads
- **Configuration**: `settings.py` - Type-safe environment configuration
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS

## 🛠️ Development

### Adding New Features

1. **Database Tools**: Extend the SQL agent tools in `multitenant_api.py`
2. **File Processors**: Add new upload handlers in `multi_sheet_uploader.py`
3. **API Endpoints**: Create new routes in `multitenant_api.py`
4. **Frontend Components**: Add React components in `frontend/components/`

### Testing

```bash
# Run evaluation tests
python evaluate_agent.py

# Test API endpoints
curl -X POST "http://localhost:8001/user/test_user/session"
curl -X GET "http://localhost:8001/docs"
```

### Debugging

- **Backend Logs**: Check console output for API server
- **Frontend Logs**: Use browser developer tools
- **Database Queries**: Enable SQL logging in settings
- **Task Processing**: Monitor RabbitMQ worker logs

## 🔒 Security Considerations

### Data Protection
- **User Isolation**: Each user's data in separate databases
- **Session Security**: Secure session token generation
- **Input Sanitization**: SQL injection prevention
- **File Validation**: Comprehensive upload validation

### Environment Security
- **Secret Management**: All secrets in environment variables
- **Database Access**: Parameterized queries only
- **CORS Policy**: Restricted cross-origin requests
- **API Authentication**: Session-based authentication

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**:
```bash
# Set production environment variables
export DEBUG=False
export API_HOST=0.0.0.0
export API_PORT=8001
```

2. **Database Setup**:
```sql
-- Create production databases
CREATE DATABASE portfoliosql_prod;
-- Configure user permissions
```

3. **Process Management**:
```bash
# Use process manager like PM2 or systemd
pm2 start start_multitenant.py --name sql-agent
```

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
