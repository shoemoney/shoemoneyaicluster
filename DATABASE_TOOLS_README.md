# MariaDB Tools for Exo Cluster

This comprehensive database integration provides AI models in your exo cluster with secure, validated access to MariaDB databases. Perfect for Mac M4 Studio clusters with massive memory (2.4TB total) for handling large-scale data operations.

## 🚀 Quick Start

### 1. Auto Setup (Recommended)
```bash
# Run the automated setup script
./setup_database.sh
```

This will:
- Install MariaDB server if not present
- Create database and user with proper permissions
- Generate secure configuration file
- Create sample tables with cluster data
- Test the connection

### 2. Manual Setup

#### Install Dependencies
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y mariadb-server mariadb-client python3-pymysql

# macOS (with Homebrew)
brew install mariadb
pip3 install pymysql
```

#### Configure Database
```sql
-- Connect as root
mariadb -u root -p

-- Create database and user
CREATE DATABASE exo_cluster CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'exo_ai'@'%' IDENTIFIED BY 'your_secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE, SHOW VIEW ON exo_cluster.* TO 'exo_ai'@'%';
FLUSH PRIVILEGES;
```

#### Create Configuration
```json
{
  "host": "localhost",
  "port": 3306,
  "user": "exo_ai", 
  "password": "your_secure_password",
  "database": "exo_cluster",
  "charset": "utf8mb4",
  "max_connections": 20,
  "connection_timeout": 30,
  "read_timeout": 60,
  "write_timeout": 60
}
```

## 🛠️ Usage

### Database Shell
Interactive shell for testing and administration:

```bash
# Interactive shell
python3 db_shell.py --config db_config.json

# Execute single query
python3 db_shell.py --config db_config.json --query "SELECT * FROM ai_models"

# Show database schema
python3 db_shell.py --config db_config.json --schema

# Test connection
python3 db_shell.py --config db_config.json --test
```

### Shell Commands
```bash
mariadb> SELECT * FROM cluster_nodes WHERE status = 'online'
mariadb> .schema          # Show database schema
mariadb> .stats           # Show connection statistics  
mariadb> .history         # Show query history
mariadb> .quit            # Exit shell
```

### API Integration

The database tools are automatically integrated into the exo ChatGPT-compatible API. Models can use these function calls:

#### Available Functions

1. **query_database(query, params=None)**
   - Execute SQL queries (SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE, EXPLAIN)
   - Automatic query validation and security filtering
   - Returns formatted results with execution statistics

2. **get_database_schema()**
   - Get complete database schema information
   - Includes all tables, columns, data types, and row counts
   - Perfect for models to understand data structure

3. **test_database_connection()**
   - Test database connectivity
   - Get connection pool statistics
   - Useful for diagnostics

### Example Model Interactions

```python
# Models can call these functions directly
result = await query_database("SELECT COUNT(*) FROM cluster_nodes WHERE status = 'online'")

# Get schema for context
schema = await get_database_schema()

# Test connectivity  
status = await test_database_connection()
```

### HTTP API Endpoint

Direct HTTP access via `/database` endpoint:

```bash
# Get available database tools
curl -X POST http://localhost:8000/database \
  -H "Content-Type: application/json" \
  -d '{"action": "tools"}'

# Execute a query
curl -X POST http://localhost:8000/database \
  -H "Content-Type: application/json" \
  -d '{
    "action": "execute",
    "tool_call": {
      "function": {
        "name": "query_database",
        "arguments": {"query": "SELECT * FROM ai_models LIMIT 5"}
      }
    }
  }'

# Test connection
curl -X POST http://localhost:8000/database \
  -H "Content-Type: application/json" \
  -d '{"action": "test"}'
```

## 🔒 Security Features

### Query Validation
- **Whitelist Approach**: Only SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE, EXPLAIN allowed
- **Pattern Blocking**: Prevents DROP, CREATE, ALTER, TRUNCATE, GRANT operations
- **Injection Protection**: Blocks SQL injection patterns and comments
- **Length Limits**: Queries limited to 10,000 characters

### Database Permissions
- Limited user with no DDL (CREATE/DROP/ALTER) privileges
- No GRANT/REVOKE capabilities
- Read/write access only to designated tables
- Connection limits and timeouts

### Audit Logging
- All queries logged with timestamps and execution details
- Query hashing for tracking repeated operations
- User context tracking
- Error logging for failed operations
- Query history maintained (last 1000 queries)

## 📊 Sample Database Schema

The setup script creates sample tables optimized for AI cluster management:

### ai_models
```sql
CREATE TABLE ai_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    parameters BIGINT,
    memory_usage_gb DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### cluster_nodes  
```sql
CREATE TABLE cluster_nodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node_id VARCHAR(100) UNIQUE NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    cpu_cores INT,
    memory_gb INT,
    gpu_memory_gb INT DEFAULT 0,
    status ENUM('online', 'offline', 'maintenance') DEFAULT 'offline',
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### query_log
```sql
CREATE TABLE query_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    query_hash VARCHAR(32) NOT NULL,
    query_text TEXT,
    user_context VARCHAR(100),
    execution_time DECIMAL(10,6),
    rows_affected INT,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚡ Performance Optimizations

### Connection Pooling
- Configurable connection pool (default: 20 connections)
- Automatic connection recycling
- Connection timeout management
- Pool statistics monitoring

### Memory Efficiency
- Optimized for Mac M4 Studios with 128GB RAM each
- Efficient cursor management
- Automatic connection cleanup
- Minimal memory footprint per connection

### Query Optimization
- Query result caching capabilities
- Execution time tracking
- Query pattern analysis
- Index recommendations via EXPLAIN support

## 🔧 Configuration Options

### Environment Variables
Alternative to JSON config file:
```bash
export MARIADB_HOST='localhost'
export MARIADB_PORT='3306'
export MARIADB_USER='exo_ai'
export MARIADB_PASSWORD='your_password'
export MARIADB_DATABASE='exo_cluster'
export MARIADB_MAX_CONNECTIONS='20'
```

### Advanced Configuration
```json
{
  "host": "your-mariadb-host",
  "port": 3306,
  "user": "exo_ai",
  "password": "secure_password",
  "database": "exo_cluster", 
  "charset": "utf8mb4",
  "max_connections": 50,
  "connection_timeout": 30,
  "read_timeout": 120,
  "write_timeout": 120
}
```

## 🚨 Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
mariadb -h localhost -u exo_ai -p exo_cluster

# Check MariaDB service status
sudo systemctl status mariadb  # Linux
brew services list | grep mariadb  # macOS

# Test with our tool
python3 db_shell.py --config db_config.json --test
```

### Permission Issues
```sql
-- Check user privileges
SHOW GRANTS FOR 'exo_ai'@'%';

-- Re-grant permissions if needed
GRANT SELECT, INSERT, UPDATE, DELETE, SHOW VIEW ON exo_cluster.* TO 'exo_ai'@'%';
FLUSH PRIVILEGES;
```

### Performance Issues
```bash
# Monitor query performance
python3 db_shell.py --config db_config.json
mariadb> .history  # Check slow queries

# Connection pool stats
mariadb> .stats
```

## 🏗️ Architecture

### Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Models     │    │  Database API   │    │   MariaDB       │
│   (Exo Cluster) │ ←→ │   (Tools)       │ ←→ │   Server        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ↑                       ↑                       ↑
         │                       │                       │
    Function Calls          Validation &              Secure
    (query_database,        Connection Pool           Storage
     get_schema, etc.)                                
```

### Data Flow
1. **Model Request**: AI model calls database function
2. **Validation**: Query validated for security/syntax
3. **Execution**: Query executed via connection pool
4. **Logging**: Operation logged for auditing
5. **Response**: Results returned to model

## 🎯 Use Cases for Mac M4 Studio Cluster

### AI Model Management
- Track model deployments across cluster nodes
- Monitor memory usage and performance
- Coordinate model loading/unloading
- Store model configurations and metadata

### Cluster Monitoring
- Real-time node status tracking
- Resource utilization monitoring  
- Performance metrics collection
- Failure detection and alerting

### Data Analytics
- Query processing logs for insights
- Performance trend analysis
- Resource optimization planning
- Cost and efficiency tracking

### Knowledge Management
- Store and query large knowledge bases
- Document embeddings and metadata
- Conversation history and context
- Training data management

## 🔮 Future Enhancements

- **Read Replicas**: Support for read-only replicas for scaling
- **Distributed Queries**: Cross-node query execution
- **ML Integration**: Built-in ML functions and procedures
- **Real-time Analytics**: Stream processing capabilities
- **Vector Storage**: Vector embedding storage and similarity search
- **Backup/Recovery**: Automated backup and disaster recovery

## 📝 License

This database integration inherits the same license as the exo project.

## 🤝 Contributing

1. Follow existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure security validation for new query types
5. Test with actual Mac M4 Studio cluster setups

## 📞 Support

For issues specific to the database integration:
1. Check the troubleshooting section above
2. Test with the database shell tool
3. Verify MariaDB server configuration
4. Review query logs for patterns

For general exo cluster issues, refer to the main project documentation.