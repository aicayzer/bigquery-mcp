# BigQuery MCP Server - Architecture & Specification

## Overview

The BigQuery MCP Server is a Model Context Protocol implementation that provides secure, read-only access to Google BigQuery datasets. It enables LLMs to explore data schemas, analyze table structures, and execute queries across multiple Google Cloud projects through a standardized interface.

## Core Principles

### Security First
- **Read-only operations** - All write operations (CREATE, DROP, DELETE, UPDATE, INSERT) are blocked at the SQL validation layer
- **Project allowlisting** - Only explicitly configured projects can be accessed
- **Dataset pattern matching** - Fine-grained control over which datasets are accessible within each project
- **Query limits** - Configurable row limits and timeouts prevent runaway queries
- **SQL injection prevention** - Parameterized queries and keyword validation

### LLM Optimization
- **Token efficiency** - Compact response mode reduces token usage by 60-70%
- **Structured responses** - Consistent JSON format across all tools
- **Progressive disclosure** - Summary information first, details on request
- **Error clarity** - Actionable error messages guide users to solutions

### Cross-Project Support
- **Unified interface** - Single connection to query multiple projects
- **Billing project separation** - Queries can run in different projects than the billing project
- **Project metadata** - Human-friendly names and descriptions for each project

## Architecture

### Component Structure

```
BigQuery MCP Server
├── FastMCP Framework (Protocol Layer)
├── Tool Modules
│   ├── Discovery Tools (list_projects, list_datasets, list_tables)
│   ├── Analysis Tools (analyze_table, analyze_columns)
│   └── Execution Tools (execute_query)
├── Core Services
│   ├── BigQuery Client (Connection management)
│   ├── Configuration (YAML + environment variables)
│   ├── SQL Validator (Security enforcement)
│   └── Response Formatter (Standard/Compact modes)
└── Error Handling (Custom exception hierarchy)
```

### Tool Registration Pattern

Tools follow a dependency injection pattern where the server initializes core services and injects them into tool modules:

1. Server starts and loads configuration
2. BigQuery client initialized with credentials
3. Tool modules receive dependencies via registration functions
4. FastMCP decorators expose tools to the MCP protocol

This design ensures tools cannot be called without proper initialization, enforcing security boundaries.

### Data Flow

1. **Request** → FastMCP receives MCP protocol request
2. **Validation** → Parameters validated and security checks applied
3. **Execution** → BigQuery API calls with appropriate project/dataset context
4. **Formatting** → Results formatted based on compact mode setting
5. **Response** → Structured JSON returned via MCP protocol

## Configuration

### YAML Structure

```yaml
server:
  name: "BigQuery MCP Server"
  version: "1.0.0"

bigquery:
  billing_project: "my-billing-project"
  location: "EU"  # BigQuery dataset location

projects:
  - project_id: "analytics-prod"
    project_name: "Analytics Production"
    description: "Main data warehouse"
    datasets: ["prod_*", "reporting_*"]  # Patterns

limits:
  default_row_limit: 20
  max_row_limit: 10000
  max_query_timeout: 60  # seconds
  max_bytes_processed: 1073741824  # 1GB

security:
  banned_sql_keywords: ["CREATE", "DROP", "DELETE", "UPDATE", "INSERT"]
  require_explicit_limits: false

formatting:
  compact_mode: false
  max_query_log_length: 500
```

### Environment Variables

Environment variables override YAML configuration:
- `BIGQUERY_BILLING_PROJECT` - Override billing project
- `BIGQUERY_LOCATION` - Override location
- `COMPACT_FORMAT` - Enable compact mode
- `LOG_LEVEL` - Set logging verbosity
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON

## Error Handling

### Exception Hierarchy

```
BigQueryMCPError (Base)
├── ConfigurationError (Invalid configuration)
├── AuthenticationError (Credential issues)
├── ProjectAccessError (Project not allowed)
├── DatasetAccessError (Dataset pattern mismatch)
├── TableNotFoundError (Table doesn't exist)
├── SQLValidationError (Forbidden SQL operations)
├── SecurityError (Security policy violations)
└── QueryExecutionError (Runtime query failures)
    └── QueryTimeoutError (Query exceeded timeout)
```

### Error Response Format

```json
{
  "status": "error",
  "error": "Clear description of what went wrong",
  "error_type": "ProjectAccessError",
  "suggestion": "Use list_projects() to see available projects"
}
```

## Security Model

### Access Control Layers

1. **Authentication** - Google Cloud credentials (ADC or service account)
2. **Project Authorization** - Allowlist in configuration
3. **Dataset Authorization** - Pattern matching per project
4. **Query Validation** - SQL keyword blocking and syntax validation
5. **Resource Limits** - Row limits, timeouts, and byte limits

### SQL Validation

The SQL validator ensures:
- Only SELECT statements allowed (WITH clauses permitted for CTEs)
- No banned keywords in queries
- Optional LIMIT enforcement
- Protection against comment-based injection

## Performance Considerations

### Query Optimization

- **Automatic LIMIT injection** - Adds LIMIT if not present
- **Sampling for analysis** - Uses RAND() sampling instead of full table scans
- **Metadata caching** - BigQuery client caches schema information
- **Query result caching** - BigQuery automatically caches identical queries

### Response Optimization

Compact mode reduces response size by:
- Omitting null/empty fields
- Simplifying nested structures
- Abbreviating field names
- Removing redundant metadata

## Limitations

### By Design
- Read-only access (no data modification)
- No table/dataset creation
- No access to query logs of other users
- No access to cost information
- No streaming inserts

### Technical
- Maximum 10,000 rows per query (configurable)
- 60-second query timeout (configurable)
- Subject to BigQuery API quotas
- Requires appropriate IAM permissions

## Future Considerations

The architecture supports potential future enhancements:
- Query result caching layer
- Query cost estimation
- Scheduled query support
- Metadata search capabilities
- Integration with other Google Cloud services

These would be implemented as new tool modules following the same registration pattern.
