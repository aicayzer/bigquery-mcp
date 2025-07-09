# Configuration Guide

This guide covers all configuration options for the BigQuery MCP Server.

## Configuration File Structure

The server uses a YAML configuration file located at `config/config.yaml`. Copy from the example:

```bash
cp config/config.yaml.example config/config.yaml
```

## Complete Configuration Reference

### Server Section

```yaml
server:
  name: "BigQuery MCP Server"
  version: "1.0.0"
```

- **`name`**: Display name for the server (used in logs and responses)
- **`version`**: Server version (should match the installed version)

### BigQuery Section

```yaml
bigquery:
  billing_project: "your-billing-project"
  location: "US"
  service_account_path: ""
```

- **`billing_project`**: Project ID used for billing BigQuery queries (required)
- **`location`**: BigQuery location/region (default: "US")
  - Common values: "US", "EU", "asia-northeast1"
- **`service_account_path`**: Path to service account JSON file (optional)
  - If not provided, uses Application Default Credentials

### Projects Section

Define which BigQuery projects and datasets the server can access:

```yaml
projects:
  - project_id: "analytics-prod"
    project_name: "Analytics Production"
    description: "Main analytics data warehouse"
    datasets: ["prod_*", "reporting_*"]

  - project_id: "raw-data-lake"
    project_name: "Raw Data Lake"
    description: "Raw data ingestion layer"
    datasets: ["*"]  # Allow all datasets

  - project_id: "ml-features"
    project_name: "ML Feature Store"
    description: "Machine learning features and training data"
    datasets: ["features_*", "training_*", "models_*"]
```

**Dataset Patterns:**
- `"*"` - Allow all datasets in the project
- `"dataset_name"` - Allow specific dataset
- `"prefix_*"` - Allow datasets starting with prefix
- `["dataset1", "dataset2"]` - Allow multiple specific datasets

### Limits Section

Control query execution and resource usage:

```yaml
limits:
  default_row_limit: 20
  max_row_limit: 10000
  max_query_timeout: 60
  max_bytes_processed: 1073741824  # 1GB
```

- **`default_row_limit`**: Default number of rows returned (if not specified in query)
- **`max_row_limit`**: Maximum rows that can be requested in a single query
- **`max_query_timeout`**: Maximum query execution time in seconds
- **`max_bytes_processed`**: Maximum bytes processed per query (for cost control)

### Security Section

SQL safety and validation settings:

```yaml
security:
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
    - "CALL"
    - "EXECUTE"
    - "SCRIPT"
  require_explicit_limits: false
  select_only: true
```

- **`banned_sql_keywords`**: SQL keywords that will cause query rejection
- **`require_explicit_limits`**: If true, all SELECT queries must include LIMIT clause
- **`select_only`**: If true, only SELECT statements and CTEs (WITH clauses) are allowed (recommended)

### Formatting Section

Response formatting options:

```yaml
formatting:
  compact_mode: false
  include_schema_descriptions: true
  abbreviate_common_terms: false
```

- **`compact_mode`**: Use compact response format (reduces token usage)
- **`include_schema_descriptions`**: Include field descriptions in schema responses
- **`abbreviate_common_terms`**: Shorten common BigQuery terms in responses

### Logging Section

Logging and audit configuration:

```yaml
logging:
  log_queries: true
  log_results: false
  max_query_log_length: 1000
```

- **`log_queries`**: Log SQL queries for audit purposes
- **`log_results`**: Log query results (be careful with sensitive data)
- **`max_query_log_length`**: Maximum length of logged SQL queries

## Environment Variables

Environment variables override YAML configuration values:

### Core Settings

```bash
# BigQuery configuration
export BIGQUERY_BILLING_PROJECT=your-billing-project
export BIGQUERY_LOCATION=US
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Server behavior
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
export COMPACT_FORMAT=true  # Override formatting.compact_mode
```

### Available Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BIGQUERY_BILLING_PROJECT` | Override billing project | From config |
| `BIGQUERY_LOCATION` | Override BigQuery location | From config |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Auto-detect |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `COMPACT_FORMAT` | Enable compact mode | From config |

## Configuration Examples

### Development Setup

For local development with personal projects:

```yaml
server:
  name: "BigQuery MCP Development"
  version: "1.0.0"

bigquery:
  billing_project: "my-dev-project"
  location: "US"

projects:
  - project_id: "my-dev-project"
    project_name: "Development Project"
    description: "Personal development data"
    datasets: ["*"]

limits:
  default_row_limit: 10
  max_row_limit: 1000
  max_query_timeout: 30
  max_bytes_processed: 104857600  # 100MB

formatting:
  compact_mode: true

logging:
  log_queries: true
  log_results: true  # OK for development
```

### Production Setup

For production deployments with multiple projects:

```yaml
server:
  name: "BigQuery MCP Production"
  version: "1.0.0"

bigquery:
  billing_project: "analytics-billing"
  location: "US"
  service_account_path: "/app/credentials/service-account.json"

projects:
  - project_id: "data-warehouse"
    project_name: "Data Warehouse"
    description: "Production data warehouse"
    datasets: ["prod_*", "reporting_*"]

  - project_id: "analytics-sandbox"
    project_name: "Analytics Sandbox"
    description: "Analytics team sandbox"
    datasets: ["sandbox_*", "experiments_*"]

limits:
  default_row_limit: 100
  max_row_limit: 10000
  max_query_timeout: 300  # 5 minutes
  max_bytes_processed: 10737418240  # 10GB

security:
  banned_sql_keywords:
    - "CREATE"
    - "DELETE"
    - "DROP"
    - "INSERT"
    - "UPDATE"
    - "TRUNCATE"
  require_explicit_limits: true
  select_only: true

formatting:
  compact_mode: true
  include_schema_descriptions: false

logging:
  log_queries: true
  log_results: false  # Don't log results in production
  max_query_log_length: 500
```

### Multi-Region Setup

For organizations with data in multiple regions:

```yaml
bigquery:
  billing_project: "global-analytics"
  location: "US"  # Default location

projects:
  - project_id: "us-data-warehouse"
    project_name: "US Data Warehouse"
    description: "US region data"
    datasets: ["us_*"]

  - project_id: "eu-data-warehouse"
    project_name: "EU Data Warehouse"
    description: "EU region data"
    datasets: ["eu_*"]

  - project_id: "asia-data-warehouse"
    project_name: "Asia Data Warehouse"
    description: "Asia region data"
    datasets: ["asia_*"]
```

## Docker Configuration

### Environment File

Create a `.env` file for Docker deployments:

```bash
# .env file
BIGQUERY_BILLING_PROJECT=your-billing-project
BIGQUERY_LOCATION=US
LOG_LEVEL=INFO
COMPACT_FORMAT=true
```

### Docker Compose

Use environment variables in `docker-compose.yml`:

```yaml
services:
  bigquery-mcp:
    build: .
    environment:
      - BIGQUERY_BILLING_PROJECT=${BIGQUERY_BILLING_PROJECT}
      - BIGQUERY_LOCATION=${BIGQUERY_LOCATION:-US}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - COMPACT_FORMAT=${COMPACT_FORMAT:-true}
    volumes:
      - ./config:/app/config:ro
      - ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro
```

## Validation

### Configuration Validation

The server validates configuration on startup:

- Required fields must be present
- Project IDs must be valid
- Numeric limits must be positive
- Dataset patterns must be valid

### Testing Configuration

Test your configuration:

```bash
# Test configuration loading
python -c "from src.config import load_config; print('Config OK')"

# Test BigQuery access
python -c "from src.client import BigQueryClient; client = BigQueryClient('config/config.yaml'); print('BigQuery OK')"
```

## Troubleshooting

### Common Configuration Issues

#### Invalid Project Access
```
Error: Project 'project-id' not found or access denied
```
**Solution:** Check project ID spelling and IAM permissions

#### Dataset Pattern Errors
```
Error: No datasets match pattern 'invalid_*'
```
**Solution:** Verify dataset names and patterns in your BigQuery project

#### Resource Limit Errors
```
Error: Query exceeded maximum bytes processed
```
**Solution:** Increase `max_bytes_processed` or optimize your query

### Configuration Best Practices

1. **Use environment variables** for sensitive values (project IDs, paths)
2. **Set appropriate limits** based on your use case and costs
3. **Use specific dataset patterns** rather than `"*"` where possible
4. **Enable query logging** for audit purposes
5. **Disable result logging** in production for security
6. **Test configuration changes** in development first

## Next Steps

- [Tools Reference](tools.md) - Learn about available MCP tools
- [Development Guide](development.md) - Set up development environment
- [Installation Guide](installation.md) - Deployment options