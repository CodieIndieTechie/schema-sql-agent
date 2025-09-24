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
from typing import List, Optional, Any, Union, Dict
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
from session_api import router as session_router
from session_manager import session_manager

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
    session_id: Optional[str] = None


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
        # Use mutual_fund database which contains the NAV data
        mutual_fund_db_uri = settings.get_database_uri("mutual_fund")
        db = SQLDatabase.from_uri(mutual_fund_db_uri)
        
        # Initialize OpenAI LLM with consistent settings to reduce hallucination
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,  # Use 0.0 for deterministic SQL generation
            openai_api_key=settings.openai_api_key,
            max_tokens=settings.openai_max_tokens
        )
        
        # Create SQL toolkit for the user's schema
        from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
        
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()
        
        # System prompt for mutual fund database access
        system_prompt = """You are a helpful SQL expert assistant with access to the mutual_fund PostgreSQL database.

**CRITICAL INSTRUCTION: For ALL performance queries (1-year returns, 3-year returns, etc.), ALWAYS use the FUND_RANKINGS table with columns like point_to_point_return_1y, annualized_return_3y, etc. DO NOT use historical_returns table for performance queries.**

You have access to a comprehensive mutual fund database containing 6,352,051+ records across 8 interconnected tables for 1,487 AMFI registered mutual fund schemes:

**Core Tables & Relationships:**
```
schemes (1:1) → fund_rankings
schemes (1:1) → historical_returns  
schemes (1:M) → bse_details
schemes (1:M) → historical_nav
schemes (1:M) → historical_risk
schemes (1:M) → current_holdings
```

**1. SCHEMES Table (1,487 records)**
Core mutual fund information:
- `id` (TEXT PK): Unique scheme identifier from MF APIs Club
- `scheme_code` (TEXT): AMFI scheme code
- `scheme_name` (TEXT): Full scheme name
- `amfi_broad` (TEXT): Broad category (Equity, Debt, Hybrid, Other, Solution Oriented)
- `amfi_sub` (TEXT): Sub-category (Large Cap Fund, Liquid Fund, etc.)
- `aum_in_lakhs` (DECIMAL): Assets Under Management in lakhs
- `current_nav` (DECIMAL): Latest Net Asset Value
- `risk_level` (INTEGER): Risk rating 1-5 (1=lowest, 5=highest)
- `amc_code` (TEXT): Asset Management Company code
- `sip_allowed` (BOOLEAN): SIP investment allowed
- `purchase_allowed` (BOOLEAN): Lump sum purchase allowed

**2. HISTORICAL_RETURNS Table (1,487 records)**
Latest performance metrics across all time periods:
- `scheme_id` (TEXT FK): References schemes.id
- `return_1d`, `return_1w`, `return_1m`, `return_3m`, `return_6m`, `return_1y`, `return_3y`, `return_5y`, `return_7y`, `return_10y` (DECIMAL): Return percentages
- `annualized_1y`, `annualized_3y`, `annualized_5y`, `annualized_7y`, `annualized_10y` (DECIMAL): Annualized returns
- `rolling_return_1y`, `rolling_return_3y`, `rolling_return_5y` (DECIMAL): Rolling returns
- `latest_nav_value` (DECIMAL): Most recent NAV

**3. FUND_RANKINGS Table (1,484 records)**
Sophisticated three-pillar ranking system:
- `scheme_id` (TEXT FK): References schemes.id
- `overall_rank` (INTEGER): Overall fund ranking (1 = best)
- `composite_score` (DECIMAL): Combined score across all pillars
- `pillar_1_score` (DECIMAL): Performance score (45% weight)
- `pillar_2_score` (DECIMAL): Risk Management score (35% weight) 
- `pillar_3_score` (DECIMAL): Cost Efficiency score (20% weight)
- Performance metrics: `point_to_point_return_1y`, `annualized_return_3y`, `annualized_return_5y`, `avg_3y_rolling_return`, `avg_5y_rolling_return`
- Risk metrics: `annualized_volatility_3y`, `annualized_volatility_5y`, `maximum_drawdown_5y`, `sharpe_ratio_3y`, `sortino_ratio_3y`
- Advanced: `jensen_alpha_3y`, `beta_3y`, `down_capture_ratio_3y`, `up_capture_ratio_3y`, `var_95_1y`
- `aum_cr` (DECIMAL): AUM in crores

**4. BSE_DETAILS Table (1,487 records)**
BSE trading information:
- `id` (SERIAL PK): Auto-increment primary key
- `scheme_id` (TEXT FK): References schemes.id
- `bse_code` (TEXT): BSE trading code
- `sip_flag`, `stp_flag`, `swp_flag`, `switch_flag` (BOOLEAN): Transaction capabilities
- `lock_in_flag` (BOOLEAN): Lock-in period applicable
- `lock_in_period_months` (INTEGER): Lock-in duration
- `exit_load_flag` (BOOLEAN): Exit load applicable
- `exit_load_message` (TEXT): Exit load conditions

**5. CURRENT_HOLDINGS Table (51,950 records)**
Comprehensive portfolio compositions:
- `scheme_id` (TEXT FK): References schemes.id
- `company_name` (TEXT): Holding company name
- `percentage_holding` (DECIMAL): Percentage allocation
- `market_value` (DECIMAL): Market value of holding
- `sector` (TEXT): Sector classification
- `investment_type` (TEXT): Type of investment

**6. HISTORICAL_NAV Table (3,147,643 records)**
Complete historical NAV data (April 1, 2006 to September 10, 2025):
- `id` (SERIAL PK): Auto-increment primary key
- `scheme_id` (TEXT FK): References schemes.id
- `scheme_code` (TEXT): AMFI scheme code
- `nav_date` (DATE): Date of NAV record
- `nav_value` (DECIMAL): Net Asset Value on the date
- Indexes: Optimized for date-range queries and scheme lookups

**7. HISTORICAL_RISK Table (1,308 records)**
Enhanced risk metrics and volatility analysis:
- `id` (SERIAL PK): Auto-increment primary key
- `scheme_id` (TEXT FK): References schemes.id
- `calculation_date` (DATE): Date of risk calculation
- `lookback_period_days` (INTEGER): Days used for calculation (252, 504, 756, 1260)
- `lookback_period_years` (DECIMAL): Lookback period in years
- `data_points` (INTEGER): Actual data points used
- `annualized_volatility` (DECIMAL): Annualized volatility
- `avg_daily_return` (DECIMAL): Average daily return
- `maximum_drawdown` (DECIMAL): Maximum drawdown (negative percentage)
- `var_95_1day` (DECIMAL): 1-day 95% Value at Risk
- `sharpe_ratio` (DECIMAL): Sharpe Ratio (6% risk-free rate)
- `sortino_ratio` (DECIMAL): Sortino Ratio
- `skewness` (DECIMAL): Return distribution skewness
- `kurtosis` (DECIMAL): Return distribution kurtosis
- `beta` (DECIMAL): Category Beta vs peer group
- `alpha` (DECIMAL): Category Alpha vs peer group
- `information_ratio` (DECIMAL): Information Ratio vs peers
- `benchmark_category` (VARCHAR): Category benchmark used
- `index_beta` (DECIMAL): Index Beta vs appropriate index
- `index_alpha` (DECIMAL): Index Alpha vs appropriate index
- `index_benchmark` (VARCHAR): Index fund proxy used
- Enhanced: `up_capture_ratio_3y`, `down_capture_ratio_3y`, `volatility_3y`

**8. BSE_DETAILS Table (1,487 records)**
Trading and transaction information:
- `scheme_id` (TEXT FK): References schemes.id
- `bse_code` (TEXT): BSE trading code
- `minimum_amount` (DECIMAL): Minimum investment amount
- `sip_allowed` (BOOLEAN): SIP investment allowed
- `stp_allowed` (BOOLEAN): STP allowed
- `swp_allowed` (BOOLEAN): SWP allowed
- `switch_allowed` (BOOLEAN): Switch allowed
- `purchase_allowed` (BOOLEAN): Purchase allowed
- `redemption_allowed` (BOOLEAN): Redemption allowed
- `exit_load` (TEXT): Exit load conditions
- `exit_load_days` (INTEGER): Exit load period in days
- `lock_in_period` (INTEGER): Lock-in period
- `dividend_reinvestment` (BOOLEAN): Dividend reinvestment option

**IMPORTANT - AUM Data Formatting:**
- The `aum_in_lakhs` column stores values in Indian Lakhs (1 Lakh = 100,000 rupees)
- When displaying AUM values, ALWAYS multiply by 100,000 to convert from lakhs to rupees
- Example: If aum_in_lakhs = 196049.8, display as ₹19,60,49,80,000
- Use proper Indian number formatting with commas for readability

**IMPORTANT - Enhanced Query Routing Guidelines:**
1. **Risk-Adjusted Returns (PRIORITY #1)**: Use `fund_rankings` table directly - contains ALL risk metrics (sharpe_ratio_3y, sortino_ratio_3y, jensen_alpha_3y, maximum_drawdown_5y, annualized_volatility_3y)
2. **Fund Rankings & Selection**: Use `fund_rankings` for sophisticated fund selection with three-pillar scoring
3. **Performance Analysis**: Use `fund_rankings` for latest comprehensive performance metrics
4. **Fund Information**: Use `schemes` table for basic fund details, categories, AUM, NAV
5. **Risk Analysis**: Use `fund_rankings` for standard risk metrics, `historical_risk` for detailed analysis
6. **Portfolio Analysis**: Use `current_holdings` for sector allocation, top holdings, diversification
7. **Trading Info**: Use `bse_details` for transaction capabilities, exit loads, lock-in periods
8. **Historical NAV**: Use `historical_nav` for NAV trends and time-series analysis

**Enhanced Query Patterns:**
- **Fund Selection**: Use `fund_rankings` for overall_rank, composite_score, pillar scores
- **Performance Analysis**: Use `fund_rankings` directly for comprehensive performance analysis
- **Risk-Adjusted Performance**: Use fund_rankings for sharpe_ratio_3y, maximum_drawdown_5y, volatility metrics
- **International/Global Funds**: For queries about "international", "global", "overseas" funds, use: amfi_sub = 'FoFs Overseas' OR scheme_name ILIKE '%Global%' OR scheme_name ILIKE '%International%' OR scheme_name ILIKE '%Overseas%' OR scheme_name ILIKE '%US%'
- **Portfolio Analysis**: JOIN schemes + current_holdings for sector allocation and diversification
- **Investment Options**: JOIN schemes + bse_details for transaction capabilities
- **Top Funds by Category**: JOIN schemes + fund_rankings filtered by amfi_broad/amfi_sub
- **Complete Fund Profile**: JOIN all tables for comprehensive fund analysis

**Enhanced Filtering & Sorting Best Practices:**
- **Fund Rankings**: Sort by `overall_rank ASC` (1 = best), `composite_score DESC` for top funds
- **Category Filtering**: Use `amfi_broad` (Equity, Debt, Hybrid) and `amfi_sub` for specific types
- **Performance Ranking**: Sort by `point_to_point_return_1y DESC`, `annualized_return_3y DESC`, `annualized_return_5y DESC`
- **Risk-Adjusted Performance**: Sort by `sharpe_ratio_3y DESC`, `sortino_ratio_3y DESC`
- **Risk Management**: Sort by `maximum_drawdown_5y DESC` (less negative = better), `annualized_volatility_3y ASC`
- **Three-Pillar Analysis**: Filter by `pillar_1_score`, `pillar_2_score`, `pillar_3_score` thresholds
- **AUM-based**: Sort by `aum_cr DESC` for largest funds (AUM in crores)
- **Investment Options**: Filter by `sip_allowed = true`, `purchase_allowed = true`
- **Advanced Risk**: Use `down_capture_ratio_3y < 0.9` for downside protection
- **Alpha Generation**: Filter by `jensen_alpha_3y > 0` for manager skill

**Enhanced Query Guidelines:**
1. **Prioritize FUND_RANKINGS**: Use for fund selection, ranking, and risk-adjusted performance analysis
2. **Use HISTORICAL_RETURNS**: For latest comprehensive performance metrics (100% coverage)
3. **Leverage Three-Pillar System**: Consider overall_rank and composite_score for recommendations
4. **International Funds**: For "top international funds" queries, use: SELECT scheme_name, overall_rank, composite_score FROM fund_rankings WHERE amfi_sub = 'FoFs Overseas' OR scheme_name ILIKE '%Global%' OR scheme_name ILIKE '%International%' OR scheme_name ILIKE '%Overseas%' OR scheme_name ILIKE '%US%' ORDER BY overall_rank LIMIT 15
5. **Efficient JOINs**: Always join through schemes.id for referential integrity
6. **Meaningful Limits**: Use LIMIT 10-15 for fund lists, LIMIT 5 for detailed analysis
7. **Handle NULLs**: Gracefully handle NULL values in performance and risk data
8. **Portfolio Analysis**: Use current_holdings for sector allocation and diversification metrics
9. **Risk Analysis**: Use fund_rankings for standard metrics, historical_risk for detailed analysis
10. **Performance Periods**: Use point_to_point_return_1y, annualized_return_3y, annualized_return_5y for standardized comparisons
11. **Data Coverage**: FUND_RANKINGS (99.8%), HISTORICAL_RETURNS (100%), CURRENT_HOLDINGS (comprehensive)

**Response Format:**
- Execute necessary tools to get the data
- Apply AUM conversion (lakhs to rupees) before displaying results
- Format return values as percentages with proper decimal places
- Include overall_rank and composite_score in fund recommendations
- Highlight three-pillar scores (Performance, Risk Management, Cost Efficiency)
- Provide clear, concise answers based on query results
- Stop after providing the answer - don't ask follow-up questions

Remember: Use the sophisticated three-pillar ranking system for fund recommendations. Prioritize FUND_RANKINGS and HISTORICAL_RETURNS for comprehensive analysis. Be direct and efficient with proper table relationships."""
        
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


@app.post("/clear-cache")
async def clear_agent_cache():
    """Clear agent cache to force recreation with updated prompts."""
    try:
        # Clear MCP orchestrator cache
        orchestrator = get_mcp_orchestrator(static_dir="static/charts")
        if hasattr(orchestrator, 'clear_cache'):
            orchestrator.clear_cache()
        
        # Clear any other caches
        logger.info("🗑️  Agent cache cleared - new prompts will be applied")
        
        return {
            "status": "success",
            "message": "Agent cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        return {
            "status": "error", 
            "message": f"Failed to clear cache: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

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
    """Process natural language query with comprehensive memory and session management."""
    try:
        # Ensure user schema exists
        ensure_user_schema(current_user.email)
        
        # Get or create active session for memory persistence
        chat_session = session_manager.get_or_create_active_session(current_user.email)
        
        # Add user message to chat history
        user_message = session_manager.add_message(
            session_id=chat_session.session_id,
            message_type="human",
            content=request.query,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Get conversation context for agent memory
        conversation_summary = session_manager.get_conversation_summary(
            chat_session.session_id, 
            last_n_messages=10
        )
        
        # Get user preferences for personalized responses
        user_preferences = session_manager.get_user_preferences(current_user.email)
        
        # Get user session from schema user service
        session = schema_user_service.create_session_from_email(current_user.email, current_user.name)
        
        # Get A2A service instance
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        # Enhanced query with memory context
        enhanced_query = request.query
        if conversation_summary and conversation_summary != "No previous conversation history.":
            enhanced_query = f"""
Previous conversation context:
{conversation_summary}

User preferences: {user_preferences}

Current query: {request.query}

Please consider the conversation history and user preferences when responding.
"""
        
        # Process query through A2A protocol
        result = await a2a_service.process_query(
            query=enhanced_query,
            user_email=current_user.email,
            session_id=str(chat_session.session_id),
            context={
                'conversation_summary': conversation_summary,
                'user_preferences': user_preferences,
                'session_data': session.to_dict() if hasattr(session, 'to_dict') else {}
            }
        )
        
        # Extract chart files and PDF from A2A result
        chart_files = result.get("chart_files", [])
        chart_file = chart_files[0] if chart_files else None
        pdf_file = result.get("pdf_file")
        
        # Store query results and charts in context
        if chart_files:
            session_manager.set_context(
                chat_session.session_id,
                "chart_context",
                "last_generated_charts",
                chart_files,
                expires_hours=24
            )
        
        # Store successful query pattern for learning
        session_manager.set_context(
            chat_session.session_id,
            "query_context",
            "last_successful_query",
            {
                "query": request.query,
                "response_type": "success",
                "had_charts": bool(chart_files),
                "timestamp": datetime.now().isoformat()
            },
            expires_hours=168  # 1 week
        )
        
        # Add AI response to chat history
        ai_message = session_manager.add_message(
            session_id=chat_session.session_id,
            message_type="ai",
            content=result.get("response", "No response generated"),
            metadata={
                "timestamp": datetime.now().isoformat(),
                "orchestrator_used": True,
                "processing_time": result.get("processing_time")
            },
            chart_files=chart_files,
            query_results=result.get("metadata")
        )
        
        return QueryResponse(
            response=result.get("response", "No response generated"),
            user_id=current_user.email,
            schema=session.schema_name,
            success=True,  # MCP orchestrator handles errors internally
            error=result.get("metadata", {}).get("error"),
            chart_file=chart_file,
            chart_type="plotly" if chart_file else None,
            session_id=str(chat_session.session_id),
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
    """No-auth endpoint with full memory capabilities for testing and development."""
    try:
        # Use anonymous user for testing
        anonymous_email = "anonymous@example.com"
        
        # Try database operations, but continue without them if they fail
        chat_session = None
        conversation_summary = "No previous conversation history."
        user_preferences = {}
        
        try:
            # Ensure anonymous schema exists
            ensure_user_schema(anonymous_email)
            
            # Get or create active session for memory persistence
            chat_session = session_manager.get_or_create_active_session(anonymous_email)
            
            # Add user message to chat history
            user_message = session_manager.add_message(
                session_id=chat_session.session_id,
                message_type="human",
                content=request.query,
                metadata={"timestamp": datetime.now().isoformat(), "no_auth": True}
            )
            
            # Get conversation context for agent memory
            conversation_summary = session_manager.get_conversation_summary(
                chat_session.session_id, 
                last_n_messages=10
            )
            
            # Get user preferences for personalized responses
            user_preferences = session_manager.get_user_preferences(anonymous_email)
            
        except Exception as db_error:
            logger.warning(f"⚠️ Database operations failed, continuing with ReAct reasoning: {db_error}")
            # Create a mock session for ReAct reasoning
            chat_session = type('MockSession', (), {
                'session_id': f"mock_session_{int(datetime.now().timestamp())}"
            })()
        
        # Use Agent Orchestrator for graph-based coordination
        try:
            from services.agent_orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator()
            
            # Enhanced query with memory context
            enhanced_query = request.query
            if conversation_summary and conversation_summary != "No previous conversation history.":
                enhanced_query = f"""
Previous conversation context:
{conversation_summary}

User preferences: {user_preferences}

Current query: {request.query}

Please consider the conversation history and user preferences when responding.
"""
            
            # Execute query with graph-based agent coordination
            result = await orchestrator.process_query(
                query=enhanced_query,
                user_email=anonymous_email,
                session_id=str(chat_session.session_id)
            )
            
            # Extract chart files from result
            chart_files = result.get("chart_files", [])
            chart_file = chart_files[0] if chart_files else None
            
            # Store query results and charts in context
            if chart_files:
                session_manager.set_context(
                    chat_session.session_id,
                    "chart_context",
                    "last_generated_charts",
                    chart_files,
                    expires_hours=24
                )
            
            # Store successful query pattern for learning
            session_manager.set_context(
                chat_session.session_id,
                "query_context",
                "last_successful_query",
                {
                    "query": request.query,
                    "response_type": "success",
                    "had_charts": bool(chart_files),
                    "timestamp": datetime.now().isoformat()
                },
                expires_hours=168  # 1 week
            )
            
            # Add AI response to chat history
            ai_message = session_manager.add_message(
                session_id=chat_session.session_id,
                message_type="ai",
                content=result.get("sql_response", result.get("response", "No response generated")),
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "orchestrator_used": True,
                    "no_auth": True,
                    "processing_time": result.get("processing_time")
                },
                chart_files=chart_files,
                query_results=result.get("metadata")
            )
            
            return QueryResponse(
                response=result.get("sql_response", result.get("response", "No response generated")),
                user_id=anonymous_email,
                schema="anonymous_schema", 
                success=result.get("success", True),
                error=result.get("error"),
                chart_file=result.get("chart_file"),
                chart_type=result.get("chart_type"),
                session_id=str(chat_session.session_id)
            )
            
        except Exception as agent_error:
            logger.error(f"SQL agent error: {str(agent_error)}")
            # Add error message to chat history for context
            session_manager.add_message(
                session_id=chat_session.session_id,
                message_type="ai",
                content=f"I apologize, but I encountered an error while processing your query: {str(agent_error)}",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "error": True,
                    "no_auth": True
                }
            )
            return QueryResponse(
                response=f"I apologize, but I encountered an error while processing your query: {str(agent_error)}",
                user_id=anonymous_email,
                schema="anonymous_schema",
                success=False,
                error=str(agent_error),
                session_id=str(chat_session.session_id)
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


# Include session management routes
app.include_router(session_router)

# A2A Protocol API Endpoints

@app.get("/a2a/health", response_model=dict[str, Any])
async def get_a2a_health():
    """
    Get A2A service health status.
    
    Returns comprehensive health information for the A2A protocol,
    orchestrators, and all registered agents.
    """
    try:
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        health_status = a2a_service.get_service_health()
        return health_status
        
    except Exception as e:
        logger.error(f"A2A health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/a2a/capabilities", response_model=dict[str, Any])
async def get_a2a_capabilities():
    """
    Get A2A service capabilities.
    
    Returns information about supported operations, query types,
    chart types, export formats, and agent capabilities.
    """
    try:
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        capabilities = a2a_service.get_service_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"A2A capabilities check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Capabilities check failed: {str(e)}")


@app.post("/a2a/analyze-query", response_model=dict[str, Any])
async def analyze_query_capabilities(request: QueryRequest):
    """
    Analyze a query to determine required capabilities and estimated processing time.
    
    This endpoint helps users understand what agents will be invoked
    and approximately how long processing will take.
    """
    try:
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        analysis = a2a_service.analyze_query_capabilities(request.query)
        return analysis
        
    except Exception as e:
        logger.error(f"Query analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")


@app.get("/a2a/reports/{user_email}", response_model=List[Dict[str, Any]])
async def list_user_reports(user_email: str, current_user: User = Depends(get_current_user)):
    """
    List available PDF reports for a user.
    
    Returns a list of generated reports with metadata including
    file size, creation date, and report type.
    """
    try:
        # Verify user access (users can only see their own reports)
        if current_user.email != user_email and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        reports = a2a_service.list_available_reports(user_email)
        return reports
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list reports for {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@app.get("/a2a/reports/download/{filename}")
async def download_report(filename: str, current_user: User = Depends(get_current_user)):
    """
    Download a generated PDF report.
    
    Serves PDF reports generated by the A2A system for download.
    Users can only download their own reports unless they are admin.
    """
    try:
        # Validate filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        if not (filename.endswith('.pdf') or filename.endswith('.txt')):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        file_path = a2a_service.get_pdf_file_path(filename)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Determine media type
        media_type = "application/pdf" if filename.endswith('.pdf') else "text/plain"
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download report {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")


@app.post("/a2a/cleanup", response_model=dict[str, Any])
async def cleanup_a2a_sessions(hours: int = 24, current_user: User = Depends(get_current_user)):
    """
    Clean up inactive A2A sessions and old protocol messages.
    
    Admin-only endpoint for system maintenance.
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from services.a2a_service import get_a2a_service
        a2a_service = get_a2a_service()
        
        cleanup_result = a2a_service.cleanup_inactive_sessions(hours)
        return cleanup_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A2A cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# All routes are now handled by the A2A protocol orchestrator pipeline above

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
