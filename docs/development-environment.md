# Development Environment Setup

This guide explains how to set up a development instance of the BigQuery MCP Server alongside your production instance.

## Overview

The development environment provides:

- **Separate MCP Server**: Independent development server with its own configuration
- **Debug Logging**: Enhanced logging for development and debugging
- **Independent Configuration**: Separate config file for development projects/settings
- **Docker Isolation**: Runs in its own container alongside production
- **Easy Testing**: Test latest changes without affecting production setup

## Quick Setup

1. **Run the setup script:**
   ```bash
   ./setup-dev.sh
   ```

2. **Configure your development settings:**
   ```bash
   cp config/config.dev.yaml.example config/config.dev.yaml
   # Edit config/config.dev.yaml with your development projects
   ```

3. **Start the development server:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

## Configuration

### Development Config (`config/config.dev.yaml`)

The development configuration is separate from production and includes:

```yaml
server:
  name: "BigQuery Development MCP"
  version: "1.1.0-dev"

bigquery:
  billing_project: "your-dev-billing-project"
  location: "US"

projects:
  - project_id: "your-dev-project"
    project_name: "Development Project"
    datasets: ["dev_*", "test_*", "staging_*"]

# More permissive limits for development
limits:
  max_rows: 1000
  max_query_timeout: 300
  max_bytes_processed: 10737418240  # 10GB

development:
  tools_enabled: true
  verbose_logging: true
  experimental_features: true
```

### Docker Configuration

The development server uses `docker-compose.dev.yml`:

- **Container Name**: `bigquery-mcp-dev-server`
- **Server Name**: "BigQuery Development MCP"
- **Debug Logging**: Enabled by default
- **Independent**: Runs alongside production without conflicts

## MCP Client Integration

### Claude Desktop

Add to your `.claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "exec", "-i", "bigquery-mcp-server",
        "python", "/app/src/server.py"
      ]
    },
    "bigquery-dev": {
      "command": "docker",
      "args": [
        "exec", "-i", "bigquery-mcp-dev-server",
        "python", "/app/src/server.py"
      ]
    }
  }
}
```

Now you have both:
- **bigquery**: Production server
- **bigquery-dev**: Development server

### Cursor IDE

For Cursor, you can add both servers to your MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "bigquery-prod": {
        "command": "docker",
        "args": ["exec", "-i", "bigquery-mcp-server", "python", "/app/src/server.py"]
      },
      "bigquery-dev": {
        "command": "docker",
        "args": ["exec", "-i", "bigquery-mcp-dev-server", "python", "/app/src/server.py"]
      }
    }
  }
}
```

## Development Workflow

### 1. Making Changes

1. Make your code changes in the repository
2. Rebuild the development image:
   ```bash
   docker-compose -f docker-compose.dev.yml build
   ```
3. Restart the development server:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   docker-compose -f docker-compose.dev.yml up -d
   ```

### 2. Testing

Test your changes using the development MCP server in your client:

- Use the `bigquery-dev` server for testing
- Keep the `bigquery` server for stable operations
- Check logs for debugging:
  ```bash
  docker-compose -f docker-compose.dev.yml logs -f
  ```

### 3. Promoting Changes

Once you're satisfied with development testing:

1. Run tests:
   ```bash
   python -m pytest tests/ -v
   ```
2. Update version numbers if needed
3. Rebuild production image:
   ```bash
   docker-compose build
   ```
4. Deploy to production

## Management Commands

### Start Development Server
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Stop Development Server
```bash
docker-compose -f docker-compose.dev.yml down
```

### View Logs
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

### Rebuild Development Image
```bash
docker-compose -f docker-compose.dev.yml build --no-cache
```

### Check Status
```bash
docker-compose -f docker-compose.dev.yml ps
```

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs
   ```

2. Verify configuration:
   ```bash
   # Check if config.dev.yaml exists and is valid
   python -c "import yaml; yaml.safe_load(open('config/config.dev.yaml'))"
   ```

3. Check Google Cloud authentication:
   ```bash
   gcloud auth application-default print-access-token
   ```

### MCP Client Can't Connect

1. Ensure container is running:
   ```bash
   docker ps | grep bigquery-mcp-dev
   ```

2. Test server directly:
   ```bash
   docker exec -it bigquery-mcp-dev-server python /app/src/server.py
   ```

### Configuration Issues

1. Validate YAML syntax:
   ```bash
   python -c "import yaml; print('Valid YAML') if yaml.safe_load(open('config/config.dev.yaml')) else print('Invalid YAML')"
   ```

2. Check environment variables:
   ```bash
   docker-compose -f docker-compose.dev.yml config
   ```

## Benefits

✅ **Safe Testing**: Test changes without affecting production
✅ **Debug Logging**: Enhanced logging for development
✅ **Independent Config**: Separate projects and settings
✅ **Easy Switching**: Switch between prod and dev in MCP clients
✅ **Isolation**: No conflicts between development and production
✅ **Version Control**: Track development vs production versions
