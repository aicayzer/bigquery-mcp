# Claude Desktop Setup Guide

This guide shows how to configure the BigQuery MCP server to work with Claude Desktop, with options for both Docker and direct Python execution.

## Prerequisites

1. **Claude Desktop** - Download and install from [Claude.ai](https://claude.ai/download)
2. **Google Cloud Authentication** - Set up using one of these methods:
   ```bash
   # Option 1: Application Default Credentials (recommended for development)
   gcloud auth application-default login

   # Option 2: Service Account JSON file (recommended for production)
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```
3. **BigQuery Access** - Ensure your account has the necessary permissions

## Method 1: Docker Setup (Recommended)

Docker provides better isolation and avoids Python environment conflicts.

### Step 1: Build the Docker Image

```bash
cd /path/to/bigquery-mcp
docker-compose build
```

This creates the Docker image `bigquery-mcp-bigquery-mcp:latest`.

### Step 2: Test the Docker Container

```bash
# Test that the container starts correctly
docker-compose run --rm bigquery-mcp
```

You should see the BigQuery MCP server start. Press Ctrl+C to stop.

### Step 3: Configure Claude Desktop

**Location**: Claude Desktop → Settings → Developer → Edit Config

Add this configuration to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "bigquery-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env", "BIGQUERY_BILLING_PROJECT=your-billing-project",
        "--env", "LOG_LEVEL=INFO",
        "--env", "COMPACT_FORMAT=true",
        "--volume", "/path/to/bigquery-mcp/config:/app/config:ro",
        "--volume", "/path/to/bigquery-mcp/logs:/app/logs",
        "--volume", "/Users/your-username/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "bigquery-mcp-bigquery-mcp:latest"
      ]
    }
  }
}
```

**Important**: Update the paths in the configuration:
- Replace `/path/to/bigquery-mcp` with your actual project path
- Replace `/Users/your-username/.config/gcloud` with your gcloud config path (usually `~/.config/gcloud`)
- Replace `your-billing-project` with your BigQuery billing project ID

### Step 4: Configure Your BigQuery Projects

Edit `config/config.yaml` to specify which projects and datasets Claude can access:

```yaml
server:
  name: "BigQuery MCP Server"
  version: "1.0.0"

bigquery:
  billing_project: "your-billing-project"
  location: "US"  # or "EU", "asia-northeast1", etc.

projects:
  - project_id: "your-analytics-project"
    project_name: "Analytics Data"
    description: "Main analytics warehouse"
    datasets: ["analytics_*", "reporting"]  # Wildcard and specific patterns

  - project_id: "your-raw-project"
    project_name: "Raw Data"
    description: "Raw data ingestion"
    datasets: ["raw_*"]
```

## Method 2: Direct Python Setup

If you prefer not to use Docker, you can run the MCP server directly with Python.

### Step 1: Install Dependencies

```bash
cd /path/to/bigquery-mcp
pip install -r requirements.txt
```

### Step 2: Configure Claude Desktop

**Location**: Claude Desktop → Settings → Developer → Edit Config

```json
{
  "mcpServers": {
    "bigquery-mcp": {
      "command": "python",
      "args": ["/path/to/bigquery-mcp/src/server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json",
        "BIGQUERY_BILLING_PROJECT": "your-billing-project",
        "LOG_LEVEL": "INFO",
        "COMPACT_FORMAT": "true"
      }
    }
  }
}
```

**Important**: Update the paths:
- Replace `/path/to/bigquery-mcp` with your actual project path
- Replace `/path/to/credentials.json` with your service account key path (or omit if using ADC)
- Replace `your-billing-project` with your BigQuery billing project ID

### Step 3: Configure Your Projects

Same as Docker method - edit `config/config.yaml` with your project details.

## Verification

### Step 1: Restart Claude Desktop

After adding the MCP configuration, completely restart Claude Desktop for the changes to take effect.

### Step 2: Test the Connection

Start a new conversation in Claude Desktop and try these commands:

1. **List your projects:**
   ```
   Can you show me what BigQuery projects are available?
   ```

2. **Explore a dataset:**
   ```
   What datasets are in my analytics project?
   ```

3. **Analyze a table:**
   ```
   Can you analyze the structure of my_dataset.my_table?
   ```

4. **Execute a simple query:**
   ```
   Run this query: SELECT COUNT(*) as total_rows FROM my_dataset.my_table LIMIT 1
   ```

### Step 3: Verify Tools Are Available

Claude should have access to these BigQuery tools:
- `list_projects()` - List configured projects
- `list_datasets()` - List datasets in a project
- `list_tables()` - List tables in a dataset
- `analyze_table()` - Get table structure and statistics
- `analyze_columns()` - Deep column analysis with statistics
- `execute_query()` - Execute SELECT queries with safety controls

## Troubleshooting

### Claude Desktop Not Recognizing MCP Server

**Symptoms**: Claude doesn't show BigQuery capabilities or responds with "I don't have access to BigQuery"

**Solutions**:
1. Restart Claude Desktop completely (not just refresh)
2. Check the MCP configuration JSON syntax is valid
3. Verify all file paths in the configuration exist
4. Check Claude Desktop logs (if available)

### Authentication Issues

**Symptoms**: "Could not automatically determine credentials" or "403 Forbidden"

**Solutions**:
1. **For Docker setup**: Ensure gcloud config directory is properly mounted:
   ```bash
   ls -la ~/.config/gcloud/application_default_credentials.json
   ```
2. **For Python setup**: Verify authentication:
   ```bash
   gcloud auth list
   gcloud auth application-default print-access-token
   ```
3. **Service Account**: Ensure the JSON file exists and has proper permissions:
   ```bash
   ls -la /path/to/credentials.json
   ```

### Permission Denied Errors

**Symptoms**: "Access Denied" when accessing datasets or tables

**Solutions**:
1. Verify your account has BigQuery permissions:
   ```bash
   bq ls  # Should list your datasets
   ```
2. Check IAM roles - you need at minimum:
   - `roles/bigquery.user`
   - `roles/bigquery.dataViewer`
   - `roles/bigquery.jobUser`

### Docker Issues

**Symptoms**: Container won't start or permission errors

**Solutions**:
1. **Check Docker is running:**
   ```bash
   docker info
   ```
2. **Verify image exists:**
   ```bash
   docker images | grep bigquery-mcp
   ```
3. **Check volume mount permissions:**
   ```bash
   chmod -R 755 ~/.config/gcloud
   chmod -R 755 /path/to/bigquery-mcp/config
   ```

### Configuration Issues

**Symptoms**: Server starts but can't access specific projects/datasets

**Solutions**:
1. **Check config.yaml syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```
2. **Verify project IDs are correct:**
   ```bash
   gcloud projects list
   ```
3. **Test dataset access:**
   ```bash
   bq ls your-project:your-dataset
   ```

## Advanced Configuration

### Custom Logging

For debugging, you can increase log verbosity:

```json
{
  "mcpServers": {
    "bigquery-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env", "LOG_LEVEL=DEBUG",
        "..."
      ]
    }
  }
}
```

### Memory and Performance Tuning

For large datasets, you can adjust query limits:

```yaml
# In config/config.yaml
query:
  max_rows: 1000
  timeout_seconds: 30
  max_bytes_processed: 1073741824  # 1GB
```

### Multiple Project Access

You can configure access to multiple BigQuery projects:

```yaml
projects:
  - project_id: "production-analytics"
    project_name: "Production Analytics"
    description: "Production data warehouse"
    datasets: ["analytics", "reporting", "dashboards"]

  - project_id: "staging-analytics"
    project_name: "Staging Analytics"
    description: "Staging environment"
    datasets: ["staging_*"]

  - project_id: "raw-data-project"
    project_name: "Raw Data Lake"
    description: "Raw data ingestion"
    datasets: ["raw_*", "external_*"]
```

## Security Best Practices

1. **Use Service Accounts for Production**: Create dedicated service accounts with minimal required permissions
2. **Limit Dataset Access**: Only include datasets that Claude needs to access in your configuration
3. **Monitor Query Usage**: BigQuery provides audit logs for all queries executed
4. **Use Read-Only Permissions**: The MCP server only needs read access to BigQuery
5. **Keep Credentials Secure**: Never commit credentials to version control

## Getting Help

If you encounter issues:

1. **Check server logs**: Look in the `logs/` directory for detailed error messages
2. **Verify BigQuery access**: Test with `gcloud` and `bq` commands independently
3. **Review configuration**: Ensure your `config.yaml` matches the [configuration guide](configuration.md)
4. **Test Docker setup**: Run the container manually to see detailed error messages
5. **Community support**: Check the [GitHub discussions](https://github.com/aicayzer/bigquery-mcp/discussions)

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Tools Reference](tools.md) - Complete documentation of available BigQuery tools
- [Installation Guide](installation.md) - Alternative installation methods
- [Development Guide](development.md) - Contributing and development setup