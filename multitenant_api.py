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

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header, BackgroundTasks
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
from user_service import main_user_service, get_or_create_session_from_user, UserSession
from auth_service import get_current_user, User
from auth_endpoints import include_auth_routes
from multi_sheet_uploader import MultiSheetExcelUploader
from venv_async_processor import VenvAsyncProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class UserSessionResponse(BaseModel):
    user_id: str
    database_name: str
    created_at: str
    message_count: int
    table_count: int


class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    user_id: str
    database_name: str
    success: bool
    error: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
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
    database_name: str
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
    
    # Start the async worker
    try:
        from venv_async_processor import processor
        processor.start_worker()
        logger.info("✅ Async worker started successfully")
        print("🔄 Async file processor worker started")
    except Exception as e:
        logger.error(f"❌ Failed to start async worker: {e}")
        print(f"⚠️ Warning: Async worker failed to start: {e}")

# Global services
from user_service import main_user_service
from multi_sheet_uploader import MultiSheetExcelUploader

user_service = main_user_service
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

def get_user_session(user_id: str = None) -> UserSession:
    """Get or create user session."""
    if user_id:
        session = user_service.get_user_session(user_id)
        if session:
            return session
    
    # Create new session
    return user_service.create_user_session()


def get_sql_agent(user_session: UserSession):
    """Get or create SQL agent for user."""
    user_id = user_session.user_id
    
    if user_id not in sql_agents:
        try:
            agent_executor = create_multitenant_sql_agent(user_session.database_name)
            sql_agents[user_id] = agent_executor
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create SQL agent: {str(e)}")
    
    return sql_agents[user_id]


# SQL Agent creation function
def create_multitenant_sql_agent(database_name: str) -> AgentExecutor:
    """Create a SQL agent with dual database access (user + portfolio)."""
    try:
        # Create database connection for the specific user database
        user_database_uri = f"postgresql://{settings.encoded_db_user}:{settings.encoded_db_password}@{settings.db_host}:{settings.db_port}/{database_name}"
        user_db = SQLDatabase.from_uri(user_database_uri)
        
        # Create database connection for the portfolio database
        portfolio_database_uri = f"postgresql://{settings.encoded_db_user}:{settings.encoded_db_password}@{settings.db_host}:{settings.db_port}/portfoliosql"
        portfolio_db = SQLDatabase.from_uri(portfolio_database_uri)
        
        # Initialize OpenAI LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Create tools for both databases
        from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
        
        # User database tools (for uploaded data)
        user_toolkit = SQLDatabaseToolkit(db=user_db, llm=llm)
        user_tools = user_toolkit.get_tools()
        
        # Portfolio database tools (for shared financial data)
        portfolio_toolkit = SQLDatabaseToolkit(db=portfolio_db, llm=llm)
        portfolio_tools = portfolio_toolkit.get_tools()
        
        # Rename tools to distinguish between databases
        for tool in user_tools:
            tool.name = f"user_db_{tool.name}"
            tool.description = f"For personal uploaded data: {tool.description}"
            
        for tool in portfolio_tools:
            tool.name = f"portfolio_db_{tool.name}"
            tool.description = f"For portfolio/financial data (stocks, bonds, mutual_funds, etc.): {tool.description}"
        
        # Combine all tools
        all_tools = user_tools + portfolio_tools
        
        # Enhanced system prompt for dual database routing with modern structure
        system_prompt = """You are a helpful SQL expert assistant with access to two databases:

1. **Personal Database** (user_db_*): Contains the user's uploaded data files
2. **Portfolio Database** (portfolio_db_*): Contains shared financial data (stocks, bonds, mutual funds, ETFs, real estate, portfolio analysis)

**Database Selection Rules:**
- For questions about FINANCIAL/INVESTMENT data (stocks, bonds, mutual funds, ETFs, real estate, portfolio analysis): Use portfolio_db_* tools
- For questions about UPLOADED USER DATA (Excel/CSV files they uploaded): Use user_db_* tools
- When in doubt, start with portfolio_db_* for financial terms, user_db_* for personal data

**Query Guidelines:**
1. Always identify which database to query based on the question context
2. Use appropriate database tools (user_db_* or portfolio_db_*)
3. Execute the tools and provide the actual results
4. If data isn't found in one database, try the other if it makes sense
5. Always mention which database you're querying for transparency
6. Unless the user specifies a specific number of examples, always limit your query to at most 5 results
7. You can order the results by a relevant column to return the most interesting examples

Examples:
- "List mutual funds" → Use portfolio_db_list_tables and portfolio_db_query_sql to get actual results
- "Show my uploaded sales data" → Use user_db_list_tables and user_db_query_sql to get actual results
- "What tables do I have?" → Use user_db_list_tables to show actual table names

Remember: Always execute the tools to get real data, don't just show function calls. Only use the given tools and only use information returned by the tools to construct your final answer."""
        
        # Create modern prompt structure with chat history support
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create modern tool-calling agent
        agent = create_tool_calling_agent(llm, all_tools, prompt)
        
        # Create agent executor with enhanced capabilities
        agent_executor = AgentExecutor(
            agent=agent,
            tools=all_tools,
            verbose=False,  # Set to True for debugging
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="force",
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
        # Check user service
        stats = user_service.get_session_stats()
        
        return {
            "status": "healthy",
            "service": "multi-tenant-sql-agent",
            "active_sessions": stats["active_sessions"],
            "user_databases": len(user_service.list_user_databases())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/session/new", response_model=UserSessionResponse)
async def create_new_session():
    """Create a new user session with dedicated database."""
    try:
        session = user_service.create_user_session()
        
        return UserSessionResponse(
            user_id=session.user_id,
            database_name=session.database_name,
            created_at=session.created_at.isoformat(),
            message_count=len(session.message_history),
            table_count=len(session.uploaded_tables)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/session/{user_id}", response_model=UserSessionResponse)
async def get_session_info(user_id: str):
    """Get information about a user session."""
    session = user_service.get_user_session(user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return UserSessionResponse(
        user_id=session.user_id,
        database_name=session.database_name,
        created_at=session.created_at.isoformat(),
        message_count=len(session.message_history),
        table_count=len(session.uploaded_tables)
    )


@app.post("/query")
async def query_database(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Process natural language query for authenticated user."""
    try:
        # Get user session from authenticated user
        session = get_or_create_session_from_user(current_user)
        
        # Get or create SQL agent for this user's database
        if current_user.email not in sql_agents:
            sql_agents[current_user.email] = create_multitenant_sql_agent(current_user.database_name)
        
        agent_with_history = sql_agents[current_user.email]
        
        # Process the query with session history
        result = agent_with_history.invoke(
            {"input": request.query},
            config={"configurable": {"session_id": current_user.email}}
        )
        
        return {
            "success": True,
            "user_email": current_user.email,
            "database": current_user.database_name,
            "query": request.query,
            "response": result["output"],
            "intermediate_steps": result.get("intermediate_steps", []) if settings.debug else None
        }
        
    except Exception as e:
        logger.error(f"Query processing failed for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/upload-files")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload and process Excel/CSV files for authenticated user."""
    try:
        # Get or create user session from authenticated user
        session = get_or_create_session_from_user(current_user)
        
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

            # Create async processing task with email and database name
            task_id = VenvAsyncProcessor().create_task(temp_files, current_user.email, current_user.database_name)

            return {
                "success": True,
                "message": f"Files uploaded successfully. Processing {len(files)} files in background.",
                "task_id": task_id,
                "files_count": len(files),
                "user_email": current_user.email,
                "database": current_user.database_name
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
    status = VenvAsyncProcessor().get_task_status(task_id)
    if not status or status.get("state") == "NOT_FOUND":
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
        # Get user session
        session = get_or_create_session_from_user(current_user)
        
        # Get table list from database
        tables = session.list_tables()
        
        return {
            "success": True,
            "user_email": current_user.email,
            "database": current_user.database_name,
            "tables": tables,
            "table_count": len(tables)
        }
        
    except Exception as e:
        logger.error(f"Failed to get tables for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


@app.get("/user/{user_id}/databases")
async def get_user_databases(user_id: str):
    """Get list of databases available to a user."""
    session = user_service.get_user_session(user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    try:
        # Check if portfoliosql database exists
        portfolio_available = False
        try:
            from settings import get_database_connection
            portfolio_engine = get_database_connection("portfoliosql")
            with portfolio_engine.connect() as conn:
                conn.execute("SELECT 1")
            portfolio_available = True
        except Exception:
            portfolio_available = False
        
        # Check if user database exists
        user_db_available = False
        try:
            user_engine = get_database_connection(session.database_name)
            with user_engine.connect() as conn:
                conn.execute("SELECT 1")
            user_db_available = True
        except Exception:
            user_db_available = False
        
        databases = []
        
        if portfolio_available:
            databases.append({
                "name": "portfoliosql",
                "type": "shared",
                "description": "Shared portfolio and financial data",
                "available": True
            })
        
        if user_db_available:
            databases.append({
                "name": session.database_name,
                "type": "personal",
                "description": "Personal database for uploaded Excel/CSV files",
                "available": True
            })
        
        return {
            "user_id": user_id,
            "databases": databases,
            "total_count": len(databases)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check databases: {str(e)}")


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
    """Get statistics about all active sessions (admin endpoint)."""
    try:
        stats = user_service.get_session_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")


@app.get("/admin/databases")
async def get_user_databases():
    """Get list of all user databases (admin endpoint)."""
    try:
        databases = user_service.list_user_databases()
        return {"user_databases": databases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")


@app.delete("/admin/session/{user_id}")
async def delete_user_session(user_id: str):
    """Delete a user session (admin endpoint)."""
    try:
        session = user_service.get_user_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Remove from active sessions
        user_service.cleanup_session(user_id)
        
        # Remove SQL agent
        if user_id in sql_agents:
            del sql_agents[user_id]
        
        return {"message": f"Session {user_id} deleted successfully"}
        
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
        "What financial data is available in the portfolio database?",
        "List all mutual funds with their performance metrics",
        "Show me the top 5 performing stocks",
        "What data did I upload recently?",
        "Compare bond performance vs stock performance",
        "What are the different asset classes available?",
        "Show my portfolio allocation by asset type"
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
            # Create a default agent for evaluation
            agent_with_history = create_multitenant_sql_agent("default_eval_db")
        
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
