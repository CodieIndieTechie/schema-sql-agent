#!/usr/bin/env python3
"""
Multi-Tenant API Server for SQL Agent

Provides REST API endpoints for multi-tenant functionality with user-specific
database instances and Excel sheet-to-table conversion.
"""

import os
import uuid
import tempfile
import logging
from datetime import datetime
from typing import List, Optional, Any, Union
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from settings import settings
import os

# Force set OpenAI API key in environment to override any cached values
os.environ['OPENAI_API_KEY'] = settings.openai_api_key
from schema_user_service import schema_user_service
from auth_service import get_current_user, User
from schema_dependencies import (
    get_db_session_with_schema, get_user_schema_info, ensure_user_schema
)
from auth_endpoints import include_auth_routes
from multi_sheet_uploader import MultiSheetExcelUploader
from celery_tasks import create_file_processing_task, get_task_status
from services.mcp_orchestrator import get_mcp_orchestrator
from database_discovery import discovery_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class UserSessionResponse(BaseModel):
    user_id: str
    schema: str
    created_at: str
    message_count: int
    table_count: int


class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    user_id: str
    schema: str
    success: bool
    error: Optional[str] = None
    chart_file: Optional[str] = None
    chart_type: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    schema: str
    tables_created: List[str]
    total_rows: int
    sheets_processed: int
    files_processed: int
    errors: List[str]


class TableInfo(BaseModel):
    table_name: str
    source_file: str
    sheet_name: Optional[str]
    uploaded_at: str


class UserTablesResponse(BaseModel):
    user_id: str
    schema: str
    tables: List[TableInfo]


class AsyncUploadResponse(BaseModel):
    task_id: str
    status: str
    message: str
    user_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    status: str
    result: Optional[Any] = None
    error: Optional[Union[str, List[str]]] = None
    current: Optional[int] = None
    total: Optional[int] = None
    files_processed: Optional[int] = None
    sheets_processed: Optional[int] = None


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Tenant SQL Agent API",
    description="Multi-tenant SQL Agent with user-specific databases and Excel sheet processing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the application and start async worker."""
    print("🚀 Starting Multi-Tenant SQL Agent API Server...")
    print("👥 Multi-tenant mode enabled")
    print("📊 LangSmith tracing enabled")
    print(f"🌐 Frontend will be available at: {settings.frontend_base_url}")
    print(f"🔗 API documentation: {settings.api_docs_url}")
    print(f"🔗 API endpoint: {settings.api_base_url}")
    
    # Celery workers should be started separately
    print("🔄 Celery task queue ready (start workers with: celery -A celery_config worker)")
    print("📊 Celery monitoring available with: celery -A celery_config flower")

# Global services
from multi_sheet_uploader import MultiSheetExcelUploader

uploader = MultiSheetExcelUploader()

# Function to invalidate a user's agent cache (no longer needed with orchestrator)
def invalidate_user_agent(user_id: str):
    """Legacy function - agent invalidation handled by orchestrator."""
    logger.info(f"ℹ️ Agent invalidation requested for user: {user_id} (handled by orchestrator)")

# In-memory store for session histories.
session_histories = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    """
    Retrieves the chat history for a given session ID.
    If no history exists, a new one is created.
    """
    if session_id not in session_histories:
        session_histories[session_id] = ChatMessageHistory()
    return session_histories[session_id]

def clear_session_history(session_id: str) -> bool:
    """
    Clears the chat history for a given session ID.
    Returns True if history was cleared, False if no history existed.
    """
    if session_id in session_histories:
        session_histories[session_id].clear()
        return True
    return False

# Note: User sessions now managed through schema_user_service
# Individual user session management removed as part of schema-per-tenant simplification


# SQL Agent creation function
def create_multitenant_sql_agent(database_uri: str, schema_name: str = None) -> AgentExecutor:
    """Create a SQL agent for schema-per-tenant architecture."""
    try:
        # Use mutual_fund_db database which contains the bse_details table
        mutual_fund_db_uri = settings.get_database_uri("mutual_fund_db")
        db = SQLDatabase.from_uri(mutual_fund_db_uri)
        
        # Initialize OpenAI LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Create SQL toolkit for the user's schema
        from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
        
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()
        
        # System prompt for mutual fund database access
        system_prompt = """You are a helpful SQL expert assistant with access to the mutual_fund_db PostgreSQL database.

You have access to a comprehensive mutual fund database containing:

**Available Tables:**
- `schemes`: Main table with 1,488 mutual fund schemes (scheme_code, scheme_name, amfi_broad, amfi_sub, amc_code, current_nav, aum_in_lakhs, risk_level, sip_allowed, purchase_allowed)
- `bse_details`: BSE trading information for 2,891 records (scheme_id, bse_code, sip_flag, stp_flag, swp_flag, purchase_allowed, sip_min_amount, sip_max_amount)
- `returns_history`: Time-series returns data for 9,827 records (scheme_id, period, return_value, data_date)
- `historical_nav_data`: Historical NAV data in JSONB format (scheme_id, nav_history, data_start_date, data_end_date)
- `complete_nav_history`: Complete NAV history records

**IMPORTANT - AUM Data Formatting:**
- The `aum_in_lakhs` column stores values in Indian Lakhs (1 Lakh = 100,000 rupees)
- When displaying AUM values, ALWAYS multiply by 100,000 (10^5) to convert from lakhs to rupees
- Example: If aum_in_lakhs = 196049.8, display as ₹19,60,49,80,000 (196049.8 × 100,000)
- Use proper Indian number formatting with commas for readability

**IMPORTANT - Returns Data Parsing:**
- The `returns_data` column contains JSONB data with time period keys and return values
- JSON format example: {{"1d": -0.05, "1m": 0.03, "1y": 9.23, "3y": 12.45, "5y": 15.67}}
- Time period keys: "1d" (1 day), "1m" (1 month), "6m" (6 months), "1y" (1 year), "3y" (3 years), "5y" (5 years), "10y" (10 years)
- Use PostgreSQL JSONB operators to extract specific returns: returns_data->>'1y' for 1-year returns
- Example SQL: SELECT scheme_name, returns_data->>'1y' as return_1y FROM schemes WHERE returns_data IS NOT NULL
- Always convert extracted values to numeric and format as percentages for display

**Key Relationships:**
- schemes.id ↔ bse_details.scheme_id
- schemes.id ↔ returns_history.scheme_id
- schemes.id ↔ historical_nav_data.scheme_id

**Available Views:**
- `scheme_summary`: Comprehensive scheme overview with aggregated metrics
- `top_performers`: Best performing schemes ranked by returns
- `category_performance`: Category-wise performance analysis

**IMPORTANT - Query Guidelines:**
1. Be efficient: Use the minimum number of tool calls needed to answer the question
2. First check available tables with sql_db_list_tables if needed
3. Then query the data with sql_db_query, limiting results to 5 rows unless specified
4. Provide your final answer immediately after getting the query results
5. Don't repeatedly query the same information
6. If you get an error, try a simpler approach instead of complex workarounds

**AUM Display Rules:**
- When showing AUM values, ALWAYS convert from lakhs to rupees by multiplying by 100,000
- Format numbers with Indian comma notation (e.g., ₹19,60,49,80,000)
- Never show raw lakh values to users - always convert to full rupee amounts

**Returns Data Query Rules:**
- When users ask for returns for specific time periods, use JSONB operators to extract the correct values
- Map user queries to JSON keys: "1 year" → "1y", "3 years" → "3y", "1 month" → "1m", etc.
- Use SQL like: SELECT scheme_name, (returns_data->>'1y')::numeric as return_1y FROM schemes
- Format return values as percentages (multiply by 100 if needed and add % symbol)
- Handle NULL values gracefully - show "N/A" if returns data is missing

**Response Format:**
- Execute necessary tools to get the data
- Apply AUM conversion and returns parsing before displaying results
- Use proper JSONB extraction for returns data based on user's time period request
- Provide a clear, concise answer based on the results
- Stop after providing the answer - don't ask follow-up questions

Remember: Be direct and efficient. Answer the user's question with the data you retrieve, then stop."""
        
        # Create modern prompt structure with chat history support
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create modern tool-calling agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        # Create agent executor with enhanced capabilities
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,  # Set to True for debugging
            handle_parsing_errors=True,
            max_iterations=75,  # Further increased for complex multi-database queries
            max_execution_time=180,  # 3 minute timeout
            return_intermediate_steps=True,  # Enable for better debugging and evaluation
        )
        
        # Wrap with message history for persistent conversations
        agent_with_history = RunnableWithMessageHistory(
            agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
        return agent_with_history
        
    except Exception as e:
        raise Exception(f"Failed to create dual-database SQL agent: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Tenant SQL Agent API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint with enhanced agent statistics."""
    try:
        # Test database connection
        from schema_migration import schema_db
        with schema_db.get_session() as session:
            session.execute(text("SELECT 1"))
        
        # Get database discovery summary
        try:
            available_databases = discovery_service.list_available_databases()
            db_count = len(available_databases)
        except Exception:
            available_databases = []
            db_count = 0
        
        # Get MCP orchestrator health stats
        orchestrator = get_mcp_orchestrator(static_dir="static/charts")
        orchestrator_health = await orchestrator.get_health_status()
        orchestrator_stats = orchestrator.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "three-agent-pipeline-system",
            "version": "4.0.0",
            "database": "connected",
            "orchestrator_status": orchestrator_health.get('orchestrator', 'unknown'),
            "agent_pipeline": {
                "enhanced_sql_agent": "✅ Active",
                "mutual_fund_quant_agent": "✅ Active", 
                "data_formatter_agent": "✅ Active"
            },
            "execution_stats": orchestrator_stats.get('execution_stats', {}),
            "available_databases": db_count,
            "database_names": available_databases,
            "features": [
                "three_agent_pipeline",
                "dynamic_database_discovery",
                "multi_database_access", 
                "schema_per_tenant",
                "quantitative_analysis",
                "plotly_visualizations",
                "intelligent_orchestration"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Legacy session endpoints removed - using schema-per-tenant architecture


@app.post("/query-test", response_model=QueryResponse)
async def query_database_test(request: QueryRequest):
    """Test endpoint without authentication to verify agent functionality."""
    try:
        # Use anonymous user for testing
        from schema_user_service import SchemaUserSession
        test_user_email = "test@example.com"
        
        # Ensure test schema exists
        ensure_user_schema(test_user_email)
        
        # Create database URI for portfoliosql
        from settings import get_portfoliosql_connection
        engine = get_portfoliosql_connection()
        db_uri = str(engine.url)
        
        # Create SQL agent
        agent_with_history = create_multitenant_sql_agent(db_uri, schema_name="test_schema")
        
        # Execute query
        result = agent_with_history.invoke({
            "input": request.query
        }, config={"configurable": {"session_id": "test_session"}})
        
        return QueryResponse(
            response=result.get("output", "No response generated"),
            user_id="test@example.com",
            schema="test_schema", 
            success=True,
            session_id="test_session",
            metadata={"test_mode": True}
        )
        
    except Exception as e:
        logger.error(f"Error in test query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session_with_schema)
):
    """Process natural language query using the new three-agent pipeline architecture."""
    try:
        # Ensure user schema exists
        ensure_user_schema(current_user.email)
        
        # Get user session from schema user service
        session = schema_user_service.create_session_from_email(current_user.email, current_user.name)
        
        # Get MCP orchestrator instance
        orchestrator = get_mcp_orchestrator(static_dir="static/charts")
        
        # Generate session ID for this query
        session_id = f"{current_user.email}_{session.email}"
        
        # Process query through MCP orchestrator
        result = await orchestrator.process_query(
            query=request.query,
            user_email=current_user.email,
            session_id=session_id
        )
        
        # Extract chart files from MCP result
        chart_files = result.get("chart_files", [])
        chart_file = chart_files[0] if chart_files else None
        
        return QueryResponse(
            response=result.get("response", "No response generated"),
            user_id=current_user.email,
            schema=session.schema_name,
            success=True,  # MCP orchestrator handles errors internally
            error=result.get("metadata", {}).get("error"),
            chart_file=chart_file,
            chart_type="plotly" if chart_file else None,
            session_id=session_id,
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing query for user {current_user.email}: {str(e)}")
        return QueryResponse(
            response=f"I apologize, but I encountered an error while processing your query: {str(e)}",
            user_id=current_user.email,
            schema="unknown",
            success=False,
            error=str(e),
            session_id=request.session_id or "unknown"
        )

@app.post("/query-no-auth", response_model=QueryResponse)
async def query_database_no_auth(request: QueryRequest):
    """Temporary endpoint without authentication for testing - uses MCP orchestrator."""
    try:
        # Use anonymous user for testing
        anonymous_email = "anonymous@example.com"
        
        # Ensure anonymous schema exists
        ensure_user_schema(anonymous_email)
        
        # Use direct SQL agent for query processing
        try:
            # Create database URI for portfoliosql
            from settings import get_portfoliosql_connection
            engine = get_portfoliosql_connection()
            db_uri = str(engine.url)
            
            # Create SQL agent with comprehensive discovery for testing
            agent_with_history = create_multitenant_sql_agent(db_uri, schema_name="anonymous_schema")
            
            # Execute query
            result = agent_with_history.invoke({
                "input": request.query
            }, config={"configurable": {"session_id": "anonymous_session"}})
            
            return QueryResponse(
                response=result.get("output", "No response generated"),
                user_id=anonymous_email,
                schema="anonymous_schema", 
                success=True,
                session_id="anonymous_session"
            )
            
        except Exception as agent_error:
            logger.error(f"SQL agent error: {str(agent_error)}")
            return QueryResponse(
                response=f"I apologize, but I encountered an error while processing your query: {str(agent_error)}",
                user_id=anonymous_email,
                schema="anonymous_schema",
                success=False,
                error=str(agent_error),
                session_id="anonymous_session"
            )
        
    except Exception as e:
        logger.error(f"Error in no-auth query: {str(e)}")
        return QueryResponse(
            response=f"I apologize, but I encountered an error while processing your query: {str(e)}",
            user_id="anonymous@example.com",
            schema="anonymous_schema",
            success=False,
            error=str(e),
            session_id="anonymous_session"
        )


@app.post("/upload-files")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session_with_schema)
):
    """Upload and process Excel/CSV files for authenticated user using schema-per-tenant architecture."""
    try:
        # Ensure user schema exists
        ensure_user_schema(current_user.email)
        
        # Get user session from schema user service
        session = schema_user_service.create_session_from_email(current_user.email, current_user.name)
        
        # Use portfoliosql database with user's schema
        schema_name = f"user_{current_user.email.replace('@', '_').replace('.', '_')}"
        
        # Save uploaded files temporarily
        temp_files = []
        try:
            for file in files:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
                content = await file.read()
                temp_file.write(content)
                temp_file.close()
                temp_files.append(temp_file.name)

            # Create Celery task for file processing
            task_id = create_file_processing_task(temp_files, current_user.email)

            return {
                "success": True,
                "message": "Files uploaded successfully and are being processed",
                "task_id": task_id,
                "schema": schema_name,
                "user_email": current_user.email
            }

        except Exception as e:
            # Clean up temp files on error
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            raise e

    except Exception as e:
        logger.error(f"File upload failed for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_api(task_id: str):
    """Get the status of a background task."""
    status = get_task_status(task_id)
    if not status or status.get("status") == "error":
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@app.post("/upload-files-sync", response_model=UploadResponse, deprecated=True)
async def upload_files_sync(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None)
):
    """Upload Excel/CSV files synchronously (deprecated - use /upload-files instead)."""
    try:
        # Get or create user session
        session = get_user_session(user_id)
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Save uploaded files temporarily
        temp_files = []
        try:
            for file in files:
                # Validate file type
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in uploader.supported_extensions:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(uploader.supported_extensions)}"
                    )
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file.close()
                    temp_files.append(temp_file.name)
            
            # Upload files with sheet processing
            result = uploader.upload_multiple_files(temp_files, session)
            
            # Add system message about upload
            if result['success']:
                message = f"✅ Uploaded {result['files_processed']} files with {result['sheets_processed']} sheets"
                if result['tables_created']:
                    message += f"\nTables created: {', '.join(result['tables_created'])}"
            else:
                message = f"❌ Upload failed: {result.get('message', 'Unknown error')}"
            
            session.add_message('system', message)
            
            # Invalidate user's SQL agent to pick up new tables
            if session.email in sql_agents:
                del sql_agents[session.email]
            
            return UploadResponse(**result)
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
                    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.get("/user/tables")
async def get_user_tables(current_user: User = Depends(get_current_user)):
    """Get tables for the authenticated user."""
    try:
        # Ensure user schema exists
        ensure_user_schema(current_user.email)
        
        # Get user session from schema user service
        session = schema_user_service.create_session_from_email(current_user.email, current_user.name)
        
        # Get table list from schema
        tables = session.list_tables()
        schema_name = f"user_{current_user.email.replace('@', '_').replace('.', '_')}"
        
        return {
            "success": True,
            "user_email": current_user.email,
            "database": f"portfoliosql (schema: {schema_name})",
            "tables": tables,
            "table_count": len(tables)
        }
        
    except Exception as e:
        logger.error(f"Failed to get tables for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


# Legacy endpoint removed - using schema-per-tenant only


@app.get("/user/{user_id}/history")
async def get_user_history(user_id: str):
    """Get conversation history for a user."""
    try:
        # Use the session history to get actual chat messages
        if user_id in session_histories:
            history = session_histories[user_id]
            messages = []
            for message in history.messages:
                messages.append({
                    "type": message.type,
                    "content": message.content,
                    "timestamp": getattr(message, 'timestamp', None)
                })
            return {
                "user_id": user_id,
                "message_count": len(messages),
                "messages": messages
            }
        else:
            return {
                "user_id": user_id,
                "message_count": 0,
                "messages": []
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user history: {str(e)}")


@app.delete("/user/{user_id}/history")
async def clear_user_history(user_id: str):
    """Clear conversation history for a user."""
    try:
        cleared = clear_session_history(user_id)
        return {
            "user_id": user_id,
            "cleared": cleared,
            "message": "Chat history cleared successfully" if cleared else "No chat history found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear user history: {str(e)}")


@app.get("/admin/sessions")
async def get_all_sessions():
    """Get statistics about active SQL agents (admin endpoint)."""
    try:
        return {
            "active_sql_agents": len(sql_agents),
            "agent_users": list(sql_agents.keys()),
            "architecture": "schema-per-tenant"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")


@app.get("/admin/databases")
async def get_user_databases():
    """Get database info for schema-per-tenant architecture (admin endpoint)."""
    try:
        from settings import get_portfoliosql_connection
        engine = get_portfoliosql_connection()
        return {
            "database": "portfoliosql",
            "architecture": "schema-per-tenant",
            "active_schemas": len(sql_agents),
            "database_url": str(engine.url).replace(engine.url.password, "***")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")


@app.delete("/admin/session/{user_id}")
async def delete_user_session(user_id: str):
    """Delete a user SQL agent (admin endpoint)."""
    try:
        if user_id not in sql_agents:
            raise HTTPException(status_code=404, detail="SQL agent not found")
        
        # Remove SQL agent
        if user_id in sql_agents:
            del sql_agents[user_id]
        
        return {"message": f"SQL agent for {user_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


# Enhanced agent management and database discovery endpoints
@app.get("/discovery/databases")
async def get_database_discovery(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive database discovery information for the current user."""
    try:
        # Get user-specific database info
        db_info = discovery_service.get_user_specific_database_info(current_user.email)
        
        return {
            "success": True,
            "user_email": current_user.email,
            "database_info": db_info,
            "discovery_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Database discovery failed for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Database discovery failed: {str(e)}")

@app.get("/discovery/summary")
async def get_discovery_summary(
    current_user: User = Depends(get_current_user)
):
    """Get a summary of the user's database discovery and orchestrator status."""
    try:
        # Get MCP orchestrator status
        orchestrator = get_mcp_orchestrator(static_dir="static/charts")
        orchestrator_health = await orchestrator.get_health_status()
        orchestrator_stats = orchestrator.get_stats()
        
        # Get basic database discovery info
        try:
            available_databases = discovery_service.list_available_databases()
            db_count = len(available_databases)
        except Exception:
            available_databases = []
            db_count = 0
        
        return {
            "success": True,
            "user_email": current_user.email,
            "orchestrator_status": orchestrator_health.get('orchestrator', 'unknown'),
            "agent_pipeline_status": orchestrator_stats.get('agents_status', {}),
            "execution_stats": orchestrator_stats.get('execution_stats', {}),
            "available_databases": db_count,
            "database_names": available_databases,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Discovery summary failed for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery summary failed: {str(e)}")

@app.post("/agent/refresh")
async def refresh_user_agent(
    current_user: User = Depends(get_current_user)
):
    """Refresh orchestrator agents and database discovery (agents are created fresh on each request)."""
    try:
        # Get fresh MCP orchestrator status and health
        orchestrator = get_mcp_orchestrator(static_dir="static/charts")
        orchestrator_health = await orchestrator.get_health_status()
        orchestrator_stats = orchestrator.get_stats()
        
        # Refresh MCP connections
        refresh_result = await orchestrator.refresh_connections()
        
        # Get updated database discovery
        try:
            available_databases = discovery_service.list_available_databases()
            db_count = len(available_databases)
        except Exception:
            available_databases = []
            db_count = 0
        
        return {
            "success": True,
            "message": "Orchestrator and database discovery refreshed successfully",
            "user_email": current_user.email,
            "orchestrator_status": orchestrator_health.get('orchestrator', 'unknown'),
            "agent_pipeline_status": orchestrator_stats.get('agents_status', {}),
            "available_databases": db_count,
            "database_names": available_databases,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent refresh failed for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent refresh failed: {str(e)}")

@app.get("/agent/contexts")
async def get_available_contexts(
    current_user: User = Depends(get_current_user)
):
    """Get all available database/schema contexts for the user."""
    try:
        # Get database discovery info directly
        try:
            available_databases = discovery_service.list_available_databases()
            db_contexts = []
            
            for db_name in available_databases:
                try:
                    schemas = discovery_service.get_database_schemas(db_name)
                    for schema in schemas:
                        db_contexts.append({
                            'database': db_name,
                            'schema': schema,
                            'context_id': f"{db_name}.{schema}"
                        })
                except Exception as e:
                    logger.warning(f"Failed to get schemas for {db_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Database discovery failed: {e}")
            db_contexts = []
        
        return {
            "success": True,
            "user_email": current_user.email,
            "available_contexts": db_contexts,
            "total_contexts": len(db_contexts),
            "available_databases": len(available_databases) if 'available_databases' in locals() else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Context listing failed for {current_user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Context listing failed: {str(e)}")

@app.get("/admin/discovery/all")
async def get_comprehensive_discovery():
    """Admin endpoint to get comprehensive database discovery across all databases."""
    try:
        discovery_info = discovery_service.get_comprehensive_database_info(include_columns=True)
        connectivity_test = discovery_service.test_database_connectivity()
        
        return {
            "success": True,
            "discovery_info": discovery_info,
            "connectivity_test": connectivity_test,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Comprehensive discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive discovery failed: {str(e)}")


# Evaluation and testing helpers
def create_sample_evaluation_questions():
    """
    Returns sample questions for evaluating the SQL agent.
    These can be used for testing and evaluation purposes.
    """
    return [
        "How many tables do I have?",
        "What data did I upload?",
        "Show me the structure of my tables",
        "List the first 5 rows from my data",
        "What columns are available in my tables?",
        "Show me a summary of my uploaded data",
        "What types of data do I have?",
        "Show me sample records from each table"
    ]

@app.get("/admin/evaluate")
async def evaluate_agent_capability():
    """
    Admin endpoint to evaluate agent with sample questions.
    Returns results for each test question.
    """
    try:
        evaluation_results = []
        sample_questions = create_sample_evaluation_questions()
        
        # Create a test session for evaluation
        test_session_id = f"eval_session_{uuid.uuid4().hex[:8]}"
        
        # Use the first available agent or create a new one
        if sql_agents:
            agent_key = list(sql_agents.keys())[0]
            agent_with_history = sql_agents[agent_key]
        else:
            # Create a default agent for evaluation using portfoliosql
            from settings import get_portfoliosql_connection
            engine = get_portfoliosql_connection()
            db_uri = str(engine.url)
            agent_with_history = create_multitenant_sql_agent(db_uri, schema_name="eval_schema")
        
        for i, question in enumerate(sample_questions):
            try:
                result = agent_with_history.invoke(
                    {"input": question},
                    config={"configurable": {"session_id": test_session_id}}
                )
                
                evaluation_results.append({
                    "question_id": i + 1,
                    "question": question,
                    "success": True,
                    "response": result["output"],
                    "has_intermediate_steps": bool(result.get("intermediate_steps")),
                    "step_count": len(result.get("intermediate_steps", []))
                })
            except Exception as e:
                evaluation_results.append({
                    "question_id": i + 1,
                    "question": question,
                    "success": False,
                    "error": str(e),
                    "response": None
                })
        
        # Clear the test session
        clear_session_history(test_session_id)
        
        success_count = sum(1 for result in evaluation_results if result["success"])
        return {
            "total_questions": len(sample_questions),
            "successful_answers": success_count,
            "success_rate": success_count / len(sample_questions),
            "evaluation_session": test_session_id,
            "results": evaluation_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# Schema information endpoint
@app.get("/user/schema-info")
async def get_user_schema_info_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Get schema information for the current user."""
    try:
        schema_info = get_user_schema_info(current_user.email)
        return {
            **schema_info,
            "architecture": "schema-per-tenant"
        }
    except Exception as e:
        logger.error(f"Error getting schema info for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting schema info: {str(e)}")


# Chart serving endpoints
@app.get("/charts/{chart_file}")
async def serve_chart(chart_file: str):
    """
    Serve generated chart HTML files.
    
    Args:
        chart_file: The chart filename (e.g., 'chart_123.html')
        
    Returns:
        HTML content of the chart
    """
    try:
        # Ensure chart_file is safe (no path traversal)
        if ".." in chart_file or "/" in chart_file or "\\" in chart_file:
            raise HTTPException(status_code=400, detail="Invalid chart file name")
            
        # Ensure it's an HTML file
        if not chart_file.endswith('.html'):
            raise HTTPException(status_code=400, detail="Invalid file type")
            
        # Construct full path
        charts_dir = "static/charts"
        chart_path = os.path.join(charts_dir, chart_file)
        
        # Check if file exists
        if not os.path.exists(chart_path):
            raise HTTPException(status_code=404, detail="Chart not found")
            
        # Return HTML response
        with open(chart_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving chart {chart_file}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving chart")


@app.get("/charts/{chart_file}/embed")
async def serve_chart_embed(chart_file: str):
    """
    Serve chart as embeddable iframe content.
    
    Args:
        chart_file: The chart filename
        
    Returns:
        Minimal HTML for embedding
    """
    try:
        # Same validation as serve_chart
        if ".." in chart_file or "/" in chart_file or "\\" in chart_file:
            raise HTTPException(status_code=400, detail="Invalid chart file name")
            
        if not chart_file.endswith('.html'):
            raise HTTPException(status_code=400, detail="Invalid file type")
            
        charts_dir = "static/charts"
        chart_path = os.path.join(charts_dir, chart_file)
        
        if not os.path.exists(chart_path):
            raise HTTPException(status_code=404, detail="Chart not found")
            
        # Return as FileResponse with iframe-friendly headers
        return FileResponse(
            path=chart_path,
            media_type="text/html",
            headers={
                "X-Frame-Options": "SAMEORIGIN",
                "Content-Security-Policy": "frame-ancestors 'self' localhost:*",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving chart embed {chart_file}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving chart")


# All routes are now handled by the three-agent orchestrator pipeline above

include_auth_routes(app)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Multi-Tenant SQL Agent API Server...")
    print("👥 Multi-tenant mode enabled")
    print("📊 LangSmith tracing enabled")
    print(f"🌐 Frontend will be available at: {settings.frontend_base_url}")
    print(f"🔗 API documentation: {settings.api_docs_url}")
    print(f"🔗 API endpoint: {settings.api_base_url}")
    
    uvicorn.run(
        "multitenant_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
