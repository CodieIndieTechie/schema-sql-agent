#!/usr/bin/env python3
"""
Database Discovery Service for Multi-Database SQL Agent

Provides comprehensive discovery capabilities to explore PostgreSQL databases,
schemas, tables, and columns dynamically.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from settings import settings

logger = logging.getLogger(__name__)


class DatabaseDiscoveryService:
    """Service for discovering database structures dynamically."""
    
    def __init__(self):
        self.connection_cache = {}
        
    def get_database_connection(self, db_name: str) -> Engine:
        """Get or create a SQLAlchemy engine for a specific database."""
        if db_name not in self.connection_cache:
            try:
                db_uri = settings.get_database_uri(db_name)
                engine = create_engine(db_uri)
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.connection_cache[db_name] = engine
                logger.info(f"✅ Connected to database: {db_name}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to database {db_name}: {e}")
                raise
        
        return self.connection_cache[db_name]
    
    def list_available_databases(self) -> List[str]:
        """List all available databases on the PostgreSQL server."""
        try:
            # Connect to the default database to list all databases
            conn = psycopg2.connect(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name  # Connect to default postgres database
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
            
            logger.info(f"📊 Discovered databases: {databases}")
            return databases
            
        except Exception as e:
            logger.error(f"❌ Error listing databases: {e}")
            return []
    
    def list_schemas_in_database(self, db_name: str, exclude_system: bool = True) -> List[str]:
        """List all schemas in a specific database."""
        try:
            engine = self.get_database_connection(db_name)
            
            query = """
                SELECT schema_name 
                FROM information_schema.schemata 
            """
            
            if exclude_system:
                query += """
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                """
            
            query += " ORDER BY schema_name;"
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                schemas = [row[0] for row in result.fetchall()]
            
            logger.info(f"📁 Schemas in {db_name}: {schemas}")
            return schemas
            
        except Exception as e:
            logger.error(f"❌ Error listing schemas in {db_name}: {e}")
            return []
    
    def list_tables_in_schema(self, db_name: str, schema_name: str) -> List[Dict[str, Any]]:
        """List all tables in a specific schema with basic metadata."""
        try:
            engine = self.get_database_connection(db_name)
            
            query = """
                SELECT 
                    t.table_name,
                    t.table_type,
                    COALESCE(
                        (SELECT COUNT(*) 
                         FROM information_schema.columns c 
                         WHERE c.table_schema = t.table_schema 
                         AND c.table_name = t.table_name), 0
                    ) as column_count
                FROM information_schema.tables t
                WHERE t.table_schema = :schema_name
                AND t.table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY t.table_name;
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {"schema_name": schema_name})
                tables = []
                
                for row in result.fetchall():
                    tables.append({
                        'name': row[0],
                        'type': row[1],
                        'column_count': row[2],
                        'schema': schema_name,
                        'database': db_name
                    })
            
            logger.info(f"📋 Tables in {db_name}.{schema_name}: {len(tables)} tables")
            return tables
            
        except Exception as e:
            logger.error(f"❌ Error listing tables in {db_name}.{schema_name}: {e}")
            return []
    
    def get_table_columns(self, db_name: str, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed column information for a specific table."""
        try:
            engine = self.get_database_connection(db_name)
            
            query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_schema = :schema_name
                AND table_name = :table_name
                ORDER BY ordinal_position;
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query), {
                    "schema_name": schema_name,
                    "table_name": table_name
                })
                
                columns = []
                for row in result.fetchall():
                    columns.append({
                        'name': row[0],
                        'data_type': row[1],
                        'is_nullable': row[2],
                        'default': row[3],
                        'max_length': row[4],
                        'precision': row[5],
                        'scale': row[6],
                        'position': row[7]
                    })
            
            logger.info(f"🏷️  Columns in {db_name}.{schema_name}.{table_name}: {len(columns)} columns")
            return columns
            
        except Exception as e:
            logger.error(f"❌ Error getting columns for {db_name}.{schema_name}.{table_name}: {e}")
            return []
    
    def get_comprehensive_database_info(self, include_columns: bool = True, 
                                      max_tables_per_schema: int = 50) -> Dict[str, Any]:
        """
        Get comprehensive information about all accessible databases.
        
        Args:
            include_columns: Whether to include column details for each table
            max_tables_per_schema: Maximum tables to analyze per schema (to prevent overload)
            
        Returns:
            Comprehensive database structure dictionary
        """
        logger.info("🔍 Starting comprehensive database discovery...")
        
        discovery_info = {
            'databases': [],
            'discovery_timestamp': None,
            'total_databases': 0,
            'total_schemas': 0,
            'total_tables': 0,
            'errors': []
        }
        
        try:
            # Get all available databases
            databases = self.list_available_databases()
            discovery_info['total_databases'] = len(databases)
            
            for db_name in databases:
                db_info = {
                    'name': db_name,
                    'schemas': [],
                    'accessible': True
                }
                
                try:
                    # Get schemas in this database
                    schemas = self.list_schemas_in_database(db_name)
                    discovery_info['total_schemas'] += len(schemas)
                    
                    for schema_name in schemas:
                        schema_info = {
                            'name': schema_name,
                            'tables': [],
                            'table_count': 0
                        }
                        
                        try:
                            # Get tables in this schema
                            tables = self.list_tables_in_schema(db_name, schema_name)
                            
                            # Limit tables to prevent overload
                            limited_tables = tables[:max_tables_per_schema]
                            if len(tables) > max_tables_per_schema:
                                logger.warning(f"⚠️  Limited tables in {db_name}.{schema_name} to {max_tables_per_schema}")
                            
                            schema_info['table_count'] = len(tables)
                            discovery_info['total_tables'] += len(tables)
                            
                            for table_info in limited_tables:
                                table_detail = {
                                    'name': table_info['name'],
                                    'type': table_info['type'],
                                    'column_count': table_info['column_count']
                                }
                                
                                # Include column details if requested
                                if include_columns:
                                    try:
                                        columns = self.get_table_columns(
                                            db_name, schema_name, table_info['name']
                                        )
                                        table_detail['columns'] = columns
                                    except Exception as e:
                                        logger.error(f"❌ Error getting columns for {table_info['name']}: {e}")
                                        table_detail['columns'] = []
                                        discovery_info['errors'].append(
                                            f"Column discovery failed for {db_name}.{schema_name}.{table_info['name']}: {e}"
                                        )
                                
                                schema_info['tables'].append(table_detail)
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing schema {schema_name} in {db_name}: {e}")
                            discovery_info['errors'].append(f"Schema processing failed for {db_name}.{schema_name}: {e}")
                        
                        db_info['schemas'].append(schema_info)
                    
                except Exception as e:
                    logger.error(f"❌ Error accessing database {db_name}: {e}")
                    db_info['accessible'] = False
                    discovery_info['errors'].append(f"Database access failed for {db_name}: {e}")
                
                discovery_info['databases'].append(db_info)
            
            # Add timestamp
            from datetime import datetime
            discovery_info['discovery_timestamp'] = datetime.now().isoformat()
            
            logger.info(f"✅ Discovery complete: {discovery_info['total_databases']} databases, "
                       f"{discovery_info['total_schemas']} schemas, {discovery_info['total_tables']} tables")
            
            if discovery_info['errors']:
                logger.warning(f"⚠️  Discovery completed with {len(discovery_info['errors'])} errors")
            
            return discovery_info
            
        except Exception as e:
            logger.error(f"❌ Critical error during database discovery: {e}")
            discovery_info['errors'].append(f"Critical discovery error: {e}")
            return discovery_info
    
    def get_user_specific_database_info(self, user_email: str) -> Dict[str, Any]:
        """
        Get database information specific to a user (for schema-per-tenant architecture).
        
        Args:
            user_email: User's email to determine their schema
            
        Returns:
            User-specific database information
        """
        from schema_migration import email_to_schema_name
        
        user_schema = email_to_schema_name(user_email)
        logger.info(f"🔍 Getting database info for user: {user_email} (schema: {user_schema})")
        
        try:
            # Get all available databases first
            available_databases = self.list_available_databases()
            logger.info(f"📊 Found {len(available_databases)} databases: {available_databases}")
            
            # Build user-specific info showing all databases
            user_db_info = {
                'databases': [],
                'current_database': settings.portfoliosql_db_name,  # Default to portfoliosql
                'current_schema': user_schema,
                'user_schema': user_schema,
                'user_email': user_email,
                'primary_database': settings.portfoliosql_db_name  # For backward compatibility
            }
            
            # Process each database
            for db_name in available_databases:
                try:
                    schemas = self.list_schemas_in_database(db_name)
                    db_info = {
                        'name': db_name,
                        'schemas': []
                    }
                    user_db_info['databases'].append(db_info)
                except Exception as db_error:
                    logger.warning(f"⚠️  Could not access database {db_name}: {db_error}")
                    # Still add the database to the list but without schema details
                    user_db_info['databases'].append({
                        'name': db_name,
                        'schemas': [],
                        'error': str(db_error)
                    })
                    continue
            
            # Now process schemas for each database
            for db_idx, db_info in enumerate(user_db_info['databases']):
                if 'error' in db_info:
                    continue  # Skip databases with errors
                    
                db_name = db_info['name']
                try:
                    schemas = self.list_schemas_in_database(db_name)
                    
                    # Get schema info for this database
                    for schema_name in schemas:
                        schema_info = {
                            'name': schema_name,
                            'tables': [],
                            'is_user_schema': schema_name == user_schema
                        }
                        
                        # Get detailed info for user's schema, basic info for others
                        if schema_name == user_schema:
                            tables = self.list_tables_in_schema(db_name, schema_name)
                            for table_info in tables:
                                table_detail = {
                                    'name': table_info['name'],
                                    'type': table_info['type'],
                                    'column_count': table_info['column_count'],
                                    'columns': self.get_table_columns(db_name, schema_name, table_info['name'])
                                }
                                schema_info['tables'].append(table_detail)
                        else:
                            # Just get table names for other schemas (for context)
                            tables = self.list_tables_in_schema(db_name, schema_name)
                            schema_info['tables'] = [{'name': t['name'], 'type': t['type']} for t in tables[:5]]  # Limit to 5
                        
                        user_db_info['databases'][db_idx]['schemas'].append(schema_info)
                        
                except Exception as schema_error:
                    logger.warning(f"⚠️  Could not get schemas for database {db_name}: {schema_error}")
            
            logger.info(f"✅ User-specific database info ready for {user_email}")
            return user_db_info
            
        except Exception as e:
            logger.error(f"❌ Error getting user-specific database info: {e}")
            return {
                'databases': [],
                'current_database': settings.portfoliosql_db_name,
                'current_schema': user_schema,
                'user_schema': user_schema,
                'user_email': user_email,
                'primary_database': settings.portfoliosql_db_name,  # For backward compatibility
                'error': str(e)
            }
    
    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to all discovered databases."""
        logger.info("🧪 Testing database connectivity...")
        
        test_results = {
            'accessible_databases': [],
            'failed_databases': [],
            'total_tested': 0,
            'success_rate': 0.0
        }
        
        databases = self.list_available_databases()
        test_results['total_tested'] = len(databases)
        
        for db_name in databases:
            try:
                engine = self.get_database_connection(db_name)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT current_database(), current_user"))
                    row = result.fetchone()
                    
                test_results['accessible_databases'].append({
                    'name': db_name,
                    'current_user': row[1] if row else 'unknown'
                })
                
            except Exception as e:
                test_results['failed_databases'].append({
                    'name': db_name,
                    'error': str(e)
                })
        
        test_results['success_rate'] = (
            len(test_results['accessible_databases']) / test_results['total_tested'] 
            if test_results['total_tested'] > 0 else 0.0
        )
        
        logger.info(f"✅ Connectivity test complete: {len(test_results['accessible_databases'])}/{test_results['total_tested']} databases accessible")
        return test_results


# Global instance
discovery_service = DatabaseDiscoveryService()


# Convenience functions
def discover_all_databases(include_columns: bool = True) -> Dict[str, Any]:
    """Discover all database structures."""
    return discovery_service.get_comprehensive_database_info(include_columns=include_columns)


def discover_user_databases(user_email: str) -> Dict[str, Any]:
    """Discover database structures for a specific user."""
    return discovery_service.get_user_specific_database_info(user_email)


def list_databases() -> List[str]:
    """List all available databases."""
    return discovery_service.list_available_databases()


def test_connectivity() -> Dict[str, Any]:
    """Test database connectivity."""
    return discovery_service.test_database_connectivity()


if __name__ == "__main__":
    # Test the discovery service
    import json
    
    print("=== DATABASE DISCOVERY TEST ===")
    
    # Test basic database listing
    print("\n1. Listing databases...")
    databases = list_databases()
    print(f"Found databases: {databases}")
    
    # Test connectivity
    print("\n2. Testing connectivity...")
    connectivity = test_connectivity()
    print(json.dumps(connectivity, indent=2))
    
    # Test comprehensive discovery (limited)
    print("\n3. Running comprehensive discovery...")
    discovery = discover_all_databases(include_columns=False)  # Skip columns for faster test
    print(f"Discovery summary: {discovery['total_databases']} databases, {discovery['total_schemas']} schemas, {discovery['total_tables']} tables")
    
    if discovery['errors']:
        print(f"Errors encountered: {len(discovery['errors'])}")
