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
# Build the Docker image
docker build -t bigquery-mcp .

# Test the container
docker run --rm bigquery-mcp python --version

# For development with volume mounts
docker-compose up --build
```

#### Claude MCP Configuration (Docker)

After building the Docker image, add this to your Claude MCP configuration:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/your/bigquery-mcp/config:/app/config:ro",
        "-v", "/path/to/your/service-account.json:/app/credentials/service-account.json:ro",
        "-e", "GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json",
        "bigquery-mcp"
      ],
      "env": {}
    }
  }
}
```

Replace `/path/to/your/bigquery-mcp/config` with the absolute path to your config directory and `/path/to/your/service-account.json` with your GCP service account key file.

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

## Available Tools

### Discovery Tools
- **list_projects()** - List configured BigQuery projects
- **list_datasets(project)** - List datasets in a project
- **list_tables(dataset, table_type)** - List tables in a dataset

### Analysis Tools
- **analyze_table(table)** - Get table structure and statistics
- **analyze_columns(table, columns, include_examples, sample_size)** - Deep column analysis

### Query Execution
- **execute_query(query, format, max_rows, timeout, dry_run, parameters)** - Execute SELECT queries

For detailed documentation and examples, see [docs/tools.md](docs/tools.md).

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

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_discovery.py
```

## Development

For code quality checks and linting, see [Development Guide](docs/development.md).

## Documentation

- [Architecture & Specification](docs/architecture.md) - System design and security model
- [Tools Reference](docs/tools.md) - Detailed tool documentation with examples
- [Development Guide](docs/development.md) - Code quality, linting, and troubleshooting
- [Contributing Guidelines](CLAUDE.md) - Guidelines for contributors

## License

MIT License - see LICENSE file for details.
