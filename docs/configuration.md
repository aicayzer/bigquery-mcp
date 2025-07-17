# Configuration Guide

This guide covers all configuration options for the BigQuery MCP Server v1.1.1 with CLI-first architecture.

## Command-Line Arguments (Primary Interface)

The preferred way to configure the server is using command-line arguments:

```bash
# Basic usage with new CLI-first format
python src/server.py --project "your-project-1:dev_*" --project "your-project-2:main_*" --billing-project "your-billing-project"

# Single project with all datasets
python src/server.py --project "your-project:*" --billing-project "your-project"

# Multiple patterns for same project
python src/server.py --project "your-project:demo_*,analytics_*" --billing-project "your-project"

# Enterprise usage with multiple projects and settings
python src/server.py \
  --project "analytics-prod:user_*,session_*" \
  --project "logs-prod:application_*,system_*" \
  --project "ml-dev:training_*,models_*" \
  --billing-project "my-billing-project" \
  --log-level "INFO" \
  --compact-format "true" \
  --timeout 300 \
  --max-limit 50000
```

## Complete CLI Arguments Reference

### Core Arguments
- **`--project`**: Project access patterns (can be repeated). Format: `project_id:dataset_pattern[:table_pattern]`
- **`--billing-project`**: BigQuery billing project (overrides environment variable)
- **`--config`**: Path to config file (fallback when no projects specified)
- **`--location`**: BigQuery location (default: EU)

### Logging Options
- **`--log-level`**: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO
- **`--log-queries`**: Log queries for audit purposes (true/false). Default: true
- **`--log-results`**: Log query results - be careful with sensitive data (true/false). Default: false

### Performance & Limits
- **`--timeout`**: Query timeout in seconds. Default: 60
- **`--max-limit`**: Maximum rows that can be requested. Default: 10000
- **`--max-bytes-processed`**: Maximum bytes processed for cost control. Default: 1073741824 (1GB)

### Security Options
- **`--select-only`**: Allow only SELECT statements (true/false). Default: true
- **`--require-explicit-limits`**: Require explicit LIMIT clause in SELECT queries (true/false). Default: false
- **`--banned-keywords`**: Comma-separated list of banned SQL keywords. Default: CREATE,DELETE,DROP,TRUNCATE,ALTER,INSERT,UPDATE

### Formatting
- **`--compact-format`**: Use compact response format (true/false). Default: false

## Configuration Precedence

**CLI Arguments > Config File > Environment Variables > Hardcoded Defaults**

This means CLI arguments always take precedence over config file settings, which take precedence over environment variables.

## Project Pattern Examples

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

### Table Patterns (Future Enhancement)
```bash
# Table patterns will be supported in future versions
--project "project:dataset:table_pattern"
```

## Configuration File (Fallback)

For backward compatibility and complex setups, the server still supports YAML configuration files:

```bash
# Use config file when no --project arguments provided
python src/server.py --config config/config.yaml
```

## Complete Configuration Reference

### Server Section

```yaml
server:
  name: "BigQuery MCP Server"
  version: "1.1.1"
```

### BigQuery Section

```yaml
bigquery:
  # Required: Project for billing
  billing_project: "your-billing-project"
  
  # Optional: BigQuery location/region
  location: "EU"
  
  # Optional: Service account path
  service_account_path: "/path/to/service-account.json"
```

### Projects Section

```yaml
projects:
  - project_id: "analytics-prod"
    project_name: "Analytics Production"
    description: "Main analytics data warehouse"
    datasets: ["prod_*", "reporting_*"]

  - project_id: "raw-data-lake"
    project_name: "Raw Data Lake"
    description: "Raw data ingestion layer"
    datasets: ["*"]  # All datasets
```

### Limits Section

```yaml
limits:
  # Default rows returned if not specified
  default_limit: 20
  
  # Maximum query execution time in seconds
  max_query_timeout: 60
  
  # Maximum rows that can be requested
  max_limit: 10000
  
  # Maximum bytes processed (cost control)
  max_bytes_processed: 1073741824  # 1GB
```

### Security Section

```yaml
security:
  # Banned SQL keywords
  banned_sql_keywords:
    - "CREATE"
    - "DELETE"
    - "DROP"
    - "TRUNCATE"
    - "INSERT"
    - "UPDATE"
    - "ALTER"
    - "GRANT"
    - "REVOKE"
    - "MERGE"
  
  # Allow only SELECT statements
  select_only: true
  
  # Require explicit LIMIT clause
  require_explicit_limits: false
```

### Formatting Section

```yaml
formatting:
  # Use compact format by default
  compact_format: false
```

### Logging Section

```yaml
logging:
  # Log queries for audit purposes
  log_queries: true
  
  # Log query results (be careful with sensitive data)
  log_results: false
```

## Environment Variables

The following environment variables are supported:

- **`BIGQUERY_BILLING_PROJECT`**: Default billing project
- **`GOOGLE_APPLICATION_CREDENTIALS`**: Path to service account JSON
- **`BIGQUERY_LOCATION`**: BigQuery location
- **`LOG_LEVEL`**: Logging level
- **`COMPACT_FORMAT`**: Use compact format (true/false)
- **`LOG_QUERIES`**: Log queries (true/false)
- **`LOG_RESULTS`**: Log results (true/false)

## Docker Configuration

### CLI-First Docker (Recommended)

```bash
docker run --rm -i \
  --volume ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
  --volume ./logs:/app/logs \
  bigquery-mcp:latest \
  python src/server.py \
  --project "your-project:*" \
  --billing-project "your-project" \
  --log-level "INFO"
```

### Docker Compose

```yaml
services:
  bigquery-mcp:
    build: .
    image: bigquery-mcp:latest
    container_name: bigquery-mcp
    command: [
      "python", "src/server.py",
      "--project", "your-project:*",
      "--billing-project", "your-project",
      "--log-level", "INFO"
    ]
    volumes:
      - ./logs:/app/logs
      - ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro
    stdin_open: true
    tty: false
```

## Migration from v1.1.0

If you're upgrading from v1.1.0:

1. **Update CLI usage**: Change from `python src/server.py project:pattern` to `python src/server.py --project "project:pattern"`
2. **Add new arguments**: Take advantage of new CLI options like `--log-level`, `--timeout`, etc.
3. **Update Docker configs**: Use new CLI-first Docker approach
4. **Check config files**: Ensure `log_results` attribute is present in config files

## Troubleshooting

### Common Issues

1. **Missing log_results attribute**: Update config files to include `log_results: false` in the logging section
2. **CLI argument parsing**: Ensure you're using `--project` flag instead of positional arguments
3. **Docker issues**: Use absolute paths for volume mounts and ensure gcloud auth is set up

### Debug Mode

```bash
# Enable debug logging
python src/server.py --project "your-project:*" --billing-project "your-project" --log-level DEBUG --log-queries true --log-results true
```

This will provide detailed information about configuration loading, query execution, and error handling.