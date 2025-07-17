# BigQuery MCP Server

Production-ready Model Context Protocol server for secure BigQuery access across multiple Google Cloud projects.

## Features

- **Multi-Project Access** - Query across BigQuery projects with pattern matching
- **Advanced Analytics** - Column analysis, data quality checks, schema exploration
- **Security Controls** - SQL validation, query limits, read-only operations
- **CLI-First Configuration** - Command-line arguments with config file fallback
- **Docker Ready** - Containerized deployment for easy integration

## Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud SDK
- Docker (optional)

### Setup

1. **Clone and install:**
   ```bash
   git clone https://github.com/aicayzer/bigquery-mcp.git
   cd bigquery-mcp
   pip install -r requirements.txt
   ```

2. **Authenticate:**
   ```bash
   gcloud auth application-default login
   ```

3. **Run:**
   ```bash
   # CLI (recommended)
   python src/server.py --project "your-project:*" --billing-project "your-project"
   
   # Docker
   docker build -t bigquery-mcp .
   docker run -v ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro bigquery-mcp \
     python src/server.py --project "your-project:*" --billing-project "your-project"
   ```

## MCP Client Setup

### Claude Desktop
Add to `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/logs:/app/logs",
        "bigquery-mcp:latest",
        "python", "src/server.py",
        "--project", "your-project:*",
        "--billing-project", "your-project"
      ]
    }
  }
}
```

### Cursor IDE
Add to MCP settings:
```json
{
  "bigquery": {
    "command": "docker",
    "args": [
      "run", "--rm", "-i",
      "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
      "bigquery-mcp:latest",
      "python", "src/server.py",
      "--project", "your-project:*",
      "--billing-project", "your-project"
    ]
  }
}
```

## Tools

- **`list_projects()`** - List configured BigQuery projects
- **`list_datasets(project)`** - List datasets in a project  
- **`list_tables(dataset, table_type)`** - List tables in a dataset
- **`analyze_table(table)`** - Get table structure and statistics
- **`analyze_columns(table, columns, sample_size)`** - Deep column analysis
- **`execute_query(query, format, limit, timeout)`** - Execute SELECT queries

## Configuration

### CLI Arguments
```bash
python src/server.py \
  --project "analytics-prod:user_*,session_*" \
  --project "logs-prod:application_*" \
  --billing-project "my-billing-project" \
  --log-level INFO \
  --timeout 300 \
  --max-limit 50000
```

### Config File (Optional)
```yaml
# config/config.yaml
bigquery:
  billing_project: "your-project"
  location: "US"

projects:
  - project_id: "analytics-prod"
    datasets: ["user_*", "session_*"]
  - project_id: "logs-prod"  
    datasets: ["application_*"]

limits:
  max_limit: 10000
  max_query_timeout: 60
```

## Documentation

- **[Setup Guide](docs/setup.md)** - Detailed installation and configuration
- **[AI Setup Assistant](docs/ai-setup.md)** - ChatGPT-powered configuration helper
- **[Tools Reference](docs/tools.md)** - Complete API documentation
- **[Configuration](docs/configuration.md)** - All configuration options

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
ruff format

# Build docs
mkdocs serve
```

## License

MIT License - see [LICENSE](LICENSE) file.
