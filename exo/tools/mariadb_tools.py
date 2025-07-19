"""
MariaDB Tools for AI Models

Provides secure database access with connection pooling, query validation,
and comprehensive logging for AI models running on exo clusters.
"""

import os
import json
import logging
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int = 3306
    user: str = 'exo_ai'
    password: str = ''
    database: str = 'exo_cluster'
    charset: str = 'utf8mb4'
    max_connections: int = 10
    connection_timeout: int = 30
    read_timeout: int = 30
    write_timeout: int = 30

@dataclass
class QueryResult:
    """Query execution result"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    rows_affected: int = 0
    error: Optional[str] = None
    execution_time: float = 0.0
    query_hash: Optional[str] = None

class QueryValidator:
    """Validates SQL queries for security and compliance"""
    
    # Allowed SQL operations
    ALLOWED_STATEMENTS = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE', 'EXPLAIN'
    }
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'DROP\s+(?:DATABASE|TABLE|INDEX|VIEW)',
        r'CREATE\s+(?:DATABASE|TABLE|INDEX|VIEW)',
        r'ALTER\s+(?:DATABASE|TABLE)',
        r'TRUNCATE\s+TABLE',
        r'GRANT\s+',
        r'REVOKE\s+',
        r'LOAD\s+DATA',
        r'INTO\s+OUTFILE',
        r'LOAD_FILE\s*\(',
        r'--\s*',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r';\s*DROP',  # SQL injection attempts
        r'UNION\s+(?:ALL\s+)?SELECT',  # Basic UNION injection
    ]
    
    @classmethod
    def validate_query(cls, query: str) -> tuple[bool, str]:
        """
        Validate SQL query for security
        
        Returns:
            (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Empty query"
        
        query_upper = query.upper().strip()
        
        # Check if query starts with allowed statement
        starts_with_allowed = any(
            query_upper.startswith(stmt) for stmt in cls.ALLOWED_STATEMENTS
        )
        
        if not starts_with_allowed:
            return False, f"Query must start with one of: {', '.join(cls.ALLOWED_STATEMENTS)}"
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False, f"Query contains dangerous pattern: {pattern}"
        
        # Limit query length
        if len(query) > 10000:
            return False, "Query too long (max 10000 characters)"
        
        return True, ""

class MariaDBConnectionPool:
    """Thread-safe connection pool for MariaDB"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = []
        self._pool_size = 0
        self._max_size = config.max_connections
        self._lock = asyncio.Lock()
        
    async def get_connection(self):
        """Get a connection from the pool"""
        async with self._lock:
            if self._pool:
                return self._pool.pop()
            
            if self._pool_size < self._max_size:
                try:
                    conn = pymysql.connect(
                        host=self.config.host,
                        port=self.config.port,
                        user=self.config.user,
                        password=self.config.password,
                        database=self.config.database,
                        charset=self.config.charset,
                        cursorclass=pymysql.cursors.DictCursor,
                        connect_timeout=self.config.connection_timeout,
                        read_timeout=self.config.read_timeout,
                        write_timeout=self.config.write_timeout,
                        autocommit=True
                    )
                    self._pool_size += 1
                    return conn
                except Exception as e:
                    logger.error(f"Failed to create database connection: {e}")
                    raise
            
            raise Exception("Connection pool exhausted")
    
    async def return_connection(self, conn):
        """Return a connection to the pool"""
        async with self._lock:
            if conn and conn.open:
                self._pool.append(conn)
            else:
                self._pool_size -= 1

class MariaDBTools:
    """
    MariaDB tools for AI models
    
    Provides secure database access with built-in query validation,
    connection pooling, and comprehensive logging.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        if pymysql is None:
            raise ImportError("pymysql is required. Install with: pip install pymysql")
        
        self.config = self._load_config(config_path)
        self.pool = MariaDBConnectionPool(self.config)
        self.validator = QueryValidator()
        self._query_history: List[Dict] = []
        self._max_history = 1000
        
    def _load_config(self, config_path: Optional[str] = None) -> DatabaseConfig:
        """Load database configuration from file or environment"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return DatabaseConfig(**config_data)
        
        # Load from environment variables
        return DatabaseConfig(
            host=os.getenv('MARIADB_HOST', 'localhost'),
            port=int(os.getenv('MARIADB_PORT', '3306')),
            user=os.getenv('MARIADB_USER', 'exo_ai'),
            password=os.getenv('MARIADB_PASSWORD', ''),
            database=os.getenv('MARIADB_DATABASE', 'exo_cluster'),
            charset=os.getenv('MARIADB_CHARSET', 'utf8mb4'),
            max_connections=int(os.getenv('MARIADB_MAX_CONNECTIONS', '10')),
        )
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query caching/tracking"""
        return hashlib.md5(query.encode()).hexdigest()[:16]
    
    def _log_query(self, query: str, result: QueryResult, user_context: str = "ai_model"):
        """Log query execution for auditing"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_context': user_context,
            'query_hash': result.query_hash,
            'query': query[:200] + '...' if len(query) > 200 else query,
            'success': result.success,
            'rows_affected': result.rows_affected,
            'execution_time': result.execution_time,
            'error': result.error
        }
        
        self._query_history.append(log_entry)
        
        # Trim history if too long
        if len(self._query_history) > self._max_history:
            self._query_history = self._query_history[-self._max_history:]
        
        logger.info(f"Query executed: {log_entry}")
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        user_context: str = "ai_model"
    ) -> QueryResult:
        """
        Execute a SQL query with validation and logging
        
        Args:
            query: SQL query string
            params: Query parameters for prepared statements
            user_context: Context about who/what is executing the query
            
        Returns:
            QueryResult object with execution details
        """
        start_time = datetime.now()
        query_hash = self._hash_query(query)
        
        # Validate query
        is_valid, error_msg = self.validator.validate_query(query)
        if not is_valid:
            result = QueryResult(
                success=False,
                error=f"Query validation failed: {error_msg}",
                query_hash=query_hash
            )
            self._log_query(query, result, user_context)
            return result
        
        conn = None
        try:
            conn = await self.pool.get_connection()
            
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get results for SELECT queries
                if query.strip().upper().startswith('SELECT'):
                    data = cursor.fetchall()
                    rows_affected = len(data) if data else 0
                else:
                    data = None
                    rows_affected = cursor.rowcount
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = QueryResult(
                    success=True,
                    data=data,
                    rows_affected=rows_affected,
                    execution_time=execution_time,
                    query_hash=query_hash
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            result = QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                query_hash=query_hash
            )
            logger.error(f"Query execution failed: {e}")
        
        finally:
            if conn:
                await self.pool.return_connection(conn)
        
        self._log_query(query, result, user_context)
        return result
    
    async def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            result = await self.execute_query("SELECT 1 as test", user_context="connection_test")
            return result.success
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_tables(self) -> QueryResult:
        """Get list of tables in the current database"""
        return await self.execute_query("SHOW TABLES", user_context="schema_info")
    
    async def describe_table(self, table_name: str) -> QueryResult:
        """Get table structure"""
        # Validate table name to prevent injection
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return QueryResult(
                success=False,
                error="Invalid table name format"
            )
        
        query = f"DESCRIBE `{table_name}`"
        return await self.execute_query(query, user_context="schema_info")
    
    async def get_table_count(self, table_name: str) -> QueryResult:
        """Get row count for a table"""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return QueryResult(
                success=False,
                error="Invalid table name format"
            )
        
        query = f"SELECT COUNT(*) as row_count FROM `{table_name}`"
        return await self.execute_query(query, user_context="table_stats")
    
    def get_query_history(self, limit: int = 50) -> List[Dict]:
        """Get recent query history"""
        return self._query_history[-limit:]
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            'pool_size': self.pool._pool_size,
            'max_connections': self.pool._max_size,
            'available_connections': len(self.pool._pool),
            'config': {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.user
            }
        }

# Tool functions for AI models
async def query_database(
    query: str, 
    params: Optional[tuple] = None,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a database query (main interface for AI models)
    
    Args:
        query: SQL query string
        params: Optional query parameters
        config_path: Optional path to database config file
        
    Returns:
        Dictionary with query results
    """
    try:
        db_tools = MariaDBTools(config_path)
        result = await db_tools.execute_query(query, params)
        
        return {
            'success': result.success,
            'data': result.data,
            'rows_affected': result.rows_affected,
            'execution_time': result.execution_time,
            'error': result.error,
            'query_hash': result.query_hash
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Database tool error: {str(e)}",
            'data': None,
            'rows_affected': 0,
            'execution_time': 0.0
        }

async def get_database_schema(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get database schema information
    
    Returns:
        Dictionary with schema details
    """
    try:
        db_tools = MariaDBTools(config_path)
        
        # Get tables
        tables_result = await db_tools.get_tables()
        if not tables_result.success:
            return {'success': False, 'error': tables_result.error}
        
        schema_info = {
            'success': True,
            'database': db_tools.config.database,
            'tables': []
        }
        
        # Get structure for each table
        if tables_result.data:
            for table_row in tables_result.data:
                table_name = list(table_row.values())[0]  # First column contains table name
                
                desc_result = await db_tools.describe_table(table_name)
                count_result = await db_tools.get_table_count(table_name)
                
                table_info = {
                    'name': table_name,
                    'columns': desc_result.data if desc_result.success else [],
                    'row_count': count_result.data[0]['row_count'] if count_result.success and count_result.data else 0
                }
                
                schema_info['tables'].append(table_info)
        
        return schema_info
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Schema retrieval error: {str(e)}"
        }

async def test_database_connection(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Test database connection
    
    Returns:
        Dictionary with connection status
    """
    try:
        db_tools = MariaDBTools(config_path)
        is_connected = await db_tools.test_connection()
        
        return {
            'success': is_connected,
            'message': 'Database connection successful' if is_connected else 'Database connection failed',
            'stats': db_tools.get_connection_stats()
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Connection test error: {str(e)}"
        }