"""Query execution tools with safety checks and result formatting."""

import csv
import io
import logging
import time as time_module
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter

from utils.errors import (
    SecurityError,
    SQLValidationError,
    create_ai_friendly_error,
)
from utils.validation import SQLValidator

logger = logging.getLogger(__name__)

# Global references that will be set by server.py
mcp = None
handle_error = None
bq_client = None
config = None
formatter = None


def _ensure_initialized():
    """Ensure that global dependencies are initialized."""
    if any(x is None for x in [mcp, bq_client, config, formatter]):
        raise RuntimeError(
            "Execution tools not properly initialized. "
            "These tools must be used through the MCP server."
        )


def _format_query_results(results: List[Dict], format_type: str = "json") -> Union[str, List[Dict]]:
    """Format query results based on requested format.

    Args:
        results: List of row dictionaries
        format_type: Output format ('json', 'csv', 'table')

    Returns:
        Formatted results
    """
    if format_type == "json":
        return results

    elif format_type == "csv":
        if not results:
            return ""

        # Get column names from first row
        columns = list(results[0].keys())

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)

        return output.getvalue()

    elif format_type == "table":
        if not results:
            return "No results"

        # Simple ASCII table format
        columns = list(results[0].keys())

        # Calculate column widths
        widths = {col: len(col) for col in columns}
        for row in results:
            for col, val in row.items():
                widths[col] = max(widths[col], len(str(val)))

        # Build table
        lines = []

        # Header
        header = " | ".join(col.ljust(widths[col]) for col in columns)
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for row in results:
            line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
            lines.append(line)

        return "\n".join(lines)

    else:
        raise ValueError(f"Unknown format type: {format_type}")


def _serialize_value(value: Any) -> Any:
    """Convert BigQuery values to JSON-serializable format."""
    if value is None:
        return None
    elif isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        # Filter out None values to prevent BigQuery array NULL element errors
        return [_serialize_value(v) for v in value if v is not None]
    elif hasattr(value, "__dict__"):
        # Handle BigQuery custom objects
        return str(value)
    else:
        return value


def execute_query(
    query: str,
    format: str = "json",
    limit: Optional[int] = None,
    timeout: Optional[int] = None,
    dry_run: bool = False,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a BigQuery SQL query with safety checks and formatting.

    Executes SELECT queries against BigQuery with comprehensive safety
    validation, result limiting, and multiple output formats.

    Args:
        query: SQL query to execute (SELECT only)
        format: Output format - 'json', 'csv', or 'table'
        limit: Maximum rows to return (default: from config)
        timeout: Query timeout in seconds (default: from config)
        dry_run: If True, validate and estimate query without executing
        parameters: Named query parameters as {name: value} dict

    Returns:
        Dictionary containing query results and metadata

    Raises:
        SecurityError: If query contains forbidden operations
        QueryExecutionError: If query execution fails
    """
    _ensure_initialized()
    logger.info(f"Executing query (dry_run={dry_run}, format={format})")

    try:
        # Validate query safety
        validator = SQLValidator(config)
        try:
            validator.validate_query(query)
        except SQLValidationError as e:
            raise SecurityError(str(e))

        # Apply limits with type checking and conversion
        if limit is None:
            limit = config.limits.default_limit
        else:
            # Convert string to int if needed (for MCP compatibility)
            if isinstance(limit, str):
                try:
                    limit = int(limit)
                except ValueError:
                    raise ValueError(f"limit must be an integer, got: {limit}")
            elif isinstance(limit, float):
                limit = int(limit)
            elif not isinstance(limit, int):
                raise ValueError(f"limit must be an integer, got type: {type(limit)}")

            limit = min(limit, config.limits.max_limit)

        if timeout is None:
            timeout = config.limits.max_query_timeout
        else:
            # Convert string to int if needed (for MCP compatibility)
            if isinstance(timeout, str):
                try:
                    timeout = int(timeout)
                except ValueError:
                    raise ValueError(f"timeout must be an integer, got: {timeout}")
            elif isinstance(timeout, float):
                timeout = int(timeout)
            elif not isinstance(timeout, int):
                raise ValueError(f"timeout must be an integer, got type: {type(timeout)}")

            timeout = min(timeout, config.limits.max_query_timeout)

        # Add LIMIT if not present and not dry run
        query_upper = query.upper().strip()
        if not dry_run and "LIMIT" not in query_upper:
            query = f"{query.rstrip().rstrip(';')} LIMIT {limit}"

        # Configure query job
        job_config = QueryJobConfig(
            use_query_cache=True,
            dry_run=dry_run,
            maximum_bytes_billed=config.limits.max_bytes_processed,
        )

        # Set job timeout if specified
        if timeout:
            job_config.job_timeout_ms = timeout * 1000

        # Add parameters if provided
        if parameters:
            query_parameters = []
            for name, value in parameters.items():
                # Auto-detect parameter type
                param = ScalarQueryParameter(name, None, value)
                query_parameters.append(param)
            job_config.query_parameters = query_parameters

        # Log query if enabled
        if config.log_queries:
            log_query = query[:500]  # Limit query log length
            if len(query) > 500:
                log_query += "..."
            logger.info(f"Query: {log_query}")

        # Execute query
        query_job = bq_client.client.query(query, job_config=job_config)

        # Handle dry run
        if dry_run:
            total_bytes = getattr(query_job, "total_bytes_processed", 0) or 0
            total_billed = getattr(query_job, "total_bytes_billed", 0) or 0

            return {
                "status": "success",
                "dry_run": True,
                "total_bytes_processed": total_bytes,
                "total_bytes_billed": total_billed,
                "estimated_cost_usd": round((total_billed / 1e12) * 5.0, 4)
                if total_billed
                else 0.0,
                "schema": (
                    [
                        {
                            "name": field.name,
                            "type": field.field_type,
                            "mode": field.mode,
                        }
                        for field in query_job.schema
                    ]
                    if hasattr(query_job, "schema") and query_job.schema
                    else []
                ),
            }

        # Get results with proper timeout handling and progress tracking
        logger.info(
            f"Starting query execution (estimated complexity: {_estimate_query_complexity(query)})"
        )

        # Wait for the query to complete and get the row iterator
        try:
            start_time = time_module.time()
            rows_iterator = query_job.result(timeout=timeout)
            execution_time = time_module.time() - start_time
            logger.info(f"Query completed in {execution_time:.2f} seconds")
        except Exception as e:
            execution_time = time_module.time() - start_time
            logger.error(f"Query failed after {execution_time:.2f} seconds: {e}")
            raise

        # CRITICAL FIX: Get schema BEFORE consuming the iterator
        schema_fields = None
        if rows_iterator:
            # Get schema from row iterator (more reliable than query_job.schema for executed queries)
            if hasattr(rows_iterator, "schema") and rows_iterator.schema:
                schema_fields = rows_iterator.schema
            elif query_job.schema:
                schema_fields = query_job.schema

        # Convert iterator to list with row limiting
        results = []
        if rows_iterator:
            for row in rows_iterator:
                results.append(row)
                if limit and len(results) >= limit:
                    break

        # Convert to dictionaries with proper serialization
        rows = []
        if results:
            if schema_fields:
                # Use proper schema
                for row in results:
                    row_dict = {}
                    for field in schema_fields:
                        value = row[field.name]
                        row_dict[field.name] = _serialize_value(value)
                    rows.append(row_dict)
            else:
                # Fallback: convert rows directly (BigQuery Row objects are dict-like)
                for row in results:
                    row_dict = {}
                    for key, value in row.items():
                        row_dict[key] = _serialize_value(value)
                    rows.append(row_dict)

        # Format results

        formatted_results = _format_query_results(rows, format)

        # Build response
        response = {
            "status": "success",
            "row_count": len(rows),
            "total_rows": (query_job.total_rows if hasattr(query_job, "total_rows") else len(rows)),
            "bytes_processed": query_job.total_bytes_processed,
            "bytes_billed": query_job.total_bytes_billed,
            "cache_hit": (query_job.cache_hit if hasattr(query_job, "cache_hit") else False),
            "slot_millis": (query_job.slot_millis if hasattr(query_job, "slot_millis") else None),
        }

        # Add results based on format
        if format == "json":
            response["results"] = formatted_results

            # Add schema in non-compact mode
            if not formatter.compact_mode and schema_fields:
                response["schema"] = [
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description or "",
                    }
                    for field in schema_fields
                ]
        else:
            response["format"] = format
            response["data"] = formatted_results

        # Add execution time
        if hasattr(query_job, "created") and hasattr(query_job, "ended"):
            execution_time = (query_job.ended - query_job.created).total_seconds()
            response["execution_time_seconds"] = round(execution_time, 3)

        # Log results if enabled (only in debug mode)
        if config.log_results and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Query returned {len(rows)} rows")

        return response

    except Exception as e:
        error_str = str(e)
        logger.error(f"Query execution error: {error_str}")

        # Create AI-friendly error with context
        context = {
            "query_length": len(query),
            "query_complexity": _estimate_query_complexity(query),
            "timeout_used": timeout,
            "limit_used": limit,
            "dry_run": dry_run,
        }

        # Use the new AI-friendly error creation system
        ai_friendly_error = create_ai_friendly_error(e, context)
        logger.error(f"AI-friendly error: {ai_friendly_error.to_dict()}")
        raise ai_friendly_error


def _estimate_query_complexity(query: str) -> str:
    """
    Estimate query complexity for better timeout predictions.

    Args:
        query: SQL query string

    Returns:
        Complexity level as string
    """
    query_upper = query.upper()
    complexity_score = 0

    # Count complexity indicators
    if "JOIN" in query_upper:
        complexity_score += query_upper.count("JOIN") * 2
    if "WINDOW" in query_upper or "OVER(" in query_upper:
        complexity_score += 3
    if "GROUP BY" in query_upper:
        complexity_score += 1
    if "ORDER BY" in query_upper:
        complexity_score += 1
    if "UNION" in query_upper:
        complexity_score += 2
    if "WITH" in query_upper:
        complexity_score += query_upper.count("WITH")

    # Classify complexity
    if complexity_score == 0:
        return "simple"
    elif complexity_score <= 3:
        return "moderate"
    elif complexity_score <= 7:
        return "complex"
    else:
        return "very_complex"


def register_execution_tools(
    mcp_server, error_handler, bigquery_client, configuration, response_formatter
):
    """Register execution tools with the MCP server.

    This function is called by server.py to inject dependencies and register tools.
    """
    global mcp, handle_error, bq_client, config, formatter

    mcp = mcp_server
    handle_error = error_handler
    bq_client = bigquery_client
    config = configuration
    formatter = response_formatter

    # Register tools with MCP - let FastMCP handle protocol translation
    mcp.tool()(handle_error(execute_query))

    logger.info("Execution tools registered successfully")
