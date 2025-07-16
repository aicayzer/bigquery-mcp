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
   git clone https://github.com/aicayzer/bigquery-mcp.git
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

4. **Run the server:**
   ```bash
   # Using command-line arguments (recommended)
   python src/server.py sandbox-dev:dev_* sandbox-main:main_*
   
   # Or using config file (deprecated)
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your project details
   python src/server.py
   ```

### Docker Deployment

```bash
# Using CLI arguments (recommended)
docker-compose up bigquery-mcp-cli --build

# Using config file (deprecated)
docker-compose up bigquery-mcp-config --build

# Custom project patterns
docker run -it --rm \
  -v ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
  -e BIGQUERY_BILLING_PROJECT=your-project \
  bigquery-mcp:latest \
  python src/server.py your-project:your_dataset_*
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
- **`execute_query(query, format, limit, timeout, dry_run, parameters)`** - Execute SELECT queries

## Integration Examples

### MCP Client Setup

For complete setup instructions with Claude Desktop, Cursor IDE, and other MCP clients, see the **[Client Setup Guide](docs/setup.md)**.

Quick Docker configuration example:
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env", "BIGQUERY_BILLING_PROJECT=your-project",
        "--volume", "~/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "bigquery-mcp:latest",
        "python", "src/server.py", "your-project:your_dataset_*"
      ]
    }
  }
}
```

## Documentation

📚 **Complete Documentation**

- **[Installation Guide](docs/installation.md)** - Detailed installation and setup
- **[Client Setup Guide](docs/setup.md)** - Claude Desktop, Cursor IDE, and other MCP clients
- **[Tools Reference](docs/tools.md)** - Complete tool documentation with examples
- **[Configuration Guide](docs/configuration.md)** - YAML configuration and environment variables

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Open http://localhost:8000 in your browser
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



### Code Quality

```bash
# Format code
ruff format src tests

# Check and fix linting issues
ruff check src tests --fix
```

For development, follow the installation guide and use the standard Python development workflow.

## Security & Safety

- **Read-only operations** - Only SELECT queries and CTEs (WITH clauses) are allowed
- **SQL validation** - Configurable banned keywords and safety checks
- **Query limits** - Row limits, timeouts, and byte processing limits
- **Project isolation** - Access control via YAML configuration
- **No credentials in code** - Uses Google Cloud authentication

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please follow these guidelines:

- Use `ruff format` and `ruff check --fix` before committing
- Add tests for new functionality with `pytest`
- Follow the existing code patterns and conventions
- Update documentation for any user-facing changes

## Support

- 📖 [Documentation](docs/index.md)
- 🐛 [Issue Tracker](https://github.com/aicayzer/bigquery-mcp/issues)
- 💬 [Discussions](https://github.com/aicayzer/bigquery-mcp/discussions)
