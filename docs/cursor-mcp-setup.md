# Cursor MCP Setup Guide

This guide shows how to configure the BigQuery MCP server to work with Cursor IDE using Docker.

## Prerequisites

1. **Docker Desktop** - Ensure Docker is installed and running
2. **Google Cloud Authentication** - Set up using one of these methods:
   ```bash
   # Option 1: Application Default Credentials (recommended)
   gcloud auth application-default login

   # Option 2: Service Account JSON file
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

## Step 1: Build the Docker Image

```bash
cd /path/to/bigquery-mcp
docker-compose build
```

This creates the Docker image `bigquery-mcp-bigquery-mcp:latest`.

## Step 2: Test the Docker Container

```bash
# Test that the container starts correctly
docker-compose run --rm bigquery-mcp
```

You should see the BigQuery MCP server start with FastMCP 2.0 output. Press Ctrl+C to stop.

## Step 3: Configure Cursor

Add this configuration to your Cursor MCP settings:

**Location**: Cursor Settings → Extensions → MCP Servers → Edit Configuration

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
        "--volume", "/Users/august.cayzer/Documents/codebase/aic/bigquery-mcp/config:/app/config:ro",
        "--volume", "/Users/august.cayzer/Documents/codebase/aic/bigquery-mcp/logs:/app/logs",
        "--volume", "/Users/august.cayzer/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "bigquery-mcp-bigquery-mcp:latest"
      ]
    }
  }
}
```

**Important**: Update the paths in the configuration:
- Replace `/Users/august.cayzer/Documents/codebase/aic/bigquery-mcp` with your actual project path
- Replace `/Users/august.cayzer/.config/gcloud` with your gcloud config path
- Replace `your-billing-project` with your BigQuery billing project ID

## Step 4: Verify the Setup

1. **Restart Cursor** after adding the MCP configuration
2. **Test the connection** by trying these commands in Cursor:
   - List available projects
   - List datasets in your project
   - Execute a simple query like `SELECT COUNT(*) FROM your_dataset.your_table LIMIT 1`

## Troubleshooting

### Container Won't Start
- Check Docker is running: `docker info`
- Verify the image exists: `docker images | grep bigquery-mcp`
- Check logs: `docker-compose logs bigquery-mcp`

### Authentication Issues
- Verify gcloud auth: `gcloud auth list`
- Check credentials file exists: `ls -la ~/.config/gcloud/application_default_credentials.json`
- Ensure billing project is correct in config

### Path Issues
- Use absolute paths in the Docker volume mounts
- Ensure all paths exist and are readable
- Check file permissions on mounted directories

## Configuration Details

The Docker configuration:
- **`--rm`**: Removes container after use (clean up)
- **`-i`**: Interactive mode for MCP stdio communication
- **Volume mounts**:
  - `config/`: Read-only access to your BigQuery MCP configuration
  - `logs/`: Write access for server logs
  - `.config/gcloud/`: Read-only access to Google Cloud credentials
- **Environment variables**:
  - `BIGQUERY_BILLING_PROJECT`: Your default billing project
  - `LOG_LEVEL`: Set to INFO for normal operation, DEBUG for troubleshooting
  - `COMPACT_FORMAT`: Optimizes responses for LLM token usage

## Alternative: Local Python Setup

If you prefer not to use Docker, you can run the MCP server directly:

```json
{
  "mcpServers": {
    "bigquery-mcp": {
      "command": "python",
      "args": ["/path/to/bigquery-mcp/src/server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json",
        "BIGQUERY_BILLING_PROJECT": "your-project-id"
      }
    }
  }
}
```

However, the Docker approach is recommended as it provides better isolation and avoids Python environment conflicts.