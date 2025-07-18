# BigQuery MCP Server v1.1.1 - Complete Setup Guide

## Overview

The BigQuery MCP Server now uses a **CLI-first architecture** with comprehensive configuration options. This guide covers both Docker and non-Docker setups for simple and enterprise use cases.

**Configuration Precedence**: CLI Arguments > Config File > Environment Variables > Defaults

## Quick Setup (Docker - Recommended)

### Step 1: Authenticate with Google Cloud
```bash
# This gives you access to everything your account can access
gcloud auth application-default login
```

### Step 2: Build the Docker Image
```bash
# Clone the repository if you haven't already
git clone https://github.com/aicayzer/bigquery-mcp.git
cd bigquery-mcp

# Build the image
docker build -t bigquery-mcp:latest .
```

### Step 3: Test the Server
```bash
# Simple test with one project
docker run --rm -i \
  --volume ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
  --volume ./logs:/app/logs \
  bigquery-mcp:latest \
  python src/server.py \
  --project "YOUR_PROJECT_ID:*" \
  --billing-project "YOUR_PROJECT_ID"
```

## Claude Desktop Configuration

### Option 1: Simple Setup (Single Project)
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
        "--project", "your-project-id:*",
        "--billing-project", "your-project-id",
        "--log-level", "INFO",
        "--compact-format", "true"
      ]
    }
  }
}
```

### Option 2: Enterprise Setup (Multiple Projects)
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
        "--project", "analytics-prod:user_*,session_*",
        "--project", "logs-prod:application_*,system_*",
        "--project", "ml-dev:training_*,models_*",
        "--billing-project", "my-billing-project",
        "--log-level", "INFO",
        "--compact-format", "true",
        "--timeout", "300",
        "--max-limit", "50000"
      ]
    }
  }
}
```

### Option 3: Config File Approach
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/logs:/app/logs",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/config:/app/config:ro",
        "bigquery-mcp:latest",
        "python", "src/server.py",
        "--config", "/app/config/config.yaml"
      ]
    }
  }
}
```

## Non-Docker Setup (Advanced)

### Prerequisites
- Python 3.11+
- Google Cloud SDK
- Virtual environment (recommended)

### Step 1: Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Authenticate
```bash
# Set up authentication
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account.json"  # Optional
```

### Step 3: Claude Desktop Configuration
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "python",
      "args": [
        "/ABSOLUTE/PATH/TO/bigquery-mcp/src/server.py",
        "--project", "your-project:*",
        "--billing-project", "your-project"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json"
      }
    }
  }
}
```

## CLI Arguments Reference

### Core Arguments
- `--project` - Project patterns (can be repeated). Format: `project_id:dataset_pattern[:table_pattern]`
- `--billing-project` - BigQuery billing project
- `--config` - Path to configuration file (fallback if no projects specified)

### Logging Options
- `--log-level` - Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO
- `--log-queries` - Log queries for audit (true/false). Default: true
- `--log-results` - Log query results (true/false). Default: false

### Performance & Limits
- `--timeout` - Query timeout in seconds. Default: 60
- `--max-limit` - Maximum rows that can be requested. Default: 10000
- `--max-bytes-processed` - Maximum bytes processed (cost control). Default: 1073741824 (1GB)

### Security Options
- `--select-only` - Allow only SELECT statements (true/false). Default: true
- `--require-explicit-limits` - Require explicit LIMIT clause (true/false). Default: false
- `--banned-keywords` - Comma-separated banned SQL keywords. Default: CREATE,DELETE,DROP,TRUNCATE,ALTER,INSERT,UPDATE

### Formatting
- `--compact-format` - Use compact response format (true/false). Default: false

## Pattern Examples

### Simple Patterns
```bash
# All datasets in a project
--project "my-project:*"

# Specific dataset patterns
--project "my-project:analytics_*,logs_*"

# Multiple projects
--project "project1:*" --project "project2:staging_*"
```

### Enterprise Patterns
```bash
# Complex multi-project setup
--project "analytics-prod:user_*,session_*,conversion_*" \
--project "logs-prod:application_*,system_*,error_*" \
--project "ml-dev:training_*,features_*,models_*" \
--project "warehouse:daily_*,weekly_*,monthly_*"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: Permission denied
```
**Solution**: 
- Run `gcloud auth application-default login`
- Verify your service account has BigQuery permissions
- Check that billing is enabled on your project

#### 2. Table Not Found
```
Error: Table "table_name" must be qualified with a dataset
```
**Solution**: 
- Use fully qualified table names: `project.dataset.table`
- Verify the table exists in BigQuery console
- Check your dataset patterns include the target dataset

#### 3. Docker Volume Issues
```
Error: No such file or directory
```
**Solution**:
- Use absolute paths in volume mounts
- Ensure the gcloud config directory exists: `~/.config/gcloud`
- Create logs directory: `mkdir -p logs`

#### 4. Configuration Precedence Issues
```
Error: CLI arguments not taking effect
```
**Solution**:
- Remember: CLI > Config File > Environment > Defaults
- Use `--log-level DEBUG` to see configuration source
- Check for typos in argument names

### Debug Mode
```bash
# Enable debug logging to see configuration details
--log-level DEBUG --log-queries true
```

### Verify Setup
```bash
# Test with a simple query
docker run --rm -i \
  --volume ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
  bigquery-mcp:latest \
  python src/server.py \
  --project "your-project:*" \
  --billing-project "your-project" \
  --log-level DEBUG
```

## 📚 Additional Resources

- [Configuration Documentation](configuration.md)
- [Tool Reference](tools.md)
- Docker setup instructions are included above
- [GitHub Repository](https://github.com/aicayzer/bigquery-mcp)

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: `tail -f logs/bigquery_mcp.log`
2. **Enable debug mode**: `--log-level DEBUG`
3. **Verify authentication**: `gcloud auth list`
4. **Test BigQuery access**: `bq ls` (should list your projects)
5. **Check Claude Desktop logs**: Look for MCP connection errors

For additional support, please open an issue on the GitHub repository with:
- Your configuration (with sensitive data removed)
- Error messages from logs
- Steps to reproduce the issue 