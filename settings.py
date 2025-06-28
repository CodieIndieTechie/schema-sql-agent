"""
Secure configuration management using pydantic-settings.
Loads configuration from environment variables with validation and type safety.
"""

import os
from typing import Optional
from urllib.parse import quote_plus
import psycopg2
from sqlalchemy import create_engine
from pydantic import Field, validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # --- Database Configuration ---
    db_user: str = Field(..., description="Database username")
    db_password: str = Field(..., description="Database password")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="postgres", description="Database name")
    
    # --- LLM Configuration ---
    openai_api_key: str = Field(..., description="OpenAI API key for LLM access")
    
    # --- LangSmith Configuration ---
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangSmith tracing")
    langchain_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langchain_endpoint: str = Field(default="https://api.smith.langchain.com", description="LangSmith endpoint")
    langchain_project: str = Field(default="Multi-DB SQL Agent", description="LangSmith project name")
    
    # --- Application Configuration ---
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # --- RabbitMQ Configuration ---
    rabbitmq_host: str = Field(default="localhost", description="RabbitMQ host")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_user: str = Field(default="guest", description="RabbitMQ username")
    rabbitmq_password: str = Field(default="guest", description="RabbitMQ password")
    rabbitmq_vhost: str = Field(default="/", description="RabbitMQ virtual host")
    task_timeout: int = Field(default=300, description="Task timeout in seconds")
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost/", description="RabbitMQ URL")
    
    # --- Frontend Configuration ---
    frontend_host: str = Field(default="localhost", description="Frontend host")
    frontend_port: int = Field(default=3001, description="Frontend port")
    
    # --- API Server Configuration ---
    api_host: str = Field(default="localhost", description="API server host")
    api_port: int = Field(default=8001, description="API server port")
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3001", 
            "http://127.0.0.1:3001", 
            "http://localhost:3000", 
            "http://127.0.0.1:3000"
        ], 
        description="CORS allowed origins"
    )
    
    # --- Google OAuth Configuration ---
    google_client_id: str = Field(..., description="Google OAuth client ID")
    google_client_secret: str = Field(..., description="Google OAuth client secret")
    google_redirect_uri: str = Field(default="", description="Google OAuth redirect URI (auto-generated if empty)")
    
    # --- JWT Configuration ---
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=480, description="JWT access token expire minutes")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from environment
    
    @validator('openai_api_key')
    def validate_openai_api_key(cls, v):
        if not v or not v.strip():
            raise ValueError("OPENAI_API_KEY is required and cannot be empty")
        return v.strip()
    
    @validator('db_user')
    def validate_db_user(cls, v):
        if not v or not v.strip():
            raise ValueError("DB_USER is required and cannot be empty")
        return v.strip()
    
    @validator('db_password')
    def validate_db_password(cls, v):
        if not v or not v.strip():
            raise ValueError("DB_PASSWORD is required and cannot be empty")
        return v.strip()
    
    @validator('db_port')
    def validate_db_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("DB_PORT must be between 1 and 65535")
        return v
    
    @validator('google_client_id')
    def validate_google_client_id(cls, v):
        if not v or not v.strip():
            raise ValueError("GOOGLE_CLIENT_ID is required and cannot be empty")
        return v.strip()
    
    @validator('google_client_secret')
    def validate_google_client_secret(cls, v):
        if not v or not v.strip():
            raise ValueError("GOOGLE_CLIENT_SECRET is required and cannot be empty")
        return v.strip()
    
    @validator('jwt_secret_key')
    def validate_jwt_secret_key(cls, v):
        if not v or not v.strip():
            raise ValueError("JWT_SECRET_KEY is required and cannot be empty")
        return v.strip()
    
    def model_post_init(self, __context) -> None:
        """Set up LangSmith environment variables after initialization."""
        if self.langchain_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = str(self.langchain_tracing_v2).lower()
            os.environ["LANGCHAIN_API_KEY"] = self.langchain_api_key
            os.environ["LANGCHAIN_ENDPOINT"] = self.langchain_endpoint
            os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
            if self.debug:
                print("✅ LangSmith tracing enabled")
        else:
            if self.debug:
                print("⚠️  LangSmith API key not found - tracing disabled")
    
    @property
    def encoded_db_user(self) -> str:
        """URL-encoded database username for connection strings."""
        return quote_plus(self.db_user)
    
    @property
    def encoded_db_password(self) -> str:
        """URL-encoded database password for connection strings."""
        return quote_plus(self.db_password)
    
    def get_database_uri(self, db_name: str = None) -> str:
        """Create a database URI for a specific database."""
        if db_name is None:
            db_name = self.db_name
        return f"postgresql+psycopg2://{self.encoded_db_user}:{self.encoded_db_password}@{self.db_host}:{self.db_port}/{db_name}"
    
    @property
    def default_database_uri(self) -> str:
        """Default database URI for backward compatibility."""
        return self.get_database_uri(self.db_name)
    
    @property
    def api_base_url(self) -> str:
        """API server base URL."""
        return f"http://{self.api_host}:{self.api_port}"
    
    @property
    def frontend_base_url(self) -> str:
        """Frontend base URL."""
        return f"http://{self.frontend_host}:{self.frontend_port}"
    
    @property
    def api_docs_url(self) -> str:
        """API documentation URL."""
        return f"{self.api_base_url}/docs"
    
    @property
    def api_health_url(self) -> str:
        """API health check URL."""
        return f"{self.api_base_url}/health"
    
    @property
    def oauth_redirect_uri(self) -> str:
        """Generate OAuth redirect URI dynamically."""
        if self.google_redirect_uri:
            return self.google_redirect_uri
        return f"{self.api_base_url}/auth/google/callback"
    
    def list_available_databases(self) -> list[str]:
        """List all available databases in the PostgreSQL server."""
        try:
            # Connect to the default database to list all databases
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT datname 
                FROM pg_database 
                WHERE datistemplate = false 
                AND datname NOT IN ('postgres', 'template0', 'template1')
                ORDER BY datname;
            """)
            
            databases = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            if self.debug:
                print(f"📊 Available databases: {databases}")
            
            return databases
            
        except Exception as e:
            if self.debug:
                print(f"❌ Error listing databases: {e}")
            return []
    
    def get_database_connection(self, db_name: str):
        """Create a SQLAlchemy engine for a specific database."""
        try:
            engine = create_engine(self.get_database_uri(db_name))
            if self.debug:
                print(f"🔗 Connected to database: {db_name}")
            return engine
        except Exception as e:
            if self.debug:
                print(f"❌ Error connecting to database {db_name}: {e}")
            raise


# Global settings instance
settings = Settings()

# Backward compatibility exports
OPENAI_API_KEY = settings.openai_api_key
DB_USER = settings.db_user
DB_PASSWORD = settings.db_password
DB_HOST = settings.db_host
DB_PORT = settings.db_port
DEFAULT_DB_NAME = settings.db_name
DATABASE_URI = settings.default_database_uri
LANGCHAIN_PROJECT = settings.langchain_project

# Function exports for backward compatibility
def get_database_uri(db_name: str) -> str:
    """Create a database URI for a specific database."""
    return settings.get_database_uri(db_name)

def list_available_databases() -> list[str]:
    """List all available databases in the PostgreSQL server."""
    return settings.list_available_databases()

def get_database_connection(db_name: str):
    """Create a SQLAlchemy engine for a specific database."""
    return settings.get_database_connection(db_name)
