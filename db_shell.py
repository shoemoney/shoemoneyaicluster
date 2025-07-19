#!/usr/bin/env python3
"""
MariaDB Shell Tool for Exo Cluster

Interactive command-line interface for database operations.
Provides testing and administration capabilities for the MariaDB tools.
"""

import asyncio
import json
import sys
import os
import argparse
from typing import Optional
from exo.tools.mariadb_tools import MariaDBTools, query_database, get_database_schema, test_database_connection

class DatabaseShell:
    """Interactive database shell for exo cluster"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.db_tools = None
        
    async def initialize(self):
        """Initialize database connection"""
        try:
            self.db_tools = MariaDBTools(self.config_path)
            print(f"🔗 Connecting to MariaDB...")
            is_connected = await self.db_tools.test_connection()
            
            if is_connected:
                print(f"✅ Connected to {self.db_tools.config.host}:{self.db_tools.config.port}")
                print(f"📊 Database: {self.db_tools.config.database}")
                print(f"👤 User: {self.db_tools.config.user}")
                return True
            else:
                print("❌ Failed to connect to database")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def run_query(self, query: str):
        """Execute a single query"""
        try:
            result = await self.db_tools.execute_query(query, user_context="shell")
            
            if result.success:
                print(f"✅ Query executed successfully")
                print(f"⏱️  Execution time: {result.execution_time:.3f}s")
                print(f"📊 Rows affected: {result.rows_affected}")
                
                if result.data:
                    self._print_table(result.data)
            else:
                print(f"❌ Query failed: {result.error}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def show_schema(self):
        """Display database schema"""
        try:
            schema = await get_database_schema(self.config_path)
            
            if schema['success']:
                print(f"\n📋 Database Schema: {schema['database']}")
                print("=" * 50)
                
                for table in schema['tables']:
                    print(f"\n📁 Table: {table['name']} ({table['row_count']} rows)")
                    print("-" * 30)
                    
                    for col in table['columns']:
                        nullable = "NULL" if col.get('Null', 'YES') == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col.get('Default', 'None')}" if col.get('Default') else ""
                        print(f"  • {col.get('Field', 'unknown')}: {col.get('Type', 'unknown')} {nullable}{default}")
            else:
                print(f"❌ Failed to get schema: {schema.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Schema error: {e}")
    
    async def show_stats(self):
        """Display connection statistics"""
        try:
            stats = self.db_tools.get_connection_stats()
            print("\n📊 Connection Statistics")
            print("=" * 30)
            print(f"Pool size: {stats['pool_size']}")
            print(f"Max connections: {stats['max_connections']}")
            print(f"Available: {stats['available_connections']}")
            print(f"Host: {stats['config']['host']}:{stats['config']['port']}")
            print(f"Database: {stats['config']['database']}")
            print(f"User: {stats['config']['user']}")
            
        except Exception as e:
            print(f"❌ Stats error: {e}")
    
    async def show_history(self, limit: int = 10):
        """Display query history"""
        try:
            history = self.db_tools.get_query_history(limit)
            
            print(f"\n📜 Query History (last {limit})")
            print("=" * 50)
            
            for entry in history:
                status = "✅" if entry['success'] else "❌"
                print(f"{status} {entry['timestamp']} [{entry['query_hash']}]")
                print(f"   {entry['query']}")
                if entry['error']:
                    print(f"   Error: {entry['error']}")
                print(f"   Time: {entry['execution_time']:.3f}s, Rows: {entry['rows_affected']}")
                print()
                
        except Exception as e:
            print(f"❌ History error: {e}")
    
    def _print_table(self, data):
        """Print query results in table format"""
        if not data:
            print("📄 No rows returned")
            return
        
        # Get column names
        columns = list(data[0].keys()) if data else []
        
        if not columns:
            print("📄 Empty result set")
            return
        
        # Calculate column widths
        widths = {}
        for col in columns:
            widths[col] = max(len(str(col)), 
                            max(len(str(row.get(col, ''))) for row in data))
        
        # Print header
        print("\n" + "+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+")
        print("|" + "|".join(f" {col:<{widths[col]}} " for col in columns) + "|")
        print("+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+")
        
        # Print rows
        for row in data:
            print("|" + "|".join(f" {str(row.get(col, '')):<{widths[col]}} " for col in columns) + "|")
        
        print("+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+")
        print(f"📊 {len(data)} row(s) returned\n")
    
    async def interactive_shell(self):
        """Run interactive shell"""
        print("\n🐚 MariaDB Interactive Shell")
        print("Commands:")
        print("  .schema    - Show database schema")
        print("  .stats     - Show connection statistics") 
        print("  .history   - Show query history")
        print("  .quit      - Exit shell")
        print("  SQL query  - Execute SQL statement")
        print("-" * 50)
        
        while True:
            try:
                query = input("mariadb> ").strip()
                
                if not query:
                    continue
                
                if query == '.quit':
                    print("👋 Goodbye!")
                    break
                elif query == '.schema':
                    await self.show_schema()
                elif query == '.stats':
                    await self.show_stats()
                elif query == '.history':
                    await self.show_history()
                else:
                    await self.run_query(query)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="MariaDB Shell for Exo Cluster")
    parser.add_argument('--config', '-c', help='Path to database config file')
    parser.add_argument('--query', '-q', help='Execute single query and exit')
    parser.add_argument('--schema', '-s', action='store_true', help='Show schema and exit')
    parser.add_argument('--test', '-t', action='store_true', help='Test connection and exit')
    parser.add_argument('--stats', action='store_true', help='Show statistics and exit')
    
    args = parser.parse_args()
    
    shell = DatabaseShell(args.config)
    
    print("🚀 Exo MariaDB Shell")
    print("=" * 30)
    
    # Initialize connection
    if not await shell.initialize():
        sys.exit(1)
    
    try:
        if args.test:
            # Just test connection
            result = await test_database_connection(args.config)
            print(json.dumps(result, indent=2))
            
        elif args.schema:
            # Show schema
            await shell.show_schema()
            
        elif args.stats:
            # Show stats
            await shell.show_stats()
            
        elif args.query:
            # Execute single query
            await shell.run_query(args.query)
            
        else:
            # Interactive shell
            await shell.interactive_shell()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())