#!/usr/bin/env python3
"""
MariaDB Tool for AI Models
Designed for high-performance distributed access across Mac M4 Studio cluster
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager

import aiomysql
from aiomysql import Pool
import pymysql
from pymysql.cursors import DictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MariaDBTool:
    """Async MariaDB tool optimized for AI model access across distributed systems"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize MariaDB tool with connection configuration"""
        self.config = config or self._load_config()
        self.pool: Optional[Pool] = None
        self.sync_connection = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or file"""
        config = {
            'host': os.getenv('MARIADB_HOST', 'localhost'),
            'port': int(os.getenv('MARIADB_PORT', '3306')),
            'user': os.getenv('MARIADB_USER', 'root'),
            'password': os.getenv('MARIADB_PASSWORD', ''),
            'database': os.getenv('MARIADB_DATABASE', 'ai_models'),
            'pool_size': int(os.getenv('MARIADB_POOL_SIZE', '20')),
            'max_overflow': int(os.getenv('MARIADB_MAX_OVERFLOW', '10')),
            'pool_recycle': int(os.getenv('MARIADB_POOL_RECYCLE', '3600')),
            'charset': 'utf8mb4'
        }
        
        # Try to load from config file
        config_file = os.getenv('MARIADB_CONFIG_FILE', 'mariadb_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
                
        return config
    
    async def initialize(self):
        """Initialize connection pool"""
        if not self.pool:
            self.pool = await aiomysql.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                db=self.config['database'],
                charset=self.config['charset'],
                minsize=1,
                maxsize=self.config['pool_size'],
                pool_recycle_time=self.config['pool_recycle'],
                autocommit=True
            )
            logger.info(f"MariaDB pool initialized: {self.config['host']}:{self.config['port']}")
    
    async def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            
        if self.sync_connection:
            self.sync_connection.close()
            self.sync_connection = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                yield cursor
    
    async def execute(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute a single query"""
        async with self.get_connection() as cursor:
            await cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                result = await cursor.fetchall()
                return {'status': 'success', 'data': result, 'rowcount': cursor.rowcount}
            else:
                return {'status': 'success', 'rowcount': cursor.rowcount, 'lastrowid': cursor.lastrowid}
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> Dict[str, Any]:
        """Execute multiple queries with different parameters"""
        async with self.get_connection() as cursor:
            await cursor.executemany(query, params_list)
            return {'status': 'success', 'rowcount': cursor.rowcount}
    
    async def batch_execute(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple different queries in a batch"""
        results = []
        async with self.get_connection() as cursor:
            for query_dict in queries:
                query = query_dict.get('query')
                params = query_dict.get('params')
                
                try:
                    await cursor.execute(query, params)
                    
                    if query.strip().upper().startswith('SELECT'):
                        result = await cursor.fetchall()
                        results.append({'status': 'success', 'data': result})
                    else:
                        results.append({'status': 'success', 'rowcount': cursor.rowcount})
                except Exception as e:
                    results.append({'status': 'error', 'error': str(e)})
                    
        return results
    
    # Sync methods for compatibility
    def sync_execute(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Synchronous query execution"""
        if not self.sync_connection:
            self.sync_connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config['charset'],
                cursorclass=DictCursor
            )
            
        with self.sync_connection.cursor() as cursor:
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                return {'status': 'success', 'data': result, 'rowcount': cursor.rowcount}
            else:
                self.sync_connection.commit()
                return {'status': 'success', 'rowcount': cursor.rowcount, 'lastrowid': cursor.lastrowid}
    
    # Utility methods for AI models
    async def store_model_output(self, model_name: str, output: Dict[str, Any], 
                                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store AI model output in database"""
        query = """
        INSERT INTO model_outputs (model_name, output, metadata, created_at)
        VALUES (%s, %s, %s, %s)
        """
        params = (
            model_name,
            json.dumps(output),
            json.dumps(metadata or {}),
            datetime.utcnow()
        )
        return await self.execute(query, params)
    
    async def get_model_history(self, model_name: str, limit: int = 100) -> Dict[str, Any]:
        """Get model output history"""
        query = """
        SELECT id, model_name, output, metadata, created_at
        FROM model_outputs
        WHERE model_name = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        return await self.execute(query, (model_name, limit))
    
    async def create_tables(self):
        """Create necessary tables for AI model data"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS model_outputs (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                model_name VARCHAR(255) NOT NULL,
                output JSON,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_model_name (model_name),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS model_metrics (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                model_name VARCHAR(255) NOT NULL,
                metric_name VARCHAR(255) NOT NULL,
                metric_value DOUBLE,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_model_metric (model_name, metric_name),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS cluster_nodes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                node_name VARCHAR(255) UNIQUE NOT NULL,
                node_ip VARCHAR(45),
                memory_gb INT,
                status VARCHAR(50),
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                metadata JSON,
                INDEX idx_status (status),
                INDEX idx_heartbeat (last_heartbeat)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        ]
        
        for table_query in tables:
            await self.execute(table_query)
            
        logger.info("Database tables created successfully")


# CLI interface for testing
async def main():
    """CLI interface for testing MariaDB tool"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MariaDB Tool for AI Models')
    parser.add_argument('--host', help='MariaDB host')
    parser.add_argument('--port', type=int, help='MariaDB port')
    parser.add_argument('--user', help='MariaDB user')
    parser.add_argument('--password', help='MariaDB password')
    parser.add_argument('--database', help='MariaDB database')
    parser.add_argument('--create-tables', action='store_true', help='Create necessary tables')
    parser.add_argument('--test', action='store_true', help='Run connection test')
    
    args = parser.parse_args()
    
    # Build config from args
    config = {}
    if args.host:
        config['host'] = args.host
    if args.port:
        config['port'] = args.port
    if args.user:
        config['user'] = args.user
    if args.password:
        config['password'] = args.password
    if args.database:
        config['database'] = args.database
    
    # Initialize tool
    tool = MariaDBTool(config if config else None)
    
    try:
        await tool.initialize()
        
        if args.create_tables:
            await tool.create_tables()
            print("Tables created successfully")
            
        if args.test:
            # Test connection
            result = await tool.execute("SELECT VERSION() as version")
            print(f"Connected to MariaDB: {result['data'][0]['version']}")
            
            # Test table existence
            result = await tool.execute("SHOW TABLES")
            print(f"Available tables: {[t[list(t.keys())[0]] for t in result['data']]}")
            
    finally:
        await tool.close()


if __name__ == '__main__':
    asyncio.run(main())