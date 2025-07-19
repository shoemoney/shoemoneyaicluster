"""
Database API for Exo Cluster

Provides database tools through the existing ChatGPT-compatible API
allowing AI models to interact with MariaDB securely.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from aiohttp import web
import aiohttp_cors
from exo.tools.mariadb_tools import query_database, get_database_schema, test_database_connection
import logging

logger = logging.getLogger(__name__)

class DatabaseAPI:
    """Database API extension for exo cluster"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        
    async def handle_database_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle database tool calls from AI models
        
        Supported tools:
        - query_database: Execute SQL queries
        - get_schema: Get database schema information  
        - test_connection: Test database connectivity
        """
        try:
            function_name = tool_call.get('function', {}).get('name', '')
            arguments = tool_call.get('function', {}).get('arguments', {})
            
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            
            if function_name == 'query_database':
                result = await query_database(
                    query=arguments.get('query', ''),
                    params=arguments.get('params'),
                    config_path=self.config_path
                )
                
            elif function_name == 'get_database_schema':
                result = await get_database_schema(config_path=self.config_path)
                
            elif function_name == 'test_database_connection':
                result = await test_database_connection(config_path=self.config_path)
                
            else:
                result = {
                    'success': False,
                    'error': f'Unknown database function: {function_name}'
                }
            
            return {
                'tool_call_id': tool_call.get('id', ''),
                'content': json.dumps(result, indent=2)
            }
            
        except Exception as e:
            logger.error(f"Database tool call error: {e}")
            return {
                'tool_call_id': tool_call.get('id', ''),
                'content': json.dumps({
                    'success': False,
                    'error': f'Database tool error: {str(e)}'
                }, indent=2)
            }

def get_database_tools() -> List[Dict[str, Any]]:
    """
    Get database tool definitions for AI models
    
    Returns tool schemas that models can use in function calling
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": "Execute a SQL query on the MariaDB database. Supports SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE, and EXPLAIN statements. Queries are validated for security.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute. Must start with SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE, or EXPLAIN."
                        },
                        "params": {
                            "type": "array",
                            "description": "Optional parameters for prepared statements",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "get_database_schema",
                "description": "Get comprehensive database schema information including all tables, columns, data types, and row counts.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "test_database_connection", 
                "description": "Test the database connection and get connection statistics.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]

async def handle_database_request(request):
    """HTTP endpoint for database operations"""
    try:
        data = await request.json()
        action = data.get('action')
        
        if action == 'tools':
            # Return available database tools
            return web.json_response({
                'success': True,
                'tools': get_database_tools()
            })
            
        elif action == 'execute':
            # Execute a tool call
            db_api = DatabaseAPI(config_path=data.get('config_path'))
            result = await db_api.handle_database_tool_call(data.get('tool_call', {}))
            return web.json_response({
                'success': True,
                'result': result
            })
            
        elif action == 'test':
            # Test connection
            result = await test_database_connection(config_path=data.get('config_path'))
            return web.json_response(result)
            
        else:
            return web.json_response({
                'success': False,
                'error': f'Unknown action: {action}'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Database API error: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

def setup_database_routes(app: web.Application, cors: aiohttp_cors.CorsConfig):
    """Setup database API routes"""
    
    # Add database endpoint
    db_resource = cors.add(app.router.add_resource("/database"))
    cors.add(db_resource.add_route("POST", handle_database_request))