#!/usr/bin/env python3
"""
Agent Prompts for Multi-Database SQL Agent

Contains dynamic prompts and instructions for the SQL agent to work with
multiple databases, schemas, tables, and columns discovered dynamically.
"""

from typing import Dict, List, Optional


def get_database_schema_context(database_info: Dict) -> str:
    """
    Generate contextual information about available databases, schemas, and tables.
    
    Args:
        database_info: Dictionary containing database discovery information
            {
                'databases': [{'name': str, 'schemas': [{'name': str, 'tables': [{'name': str, 'columns': [...]}]}]}],
                'current_database': str,
                'current_schema': str,
                'user_schema': str (optional)
            }
    
    Returns:
        Formatted string containing database context information
    """
    context = []
    
    if 'databases' in database_info and database_info['databases']:
        context.append("📊 **AVAILABLE DATABASES AND STRUCTURES:**\n")
        
        for db in database_info['databases']:
            db_name = db.get('name', 'Unknown')
            context.append(f"🗄️  **Database: {db_name}**")
            
            if 'schemas' in db and db['schemas']:
                for schema in db['schemas']:
                    schema_name = schema.get('name', 'Unknown')
                    
                    # Mark current/user schema
                    if schema_name == database_info.get('current_schema') or schema_name == database_info.get('user_schema'):
                        context.append(f"   📂 **Schema: {schema_name}** (YOUR CURRENT SCHEMA)")
                    else:
                        context.append(f"   📂 Schema: {schema_name}")
                    
                    if 'tables' in schema and schema['tables']:
                        for table in schema['tables']:
                            table_name = table.get('name', 'Unknown')
                            context.append(f"      📋 Table: {table_name}")
                            
                            if 'columns' in table and table['columns']:
                                column_names = [col.get('name', 'Unknown') for col in table['columns']]
                                context.append(f"         Columns: {', '.join(column_names[:5])}")
                                if len(column_names) > 5:
                                    context.append(f"         ... and {len(column_names) - 5} more columns")
                    else:
                        context.append("      (No tables found)")
            else:
                context.append("   (No schemas found)")
    
    return "\n".join(context)


def get_dynamic_system_prompt(database_info: Dict, user_schema: Optional[str] = None) -> str:
    """
    Generate dynamic system prompt based on discovered database structure.
    
    Args:
        database_info: Dictionary containing database discovery information
        user_schema: User's specific schema name (for schema-per-tenant architecture)
    
    Returns:
        Complete system prompt for the SQL agent
    """
    
    # Get database context
    db_context = get_database_schema_context(database_info)
    
    # Determine current working context
    current_context = ""
    if user_schema:
        current_context = f"\n🎯 **YOUR WORKING CONTEXT:**\nYou are currently working in schema '{user_schema}' which contains your personal data.\n"
    elif database_info.get('current_database') or database_info.get('current_schema'):
        db_name = database_info.get('current_database', 'default')
        schema_name = database_info.get('current_schema', 'public')
        current_context = f"\n🎯 **YOUR WORKING CONTEXT:**\nCurrently connected to database '{db_name}', schema '{schema_name}'.\n"
    
    prompt = f"""You are an expert SQL assistant with access to PostgreSQL databases and their complete structure.

{current_context}

{db_context}

**🔍 DISCOVERY AND EXPLORATION:**
- Always use sql_db_list_tables to check available tables before querying
- Use sql_db_schema to understand table structures when needed  
- You can access data across different schemas using qualified names (schema.table)
- Focus on the user's current schema unless explicitly asked about other schemas

**⚡ QUERY EXECUTION GUIDELINES:**
1. **Be Efficient**: Minimize tool calls - don't repeatedly query the same information
2. **Start Smart**: Use sql_db_list_tables first if you need to explore available data
3. **Query Precisely**: Write targeted SQL queries, limit results to 5 rows unless specified
4. **Handle Errors Gracefully**: If a query fails, try a simpler approach instead of complex workarounds
5. **Stay Focused**: Answer the user's question directly with the data you retrieve

**📋 DATA RETRIEVAL BEST PRACTICES:**
- Use LIMIT clauses to prevent overwhelming responses
- When joining tables, be explicit about schema prefixes if needed
- For large datasets, provide summaries or aggregations rather than raw data dumps
- If exploring data structure, focus on relevant tables for the user's question

**💬 RESPONSE GUIDELINES:**
- Execute the necessary SQL queries to get the data
- Provide clear, concise answers based on your query results
- Stop after answering - don't ask follow-up questions unless clarification is needed
- If data spans multiple schemas/databases, clearly indicate the source

**📊 CHART AND VISUALIZATION GUIDELINES:**
- When users request charts, graphs, plots, or visualizations:
  1. **ALWAYS execute SQL queries first** to retrieve the actual data
  2. Return the data so it can be automatically converted to charts
  3. **NEVER provide manual instructions** for creating charts - the system will generate them automatically
- Keywords that indicate chart requests: "chart", "graph", "plot", "visualize", "draw", "show chart"
- Focus on getting the right data structure for effective visualization
- For charts, ensure data has meaningful columns that can be plotted (e.g., categories and values)

**🚨 IMPORTANT RULES:**
- You can query any accessible database/schema, but focus on the user's working context by default
- Always respect data privacy - only access what's necessary to answer the question
- If asked about data in other schemas, make sure the user has appropriate access
- When in doubt about data access, ask for clarification

Remember: You have full visibility into the database structure shown above. Use this knowledge to provide accurate, efficient responses to user queries."""

    return prompt


def get_schema_specific_prompt(schema_name: str, table_info: List[Dict]) -> str:
    """
    Generate a schema-specific prompt for focused queries within a single schema.
    
    Args:
        schema_name: Name of the specific schema
        table_info: List of table information dictionaries
    
    Returns:
        Schema-specific system prompt
    """
    
    table_context = ""
    if table_info:
        table_context = f"\n📊 **TABLES IN SCHEMA '{schema_name}':**\n"
        for table in table_info:
            table_name = table.get('name', 'Unknown')
            table_context += f"📋 {table_name}"
            if 'columns' in table and table['columns']:
                column_names = [col.get('name', '') for col in table['columns'] if col.get('name')]
                if column_names:
                    table_context += f" (Columns: {', '.join(column_names[:5])})"
                    if len(column_names) > 5:
                        table_context += f" + {len(column_names) - 5} more"
            table_context += "\n"
    
    prompt = f"""You are a SQL expert working specifically with the '{schema_name}' schema in PostgreSQL.

{table_context}

**🎯 FOCUSED OPERATIONS:**
- All queries will be executed within the '{schema_name}' schema
- Use sql_db_list_tables to see all available tables
- Use sql_db_schema for detailed table structure when needed
- Focus on providing precise, efficient answers

**⚡ EXECUTION GUIDELINES:**
1. Check available tables with sql_db_list_tables if needed
2. Query data efficiently with appropriate LIMIT clauses
3. Provide direct answers based on your query results
4. Stop after answering - be concise and helpful

Remember: You're working in a focused environment with schema '{schema_name}'. Make the most of the available data to answer user questions accurately."""

    return prompt


def get_multi_database_prompt(databases: List[str], current_db: str) -> str:
    """
    Generate prompt for multi-database access scenarios.
    
    Args:
        databases: List of available database names
        current_db: Currently connected database name
    
    Returns:
        Multi-database system prompt
    """
    
    db_list = "\n".join([f"• {db}" for db in databases])
    
    prompt = f"""You are a SQL expert with access to multiple PostgreSQL databases.

**🗄️ AVAILABLE DATABASES:**
{db_list}

**📍 CURRENT CONNECTION:** {current_db}

**🔄 MULTI-DATABASE OPERATIONS:**
- You can query the currently connected database directly
- To access other databases, you may need to specify full connection details
- Use sql_db_list_tables to explore available tables in the current database
- Focus queries on the current database unless specifically asked about others

**⚡ BEST PRACTICES:**
1. Start by exploring the current database structure
2. Use efficient queries with appropriate LIMIT clauses  
3. Provide clear answers based on available data
4. If asked about other databases, indicate any limitations in cross-database access

Remember: Work primarily with the current database ({current_db}) unless explicitly directed to use others."""

    return prompt


# Configuration for different prompt types
PROMPT_TEMPLATES = {
    'dynamic': get_dynamic_system_prompt,
    'schema_specific': get_schema_specific_prompt,
    'multi_database': get_multi_database_prompt
}


def get_agent_prompt(prompt_type: str = 'dynamic', **kwargs) -> str:
    """
    Get agent prompt based on type and provided context.
    
    Args:
        prompt_type: Type of prompt ('dynamic', 'schema_specific', 'multi_database')
        **kwargs: Context information for prompt generation
    
    Returns:
        Generated prompt string
    """
    if prompt_type in PROMPT_TEMPLATES:
        return PROMPT_TEMPLATES[prompt_type](**kwargs)
    else:
        # Fallback to dynamic prompt
        return get_dynamic_system_prompt(kwargs.get('database_info', {}))


# Example usage and testing
if __name__ == "__main__":
    # Example database info structure
    sample_db_info = {
        'databases': [
            {
                'name': 'portfoliosql',
                'schemas': [
                    {
                        'name': 'user_john_doe',
                        'tables': [
                            {
                                'name': 'customers',
                                'columns': [
                                    {'name': 'id', 'type': 'integer'},
                                    {'name': 'name', 'type': 'varchar'},
                                    {'name': 'email', 'type': 'varchar'}
                                ]
                            },
                            {
                                'name': 'orders',
                                'columns': [
                                    {'name': 'id', 'type': 'integer'},
                                    {'name': 'customer_id', 'type': 'integer'},
                                    {'name': 'total', 'type': 'decimal'}
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        'current_database': 'portfoliosql',
        'current_schema': 'user_john_doe'
    }
    
    print("=== SAMPLE DYNAMIC PROMPT ===")
    print(get_dynamic_system_prompt(sample_db_info, user_schema='user_john_doe'))
