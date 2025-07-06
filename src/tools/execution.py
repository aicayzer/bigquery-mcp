"""Query execution tools with safety checks and result formatting."""

import logging
from typing import Dict, Any, List, Optional, Union
import json
import csv
import io
from datetime import datetime, date, time
from decimal import Decimal

from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
from utils.errors import QueryExecutionError, SecurityError, SQLValidationError
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


def _validate_query_safety(query: str) -> None:
    """Validate query for safety and security.
    
    Raises SecurityError if query contains forbidden operations.
    """
    # Use SQL validator with the global config
    validator = SQLValidator(config)
    
    try:
        validator.validate_query(query)
    except SQLValidationError as e:
        raise SecurityError(str(e))
    
    # Additional safety checks specific to execution
    query_upper = query.upper().strip()
    
    # Ensure it's a SELECT query (WITH is allowed for CTEs)
    if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
        raise SecurityError("Only SELECT queries are allowed")


def _format_query_results(results: List[Dict], format_type: str = 'json') -> Union[str, List[Dict]]:
    """Format query results based on requested format.
    
    Args:
        results: List of row dictionaries
        format_type: Output format ('json', 'csv', 'table')
        
    Returns:
        Formatted results
    """
    if format_type == 'json':
        return results
    
    elif format_type == 'csv':
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
    
    elif format_type == 'table':
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
            line = " | ".join(
                str(row.get(col, '')).ljust(widths[col]) 
                for col in columns
            )
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
        return value.decode('utf-8', errors='replace')
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(v) for v in value]
    else:
        return value


def execute_query(
    query: str,
    format: str = 'json',
    max_rows: Optional[int] = None,
    timeout: Optional[int] = None,
    dry_run: bool = False,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute a BigQuery SQL query with safety checks and formatting.
    
    Executes SELECT queries against BigQuery with comprehensive safety
    validation, result limiting, and multiple output formats.
    
    Args:
        query: SQL query to execute (SELECT only)
        format: Output format - 'json', 'csv', or 'table'
        max_rows: Maximum rows to return (default: from config)
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
        _validate_query_safety(query)
        
        # Apply limits
        if max_rows is None:
            max_rows = config.limits.default_row_limit
        else:
            max_rows = min(max_rows, config.limits.max_row_limit)
        
        if timeout is None:
            timeout = config.limits.max_query_timeout
        
        # Add LIMIT if not present and not dry run
        query_upper = query.upper().strip()
        if not dry_run and 'LIMIT' not in query_upper:
            query = f"{query.rstrip().rstrip(';')} LIMIT {max_rows}"
        
        # Configure query job
        job_config = QueryJobConfig(
            use_query_cache=True,
            dry_run=dry_run,
            maximum_bytes_billed=config.limits.max_bytes_processed,
            timeout_ms=timeout * 1000 if timeout else None
        )
        
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
            log_query = query[:config.max_query_log_length]
            if len(query) > config.max_query_log_length:
                log_query += "..."
            logger.info(f"Query: {log_query}")
        
        # Execute query
        query_job = bq_client.client.query(query, job_config=job_config)
        
        # Handle dry run
        if dry_run:
            return {
                'status': 'success',
                'dry_run': True,
                'total_bytes_processed': query_job.total_bytes_processed,
                'total_bytes_billed': query_job.total_bytes_billed,
                'estimated_cost_usd': round(
                    (query_job.total_bytes_billed / 1e12) * 5.0, 4
                ),  # $5 per TB
                'schema': [
                    {
                        'name': field.name,
                        'type': field.field_type,
                        'mode': field.mode
                    }
                    for field in query_job.schema
                ] if query_job.schema else []
            }
        
        # Get results with proper timeout handling
        # Use the same timeout for waiting for results as for query execution
        results = list(query_job.result(max_results=max_rows, timeout=timeout))
        
        # Convert to dictionaries with proper serialization
        rows = []
        for row in results:
            row_dict = {}
            for field in query_job.schema:
                value = row[field.name]
                row_dict[field.name] = _serialize_value(value)
            rows.append(row_dict)
        
        # Format results
        formatted_results = _format_query_results(rows, format)
        
        # Build response
        response = {
            'status': 'success',
            'row_count': len(rows),
            'total_rows': query_job.total_rows if hasattr(query_job, 'total_rows') else len(rows),
            'bytes_processed': query_job.total_bytes_processed,
            'bytes_billed': query_job.total_bytes_billed,
            'cache_hit': query_job.cache_hit if hasattr(query_job, 'cache_hit') else False,
            'slot_millis': query_job.slot_millis if hasattr(query_job, 'slot_millis') else None
        }
        
        # Add results based on format
        if format == 'json':
            response['results'] = formatted_results
            
            # Add schema in non-compact mode
            if not formatter.compact_mode:
                response['schema'] = [
                    {
                        'name': field.name,
                        'type': field.field_type,
                        'mode': field.mode,
                        'description': field.description or ''
                    }
                    for field in query_job.schema
                ]
        else:
            response['format'] = format
            response['data'] = formatted_results
        
        # Add execution time
        if hasattr(query_job, 'created') and hasattr(query_job, 'ended'):
            execution_time = (query_job.ended - query_job.created).total_seconds()
            response['execution_time_seconds'] = round(execution_time, 3)
        
        # Log results if enabled (only in debug mode)
        if config.log_results and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Query returned {len(rows)} rows")
        
        return response
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"Query execution error: {error_str}")
        
        # Handle specific error types
        if "403" in error_str:
            raise QueryExecutionError(
                f"Permission denied. Ensure you have bigquery.jobs.create permission "
                f"and access to the referenced tables."
            )
        elif "404" in error_str:
            raise QueryExecutionError(
                f"Table not found. Check the table references in your query."
            )
        elif "Syntax error" in error_str:
            raise QueryExecutionError(
                f"SQL syntax error: {error_str}"
            )
        elif isinstance(e, TimeoutError) or "TimeoutError" in str(type(e)):
            # Only treat actual timeout errors as timeouts
            raise QueryExecutionError(
                f"Query timeout after {timeout} seconds. "
                f"Try a smaller query or increase the timeout."
            )
        else:
            # For any other error, preserve the original message
            raise QueryExecutionError(f"Query execution failed: {error_str}")


def register_execution_tools(mcp_server, error_handler, bigquery_client, configuration, response_formatter):
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
