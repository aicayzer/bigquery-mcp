# BigQuery MCP Server

MCP server for secure BigQuery access across multiple Google Cloud projects.

## Features

- **Multi-Project Access** - Query across BigQuery projects with pattern matching
- **Advanced Analytics** - Column analysis, data quality checks, schema exploration
- **Security Controls** - SQL validation, query limits, read-only operations
- **CLI Configuration** - Command-line arguments with config file fallback
- **Docker Support** - Containerized deployment for easy integration

## Documentation

Full documentation available at [aicayzer.github.io/bigquery-mcp](https://aicayzer.github.io/bigquery-mcp/)

## Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud SDK
- Docker (optional)

### Authentication
```bash
gcloud auth application-default login
```

### Installation
```bash
git clone https://github.com/aicayzer/bigquery-mcp.git
cd bigquery-mcp
pip install -r requirements.txt
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

## Usage

### CLI
```bash
# Single project
python src/server.py --project "your-project:*" --billing-project "your-project"

# Multiple projects with patterns
python src/server.py \
  --project "analytics-prod:user_*,session_*" \
  --project "logs-prod:application_*" \
  --billing-project "my-billing-project"
```

### Docker
```bash
docker build -t bigquery-mcp .
docker run -v ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro bigquery-mcp \
  python src/server.py --project "your-project:*" --billing-project "your-project"
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
  --timeout 20 \
  --max-limit 50000
```

### Config File (Optional)
```yaml
bigquery:
  billing_project: "your-project"
  location: "EU"

projects:
  - project_id: "analytics-prod"
    datasets: ["user_*", "session_*"]
  - project_id: "logs-prod"  
    datasets: ["application_*"]
```

## Contributing

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes with tests
4. Submit a pull request to `develop`

## License

MIT License - see [LICENSE](LICENSE) file.