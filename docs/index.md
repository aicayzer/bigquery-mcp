# BigQuery MCP Server

A production-ready Model Context Protocol server that provides secure, cross-project access to BigQuery datasets. Built with FastMCP for Python, enabling LLMs to explore data, analyze schemas, and execute queries across multiple Google Cloud projects.

## Key Features

- **Cross-Project Access** - Query data across multiple BigQuery projects with a single connection
- **Advanced Analytics** - Column-level analysis for nulls, cardinality, and data quality
- **Safety Controls** - SQL validation, query limits, and read-only operations
- **Token Optimization** - Compact response formats designed for LLM efficiency
- **Flexible Configuration** - YAML-based project and dataset access control
- **Docker Support** - Containerized deployment for easy integration

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK with BigQuery access
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bigquery-mcp.git
   cd bigquery-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure authentication:**
   ```bash
   # Option 1: Application Default Credentials (recommended)
   gcloud auth application-default login

   # Option 2: Service Account (for production)
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

4. **Set up configuration:**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your project details
   ```

5. **Run the server:**
   ```bash
   python src/server.py
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Available Tools

The server provides 6 core tools for BigQuery interaction:

### Discovery Tools
- **`list_projects()`** - List configured BigQuery projects
- **`list_datasets(project)`** - List datasets in a project
- **`list_tables(dataset, table_type)`** - List tables in a dataset

### Analysis Tools
- **`analyze_table(table)`** - Get table structure and statistics
- **`analyze_columns(table, columns, include_examples, sample_size)`** - Deep column analysis

### Query Execution
- **`execute_query(query, format, max_rows, timeout, dry_run, parameters)`** - Execute SELECT queries

## Integration Examples

### Claude Desktop

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

### Cursor IDE with Docker

For detailed setup instructions with Cursor IDE using Docker, see the [Cursor MCP Setup Guide](cursor-mcp-setup.md).

## Security & Safety

- **Read-only operations** - Only SELECT queries are allowed
- **SQL validation** - Configurable banned keywords and safety checks
- **Query limits** - Row limits, timeouts, and byte processing limits
- **Project isolation** - Access control via YAML configuration
- **No credentials in code** - Uses Google Cloud authentication

## Next Steps

- [Installation Guide](installation.md) - Detailed installation and setup
- [Tools Reference](tools.md) - Complete tool documentation with examples
- [Configuration Guide](configuration.md) - YAML configuration and environment variables
- [Development Guide](development.md) - Contributing and development setup