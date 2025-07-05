# BigQuery MCP Server

A Model Context Protocol server that provides secure, cross-project access to BigQuery datasets. Built with FastMCP for Python, enabling LLMs to explore data, analyze schemas, and execute queries across multiple Google Cloud projects.

## Key Features

- **Cross-Project Access** - Query data across multiple BigQuery projects with a single connection
- **Advanced Analytics** - Column-level analysis for nulls, cardinality, and data quality
- **Token Optimization** - Compact response formats designed for LLM efficiency  
- **Safety Controls** - SQL validation, query limits, and read-only operations
- **Flexible Configuration** - YAML-based project and dataset access control

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK with BigQuery access
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bigquery-mcp.git
cd bigquery-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure authentication:
```bash
# Option 1: Application Default Credentials (recommended)
gcloud auth application-default login

# Option 2: Service Account (for production)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

4. Set up configuration:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your project details
```

5. Run the server:
```bash
python src/server.py
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the Docker image directly
docker build -t bigquery-mcp .
docker run -it bigquery-mcp
```

## Configuration

### config.yaml

```yaml
bigquery:
  billing_project: "your-billing-project"
  
projects:
  - project_id: "analytics-prod"
    project_name: "Analytics Production"
    description: "Main data warehouse"
    datasets: ["prod_*", "reporting_*"]
    
  - project_id: "raw-data"
    project_name: "Raw Data Lake" 
    datasets: ["*"]  # Allow all datasets

limits:
  default_row_limit: 20
  max_query_timeout: 60

security:
  banned_sql_keywords: ["CREATE", "DROP", "DELETE", "UPDATE"]
```

### Environment Variables

```bash
# Optional overrides
COMPACT_FORMAT=true              # Enable compact responses
BIGQUERY_BILLING_PROJECT=my-project
LOG_LEVEL=DEBUG
```

## MCP Tools

### Discovery Tools

#### list_projects()
List all configured BigQuery projects with metadata.

```python
# Returns accessible projects
{
  "projects": [
    {
      "project_id": "analytics-prod",
      "project_name": "Analytics Production",
      "description": "Main data warehouse"
    }
  ]
}
```

#### list_datasets(project)
List datasets in a project, filtered by configuration patterns.

```python
# List datasets in default billing project
list_datasets()

# List datasets in specific project
list_datasets(project="analytics-prod")
```

#### list_tables(dataset_path, table_type)
List tables with filtering by type.

```python
# List all tables in dataset
list_tables("my_dataset")

# List only views
list_tables("project.dataset", table_type="view")
```

### Analysis Tools

#### analyze_table(table_path)
Get comprehensive table information including schema and metadata.

```python
# Analyze table with full path
analyze_table("project.dataset.table")

# Using default project
analyze_table("dataset.table")
```

#### analyze_columns(table_path, analysis_type, columns)
Perform column-level analysis for data quality insights.

```python
# Analyze nulls and cardinality for all columns
analyze_columns("dataset.table")

# Analyze only null counts for specific columns
analyze_columns(
    "dataset.table",
    analysis_type=["nulls"],
    columns=["user_id", "created_at"]
)
```

### Query Execution

#### execute_query(sql, project, limit, format)
Execute SQL queries with safety validation.

```python
# Simple query
execute_query("SELECT * FROM dataset.table")

# With options
execute_query(
    sql="SELECT user_id, COUNT(*) FROM dataset.events GROUP BY user_id",
    project="analytics-prod",
    limit=100,
    format="csv"
)
```

## Claude Desktop Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "python",
      "args": ["/path/to/bigquery-mcp/src/server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json"
      }
    }
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_discovery.py

# Test server functionality locally
python tests/test_server_local.py
```

### Project Structure

- `src/` - Core server implementation
  - `tools/` - MCP tool implementations
  - `utils/` - Shared utilities
- `tests/` - Test suite with fixtures
  - `unit/` - Unit tests with mocked dependencies
  - `integration/` - Integration tests with BigQuery
- `config/` - Configuration files

## Security

- **Read-Only** - All data modification operations are blocked
- **Project Allowlist** - Only configured projects are accessible
- **Dataset Patterns** - Fine-grained dataset access control
- **Query Validation** - SQL queries are validated for banned operations
- **Row Limits** - Default 20-row limit, configurable maximum

## Troubleshooting

### Authentication Issues

```bash
# Verify credentials
gcloud auth application-default print-access-token

# Check BigQuery permissions
bq ls --project_id=your-project
```

### Connection Errors

1. Verify project IDs in config.yaml
2. Check dataset patterns match actual dataset names
3. Ensure billing project has BigQuery API enabled

### Query Failures

- Check for forbidden SQL keywords (CREATE, DROP, etc.)
- Verify table paths use correct format
- Ensure you have permissions for the target dataset

## Support

- Documentation: [GitHub Wiki](https://github.com/yourusername/bigquery-mcp/wiki)
- Issues: [GitHub Issues](https://github.com/yourusername/bigquery-mcp/issues)
