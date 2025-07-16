# BigQuery MCP Tools Reference

This document provides detailed documentation for all available MCP tools in the BigQuery MCP Server.

## Parameter Types and Validation

All tools perform automatic parameter type conversion to ensure compatibility with MCP protocol:

- **Integers**: String values are automatically converted to integers (e.g., "100" → 100)
- **Booleans**: String values are converted to booleans (e.g., "true" → true)
- **Arrays**: JSON string arrays are parsed automatically
- **Optional Parameters**: Marked as optional in tool descriptions

## Context Management Tools

### get_current_context()

Get the current BigQuery context including billing project, last accessed resources, and allowed projects/datasets for better query planning.

**Parameters**: None

**Returns**: Dictionary with current context information

**Example Response**:
```json
{
  "success": true,
  "context": {
    "billing_project": "my-project",
    "allowed_projects": ["project1", "project2"],
    "allowed_datasets": ["dataset1", "dataset2"],
    "last_accessed": {
      "project": "project1",
      "dataset": "dataset1"
    },
    "location": "US"
  }
}
```

### list_accessible_projects()

List all projects accessible through the current configuration.

**Parameters**: None

**Returns**: Dictionary with list of accessible projects and their allowed datasets

**Example Response**:
```json
{
  "success": true,
  "accessible_projects": ["project1", "project2"],
  "project_details": {
    "project1": {
      "is_billing_project": true,
      "allowed_datasets": ["dataset1", "dataset2"]
    }
  },
  "total_count": 2
}
```

## Discovery Tools

### list_projects()

Lists all configured BigQuery projects that this server can access.

**Parameters**: None

**Returns**: Dictionary with project information

**Example Response**:
```json
{
  "status": "success",
  "projects": [
    {
      "project_id": "analytics-prod",
      "project_name": "Analytics Production",
      "description": "Main data warehouse",
      "dataset_patterns": ["prod_*", "reporting_*"]
    },
    {
      "project_id": "raw-data",
      "project_name": "Raw Data Lake",
      "description": "Unprocessed data storage",
      "dataset_patterns": ["*"]
    }
  ],
  "total_projects": 2,
  "billing_project": "my-billing-project"
}
```

**Compact Mode**: Omits `dataset_patterns` field

### list_datasets(project)

Lists datasets in a project that match configured access patterns.

**Parameters**:
- `project` (str, optional): Project ID. Defaults to billing project.

**Returns**: Dictionary with dataset information

**Example Response**:
```json
{
  "status": "success",
  "project": "analytics-prod",
  "project_name": "Analytics Production",
  "datasets": [
    {
      "dataset_id": "prod_sales",
      "location": "EU",
      "created": "2023-01-15T10:30:00",
      "modified": "2024-12-01T14:22:00",
      "description": "Production sales data"
    },
    {
      "dataset_id": "reporting_metrics",
      "location": "EU",
      "created": "2023-03-20T09:15:00",
      "modified": "2024-12-15T16:45:00",
      "description": "Aggregated reporting metrics"
    }
  ],
  "total_datasets": 2
}
```

**Compact Mode**: Only includes `dataset_id`, `location`, and `description` (if present)

### list_tables(dataset, table_type)

Lists tables, views, and materialized views in a dataset.

**Parameters**:
- `dataset` (str): Dataset path as 'dataset_id' or 'project.dataset_id'
- `table_type` (str, optional): Filter by type - 'all', 'table', 'view', or 'materialized_view'. Default: 'all'

**Returns**: Dictionary with table information

**Example Response**:
```json
{
  "status": "success",
  "project": "analytics-prod",
  "dataset": "prod_sales",
  "full_path": "analytics-prod.prod_sales",
  "tables": [
    {
      "table_id": "transactions",
      "table_type": "TABLE",
      "created": "2023-05-10T11:00:00",
      "modified": "2024-12-20T08:30:00",
      "num_rows": 1500000,
      "size_bytes": 536870912,
      "size_mb": 512.0,
      "description": "Daily transaction records",
      "schema_field_count": 15,
      "partitioning": {
        "type": "DAY",
        "field": "transaction_date"
      }
    },
    {
      "table_id": "customer_summary",
      "table_type": "VIEW",
      "created": "2023-06-01T14:00:00",
      "modified": "2023-06-01T14:00:00",
      "num_rows": 0,
      "size_bytes": 0,
      "size_mb": 0.0,
      "description": "Customer aggregation view"
    }
  ],
  "total_tables": 2,
  "filtered_by_type": "ALL"
}
```

**Compact Mode**: Only includes `table_id`, `type`, `rows`, `size_mb`, and `description` (if present)

## Analysis Tools

### analyze_table(table)

Analyzes table structure and provides column-level statistics without sampling.

**Parameters**:
- `table` (str): Table path as 'project.dataset.table' or 'dataset.table'

**Returns**: Dictionary with table analysis

**Example Response**:
```json
{
  "status": "success",
  "table": "analytics-prod.prod_sales.transactions",
  "total_rows": 1500000,
  "size_mb": 512.0,
  "columns": [
    {
      "name": "transaction_id",
      "type": "STRING",
      "description": "Unique transaction identifier",
      "null_count": 0,
      "distinct_count": 1500000
    },
    {
      "name": "amount",
      "type": "NUMERIC",
      "description": "Transaction amount in USD",
      "null_count": 1250,
      "distinct_count": 8750
    },
    {
      "name": "transaction_date",
      "type": "DATE",
      "description": "Date of transaction",
      "null_count": 0,
      "distinct_count": 365
    }
  ],
  "partitioned_by": "transaction_date"
}
```

### analyze_columns(table, columns, include_examples, sample_size)

Performs deep statistical analysis on specific columns with sampling.

**Parameters**:
- `table` (str): Table path as 'project.dataset.table' or 'dataset.table'
- `columns` (str, optional): Comma-separated list of column names. Default: all columns
- `include_examples` (bool, optional): Include example values. Default: true
- `sample_size` (int, optional): Number of rows to sample. Default: 10000

**Returns**: Dictionary with detailed column analysis

**Example Response**:
```json
{
  "status": "success",
  "table": "analytics-prod.prod_sales.transactions",
  "columns_analyzed": 2,
  "sample_size": 10000,
  "analysis_method": "RANDOM_SAMPLING",
  "columns": [
    {
      "column_name": "amount",
      "data_type": "NUMERIC",
      "total_rows_analyzed": 10000,
      "null_analysis": {
        "null_count": 125,
        "non_null_count": 9875,
        "null_percentage": 1.25,
        "is_nullable": true
      },
      "cardinality": {
        "distinct_count": 4250,
        "distinct_percentage": 42.5,
        "is_unique": false,
        "has_duplicates": true
      },
      "numeric_stats": {
        "min": 0.01,
        "max": 9999.99,
        "avg": 127.45,
        "stddev": 245.67,
        "quartiles": {
          "q0_min": 0.01,
          "q1": 25.50,
          "q2_median": 75.00,
          "q3": 150.25,
          "q4_max": 9999.99
        }
      },
      "classification": {
        "data_type": "NUMERIC",
        "nullable": true,
        "null_ratio": 0.0125,
        "category": "measure",
        "cardinality_type": "high"
      },
      "data_quality": {
        "completeness": 98.75,
        "uniqueness": 42.5,
        "has_nulls": true,
        "has_empty_strings": false
      }
    },
    {
      "column_name": "customer_id",
      "data_type": "STRING",
      "total_rows_analyzed": 10000,
      "null_analysis": {
        "null_count": 0,
        "non_null_count": 10000,
        "null_percentage": 0.0,
        "is_nullable": false
      },
      "cardinality": {
        "distinct_count": 2500,
        "distinct_percentage": 25.0,
        "is_unique": false,
        "has_duplicates": true
      },
      "string_stats": {
        "min_length": 10,
        "max_length": 10,
        "avg_length": 10.0
      },
      "top_values": [
        {"value": "CUST000123", "count": 25, "percentage": 0.25},
        {"value": "CUST000456", "count": 23, "percentage": 0.23},
        {"value": "CUST000789", "count": 22, "percentage": 0.22}
      ],
      "classification": {
        "data_type": "STRING",
        "nullable": false,
        "null_ratio": 0.0,
        "category": "identifier",
        "cardinality_type": "medium"
      },
      "data_quality": {
        "completeness": 100.0,
        "uniqueness": 25.0,
        "has_nulls": false,
        "has_empty_strings": false
      }
    }
  ]
}
```

## Query Execution

### execute_query(query, format, limit, timeout, dry_run, parameters)

Executes SELECT queries with comprehensive safety validation.

**Parameters**:
- `query` (str): SQL SELECT query to execute
- `format` (str, optional): Output format - 'json', 'csv', or 'table'. Default: 'json'
- `limit` (int, optional): Maximum rows to return. Default: from config (20)
- `timeout` (int, optional): Query timeout in seconds. Default: from config (60)
- `dry_run` (bool, optional): Validate and estimate cost without executing. Default: false
- `parameters` (dict, optional): Named query parameters as {name: value}

**Returns**: Dictionary with query results

**Example Response (Normal Execution)**:
```json
{
  "status": "success",
  "row_count": 10,
  "total_rows": 10,
  "bytes_processed": 1048576,
  "bytes_billed": 10485760,
  "cache_hit": false,
  "slot_millis": 1250,
  "execution_time_seconds": 1.234,
  "results": [
    {
      "customer_id": "CUST000123",
      "total_purchases": 15,
      "total_amount": 1567.89,
      "last_purchase_date": "2024-12-15"
    },
    {
      "customer_id": "CUST000456",
      "total_purchases": 8,
      "total_amount": 892.50,
      "last_purchase_date": "2024-12-18"
    }
  ],
  "schema": [
    {"name": "customer_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "total_purchases", "type": "INT64", "mode": "NULLABLE"},
    {"name": "total_amount", "type": "NUMERIC", "mode": "NULLABLE"},
    {"name": "last_purchase_date", "type": "DATE", "mode": "NULLABLE"}
  ]
}
```

**Example Response (Dry Run)**:
```json
{
  "status": "success",
  "dry_run": true,
  "total_bytes_processed": 536870912,
  "total_bytes_billed": 536870912,
  "estimated_cost_usd": 0.0026,
  "schema": [
    {"name": "customer_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "total_amount", "type": "NUMERIC", "mode": "NULLABLE"}
  ]
}
```

**Example Response (CSV Format)**:
```json
{
  "status": "success",
  "row_count": 3,
  "format": "csv",
  "data": "customer_id,total_purchases,total_amount\nCUST000123,15,1567.89\nCUST000456,8,892.50\nCUST000789,12,2103.75\n",
  "bytes_processed": 1048576,
  "execution_time_seconds": 0.892
}
```

## Error Responses

All tools return consistent error responses:

```json
{
  "status": "error",
  "error": "Project 'unknown-project' not in allowed list. Use list_projects() to see available projects.",
  "error_type": "ProjectAccessError"
}
```

Common error types:
- `ConfigurationError`: Invalid configuration
- `AuthenticationError`: Credential issues
- `ProjectAccessError`: Project not in allowlist
- `DatasetAccessError`: Dataset doesn't match patterns
- `TableNotFoundError`: Table doesn't exist
- `SecurityError`: Forbidden SQL operations
- `QueryExecutionError`: Query failed to execute
- `QueryTimeoutError`: Query exceeded timeout
