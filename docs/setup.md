# MCP Client Setup Guide

This guide shows how to configure the BigQuery MCP server to work with various MCP clients.

## Prerequisites

1. **Docker Desktop** - Ensure Docker is installed and running
2. **Google Cloud Authentication** - Set up using one of these methods:
   ```bash
   # Option 1: Application Default Credentials (recommended)
   gcloud auth application-default login

   # Option 2: Service Account JSON file
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```
3. **BigQuery Access** - Ensure your account has the necessary permissions

## Setup Steps

### Step 1: Build the Docker Image

```bash
cd /path/to/bigquery-mcp
docker-compose build
```

### Step 2: Test the Container

```bash
# Test that the container starts correctly
docker-compose run --rm bigquery-mcp
```

You should see the BigQuery MCP server start. Press Ctrl+C to stop.

### Step 3: Configure Your Client

## Claude Desktop

**Location**: Claude Desktop → Settings → Developer → Edit Config

```json
{
  "mcpServers": {
    "bigquery": {
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
        "bigquery-mcp:latest"
      ]
    }
  }
}
```

## Cursor IDE

**Location**: Cursor Settings → Extensions → MCP Servers → Edit Configuration

```json
{
  "mcpServers": {
    "bigquery": {
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
        "bigquery-mcp:latest"
      ]
    }
  }
}
```

## Alternative: Python Setup

If you prefer not to use Docker:

```json
{
  "mcpServers": {
    "bigquery": {
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

## Configuration Notes

**Important**: Update the paths in the configuration:
- Replace `/path/to/bigquery-mcp` with your actual project path
- Replace `/Users/your-username/.config/gcloud` with your gcloud config path
- Replace `your-billing-project` with your BigQuery billing project ID

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