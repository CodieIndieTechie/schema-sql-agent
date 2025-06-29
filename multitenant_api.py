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
from typing import List, Optional, Any, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from schema_user_service import schema_user_service
from auth_service import get_current_user, User
from schema_dependencies import (
    get_db_session_with_schema, get_user_schema_info, ensure_user_schema
)
from auth_endpoints import include_auth_routes
from multi_sheet_uploader import MultiSheetExcelUploader
from celery_tasks import create_file_processing_task, get_task_status

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
    allow_origins=settings.cors_origins,
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

# Store SQL agents per user
sql_agents = {}

# Function to invalidate a user's SQL agent
def invalidate_user_agent(user_id: str):
    """Invalidate a user's SQL agent so it will be recreated with new tables."""
    if user_id in sql_agents:
        del sql_agents[user_id]
        print(f"✅ Invalidated SQL agent for user: {user_id}")

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
        # Create database connection with schema-specific search path
        db = SQLDatabase.from_uri(database_uri)
        
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
        
        # System prompt for schema-per-tenant architecture
        system_prompt = f"""You are a helpful SQL expert assistant with access to a PostgreSQL database.

You are working with the user's personal schema{f' ({schema_name})' if schema_name else ''} which contains their uploaded data files and tables.

**IMPORTANT - Query Guidelines:**
1. Be efficient: Use the minimum number of tool calls needed to answer the question
2. First check available tables with sql_db_list_tables if needed
3. Then query the data with sql_db_query, limiting results to 5 rows unless specified
4. Provide your final answer immediately after getting the query results
5. Don't repeatedly query the same information
6. If you get an error, try a simpler approach instead of complex workarounds

**Response Format:**
- Execute necessary tools to get the data
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
            max_iterations=15,  # Increased from 10 to 15
            max_execution_time=60,  # 60 second timeout
            early_stopping_method="generate",  # Changed from "force" to "generate"
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
    """Health check endpoint."""
    try:
        # Check portfoliosql database connection
        from settings import get_portfoliosql_connection
        engine = get_portfoliosql_connection()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "multi-tenant-sql-agent",
            "architecture": "schema-per-tenant",
            "database": "portfoliosql",
            "active_sql_agents": len(sql_agents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Legacy session endpoints removed - using schema-per-tenant architecture


@app.post("/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db_session = Depends(get_db_session_with_schema)
):
    """Process natural language query for authenticated user using schema-per-tenant architecture."""
    try:
        # Ensure user schema exists
        ensure_user_schema(current_user.email)
        
        # Get user session from schema user service
        session = schema_user_service.create_session_from_email(current_user.email, current_user.name)
        
        # Get or create SQL agent for this user's schema in portfoliosql
        # Use the same schema name logic as SchemaUserSession
        from schema_migration import email_to_schema_name
        schema_name = email_to_schema_name(current_user.email)
        
        if current_user.email not in sql_agents:
            # Create agent with schema-specific database connection using SchemaUserSession's db_uri
            db_uri = session.db_uri
            sql_agents[current_user.email] = create_multitenant_sql_agent(db_uri, schema_name=schema_name)
        
        agent_with_history = sql_agents[current_user.email]
        
        # Process the query with LangChain's built-in chat history
        result = agent_with_history.invoke(
            {"input": request.query},
            config={"configurable": {"session_id": current_user.email}}
        )
        
        return QueryResponse(
            success=True,
            user_id=current_user.email,
            schema=schema_name,
            response=result["output"],
            error=None
        )
        
    except Exception as e:
        logger.error(f"Query processing failed for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


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
            if session.user_id in sql_agents:
                del sql_agents[session.user_id]
            
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
