"""Analysis tools for table and column profiling."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from google.cloud.bigquery import QueryJobConfig
from utils.errors import DatasetAccessError, QueryExecutionError

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
            "Analysis tools not properly initialized. "
            "These tools must be used through the MCP server."
        )


def _build_analyze_query(project: str, dataset: str, table: str, sample_size: int = 1000) -> str:
    """Build optimized query for table analysis.
    
    Creates a query that efficiently samples data for analysis while
    avoiding full table scans when possible.
    """
    # Use TABLESAMPLE for efficient sampling on large tables
    return f"""
    WITH sampled_data AS (
        SELECT *
        FROM `{project}.{dataset}.{table}`
        TABLESAMPLE SYSTEM ({sample_size} ROWS)
    ),
    column_stats AS (
        SELECT 
            '{project}' as project_id,
            '{dataset}' as dataset_id,
            '{table}' as table_id,
            COUNT(*) as sample_rows,
            COUNT(DISTINCT TO_JSON_STRING(t)) as distinct_rows,
            ARRAY_AGG(
                STRUCT(
                    column_name,
                    data_type,
                    COUNT(*) OVER() - COUNTIF(value IS NULL) as non_null_count,
                    COUNTIF(value IS NULL) as null_count,
                    COUNT(DISTINCT value) as distinct_count
                )
            ) as column_info
        FROM sampled_data t,
        UNNEST(
            ARRAY(
                SELECT AS STRUCT 
                    column_name,
                    data_type,
                    CAST(TO_JSON_STRING(EXTRACT(JSON_VALUE FROM TO_JSON_STRING(t) AT '$.' || column_name)) AS STRING) as value
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE table_name = '{table}'
                AND table_schema = '{dataset}'
            )
        )
        GROUP BY column_name, data_type
    )
    SELECT * FROM column_stats
    """


def _classify_column(column_name: str, data_type: str, 
                    null_ratio: float, cardinality: int, 
                    sample_size: int) -> Dict[str, Any]:
    """Classify column based on its characteristics.
    
    Identifies column patterns like IDs, categories, measures, etc.
    """
    classification = {
        'data_type': data_type,
        'nullable': null_ratio > 0,
        'null_ratio': round(null_ratio, 4)
    }
    
    # Normalize column name for pattern matching
    name_lower = column_name.lower()
    
    # ID detection
    if any(pattern in name_lower for pattern in ['_id', 'id_', '_key', 'key_']) or name_lower == 'id':
        classification['category'] = 'identifier'
        classification['likely_primary_key'] = null_ratio == 0 and cardinality == sample_size
    
    # Date/time detection
    elif data_type in ['TIMESTAMP', 'DATETIME', 'DATE', 'TIME']:
        classification['category'] = 'temporal'
        
    # Numeric measure detection
    elif data_type in ['INT64', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC']:
        if cardinality < 10:
            classification['category'] = 'categorical_numeric'
        else:
            classification['category'] = 'measure'
            
    # String classification
    elif data_type == 'STRING':
        uniqueness_ratio = cardinality / sample_size if sample_size > 0 else 0
        
        if uniqueness_ratio > 0.95:
            classification['category'] = 'high_cardinality_string'
        elif cardinality < 50:
            classification['category'] = 'categorical'
        else:
            classification['category'] = 'descriptive'
            
    # Boolean
    elif data_type == 'BOOL':
        classification['category'] = 'boolean'
        
    # Complex types
    elif data_type in ['STRUCT', 'ARRAY', 'JSON']:
        classification['category'] = 'complex'
        
    else:
        classification['category'] = 'other'
    
    # Add cardinality classification
    if cardinality == 1:
        classification['cardinality_type'] = 'constant'
    elif cardinality == 2:
        classification['cardinality_type'] = 'binary'
    elif cardinality < 10:
        classification['cardinality_type'] = 'low'
    elif cardinality < 100:
        classification['cardinality_type'] = 'medium'
    else:
        classification['cardinality_type'] = 'high'
    
    return classification


def analyze_table(table_path: str, sample_size: int = 1000) -> Dict[str, Any]:
    """Analyze table structure and statistics.
    
    Provides comprehensive table analysis including row counts, data types,
    null statistics, and cardinality information for each column.
    
    Args:
        table_path: Full table path as 'project.dataset.table' or 'dataset.table'
        sample_size: Number of rows to sample for analysis (default: 1000)
        
    Returns:
        Dictionary containing table analysis results
    """
    _ensure_initialized()
    logger.info(f"Analyzing table: {table_path} (sample size: {sample_size})")
    
    try:
        # Parse table path
        parts = table_path.split('.')
        if len(parts) == 3:
            project, dataset, table = parts
        elif len(parts) == 2:
            project = bq_client.billing_project
            dataset, table = parts
        else:
            raise ValueError(
                "Invalid table path. Use 'project.dataset.table' or 'dataset.table'"
            )
        
        # Validate access
        if not config.is_dataset_allowed(project, dataset):
            raise DatasetAccessError(
                f"Dataset '{dataset}' in project '{project}' is not accessible"
            )
        
        # Get table metadata
        table_ref = bq_client.client.get_table(f"{project}.{dataset}.{table}")
        
        # Get sample data for analysis
        sample_query = f"""
        SELECT *
        FROM `{project}.{dataset}.{table}`
        LIMIT {sample_size}
        """
        
        # Run sample query
        query_job = bq_client.client.query(
            sample_query,
            job_config=QueryJobConfig(use_query_cache=True)
        )
        sample_results = list(query_job.result())
        actual_sample_size = len(sample_results)
        
        # Analyze columns
        columns_analysis = []
        
        for field in table_ref.schema:
            # Calculate statistics for this column
            null_count = sum(1 for row in sample_results if row[field.name] is None)
            non_null_values = [row[field.name] for row in sample_results if row[field.name] is not None]
            distinct_count = len(set(str(v) for v in non_null_values))
            
            null_ratio = null_count / actual_sample_size if actual_sample_size > 0 else 0
            
            # Classify column
            classification = _classify_column(
                field.name,
                field.field_type,
                null_ratio,
                distinct_count,
                actual_sample_size
            )
            
            column_info = {
                'name': field.name,
                'type': field.field_type,
                'mode': field.mode,
                'description': field.description or '',
                'null_count': null_count,
                'null_percentage': round(null_ratio * 100, 2),
                'distinct_count': distinct_count,
                'classification': classification
            }
            
            # Add sample values for categorical columns
            if distinct_count <= 20 and non_null_values:
                value_counts = defaultdict(int)
                for v in non_null_values:
                    value_counts[str(v)] += 1
                column_info['sample_values'] = [
                    {'value': v, 'count': c} 
                    for v, c in sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ]
            
            columns_analysis.append(column_info)
        
        # Build response
        if formatter.compact_mode:
            # Compact format focuses on key information
            response = {
                'status': 'success',
                'table': f"{project}.{dataset}.{table}",
                'total_rows': table_ref.num_rows,
                'size_mb': round((table_ref.num_bytes or 0) / (1024 * 1024), 2),
                'columns': [
                    {
                        'name': col['name'],
                        'type': col['type'],
                        'nulls': col['null_percentage'],
                        'distinct': col['distinct_count'],
                        'category': col['classification']['category']
                    }
                    for col in columns_analysis
                ]
            }
            
            # Add partitioning info if present
            if table_ref.time_partitioning:
                response['partitioned_by'] = table_ref.time_partitioning.field or '_PARTITIONTIME'
                
        else:
            # Full format with comprehensive details
            response = {
                'status': 'success',
                'table': {
                    'project': project,
                    'dataset': dataset,
                    'table_id': table,
                    'full_path': f"{project}.{dataset}.{table}"
                },
                'metadata': {
                    'created': table_ref.created.isoformat() if table_ref.created else None,
                    'modified': table_ref.modified.isoformat() if table_ref.modified else None,
                    'description': table_ref.description or '',
                    'labels': table_ref.labels or {},
                    'location': table_ref.location
                },
                'statistics': {
                    'total_rows': table_ref.num_rows,
                    'total_bytes': table_ref.num_bytes,
                    'size_mb': round((table_ref.num_bytes or 0) / (1024 * 1024), 2),
                    'size_gb': round((table_ref.num_bytes or 0) / (1024 * 1024 * 1024), 2)
                },
                'structure': {
                    'column_count': len(table_ref.schema),
                    'has_partitioning': table_ref.time_partitioning is not None,
                    'has_clustering': bool(table_ref.clustering_fields),
                    'table_type': table_ref.table_type
                },
                'sample_info': {
                    'requested_rows': sample_size,
                    'actual_rows': actual_sample_size,
                    'sampling_method': 'LIMIT' if actual_sample_size < table_ref.num_rows else 'FULL'
                },
                'columns': columns_analysis
            }
            
            # Add partitioning details if present
            if table_ref.time_partitioning:
                response['structure']['partitioning'] = {
                    'type': table_ref.time_partitioning.type_,
                    'field': table_ref.time_partitioning.field,
                    'require_partition_filter': table_ref.require_partition_filter
                }
            
            # Add clustering details if present
            if table_ref.clustering_fields:
                response['structure']['clustering'] = {
                    'fields': table_ref.clustering_fields
                }
        
        return response
        
    except Exception as e:
        if "404" in str(e):
            raise DatasetAccessError(
                f"Table not found: {table_path}. "
                "Please check the table path and ensure you have access."
            )
        raise


def analyze_columns(
    table_path: str,
    columns: Optional[List[str]] = None,
    include_examples: bool = True,
    sample_size: int = 10000
) -> Dict[str, Any]:
    """Deep analysis of specific columns with statistical profiling.
    
    Provides detailed statistical analysis of columns including:
    - Null analysis and patterns
    - Cardinality and uniqueness
    - Value distribution for categorical data
    - Statistical measures for numeric data
    - Data quality indicators
    
    Args:
        table_path: Full table path as 'project.dataset.table' or 'dataset.table'
        columns: List of column names to analyze (None = all columns)
        include_examples: Include example values in response
        sample_size: Number of rows to sample for analysis
        
    Returns:
        Dictionary containing detailed column analysis
    """
    _ensure_initialized()
    logger.info(f"Analyzing columns in table: {table_path}")
    
    try:
        # Parse table path
        parts = table_path.split('.')
        if len(parts) == 3:
            project, dataset, table = parts
        elif len(parts) == 2:
            project = bq_client.billing_project
            dataset, table = parts
        else:
            raise ValueError(
                "Invalid table path. Use 'project.dataset.table' or 'dataset.table'"
            )
        
        # Validate access
        if not config.is_dataset_allowed(project, dataset):
            raise DatasetAccessError(
                f"Dataset '{dataset}' in project '{project}' is not accessible"
            )
        
        # Get table metadata
        table_ref = bq_client.client.get_table(f"{project}.{dataset}.{table}")
        
        # Determine columns to analyze
        if columns:
            # Validate requested columns exist
            schema_fields = {field.name: field for field in table_ref.schema}
            invalid_columns = [col for col in columns if col not in schema_fields]
            if invalid_columns:
                raise ValueError(
                    f"Columns not found in table: {', '.join(invalid_columns)}"
                )
            columns_to_analyze = columns
        else:
            # Analyze all columns
            columns_to_analyze = [field.name for field in table_ref.schema]
            
        # Build analysis query
        column_analyses = []
        
        # For each column, build appropriate analysis
        for col_name in columns_to_analyze:
            field = next(f for f in table_ref.schema if f.name == col_name)
            
            # Build column-specific analysis query
            if field.field_type in ['INT64', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC']:
                # Numeric analysis
                analysis_query = f"""
                WITH sample_data AS (
                    SELECT {col_name}
                    FROM `{project}.{dataset}.{table}`
                    TABLESAMPLE SYSTEM ({sample_size} ROWS)
                )
                SELECT
                    '{col_name}' as column_name,
                    COUNT(*) as total_count,
                    COUNTIF({col_name} IS NULL) as null_count,
                    COUNT(DISTINCT {col_name}) as distinct_count,
                    MIN({col_name}) as min_value,
                    MAX({col_name}) as max_value,
                    AVG({col_name}) as avg_value,
                    STDDEV({col_name}) as stddev_value,
                    APPROX_QUANTILES({col_name}, 4) as quartiles
                FROM sample_data
                """
            
            elif field.field_type == 'STRING':
                # String analysis
                analysis_query = f"""
                WITH sample_data AS (
                    SELECT {col_name}
                    FROM `{project}.{dataset}.{table}`
                    TABLESAMPLE SYSTEM ({sample_size} ROWS)
                ),
                value_counts AS (
                    SELECT 
                        {col_name} as value,
                        COUNT(*) as count
                    FROM sample_data
                    GROUP BY {col_name}
                    ORDER BY count DESC
                    LIMIT 20
                )
                SELECT
                    '{col_name}' as column_name,
                    COUNT(*) as total_count,
                    COUNTIF({col_name} IS NULL) as null_count,
                    COUNT(DISTINCT {col_name}) as distinct_count,
                    MIN(LENGTH({col_name})) as min_length,
                    MAX(LENGTH({col_name})) as max_length,
                    AVG(LENGTH({col_name})) as avg_length,
                    ARRAY_AGG(STRUCT(value, count)) as top_values
                FROM sample_data
                LEFT JOIN value_counts USING (value)
                """
            
            elif field.field_type in ['DATE', 'DATETIME', 'TIMESTAMP']:
                # Temporal analysis
                analysis_query = f"""
                WITH sample_data AS (
                    SELECT {col_name}
                    FROM `{project}.{dataset}.{table}`
                    TABLESAMPLE SYSTEM ({sample_size} ROWS)
                )
                SELECT
                    '{col_name}' as column_name,
                    COUNT(*) as total_count,
                    COUNTIF({col_name} IS NULL) as null_count,
                    COUNT(DISTINCT {col_name}) as distinct_count,
                    MIN({col_name}) as min_value,
                    MAX({col_name}) as max_value,
                    DATE_DIFF(MAX({col_name}), MIN({col_name}), DAY) as range_days
                FROM sample_data
                """
            
            else:
                # Generic analysis for other types
                analysis_query = f"""
                WITH sample_data AS (
                    SELECT {col_name}
                    FROM `{project}.{dataset}.{table}`
                    TABLESAMPLE SYSTEM ({sample_size} ROWS)
                )
                SELECT
                    '{col_name}' as column_name,
                    COUNT(*) as total_count,
                    COUNTIF({col_name} IS NULL) as null_count,
                    COUNT(DISTINCT TO_JSON_STRING({col_name})) as distinct_count
                FROM sample_data
                """
            
            # Run analysis query
            try:
                query_job = bq_client.client.query(
                    analysis_query,
                    job_config=QueryJobConfig(use_query_cache=True)
                )
                results = list(query_job.result())[0]
                
                # Build column analysis
                total_count = results.total_count or 0
                null_count = results.null_count or 0
                distinct_count = results.distinct_count or 0
                null_ratio = null_count / total_count if total_count > 0 else 0
                
                col_analysis = {
                    'column_name': col_name,
                    'data_type': field.field_type,
                    'mode': field.mode,
                    'description': field.description or '',
                    'total_rows_analyzed': total_count,
                    'null_analysis': {
                        'null_count': null_count,
                        'non_null_count': total_count - null_count,
                        'null_percentage': round(null_ratio * 100, 2),
                        'is_nullable': field.mode != 'REQUIRED'
                    },
                    'cardinality': {
                        'distinct_count': distinct_count,
                        'distinct_percentage': round((distinct_count / total_count * 100) if total_count > 0 else 0, 2),
                        'is_unique': distinct_count == total_count and total_count > 0,
                        'has_duplicates': distinct_count < total_count
                    }
                }
                
                # Add type-specific analysis
                if field.field_type in ['INT64', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC']:
                    col_analysis['numeric_stats'] = {
                        'min': float(results.min_value) if results.min_value is not None else None,
                        'max': float(results.max_value) if results.max_value is not None else None,
                        'avg': float(results.avg_value) if results.avg_value is not None else None,
                        'stddev': float(results.stddev_value) if results.stddev_value is not None else None
                    }
                    
                    if hasattr(results, 'quartiles') and results.quartiles:
                        col_analysis['numeric_stats']['quartiles'] = {
                            'q0_min': float(results.quartiles[0]) if results.quartiles[0] is not None else None,
                            'q1': float(results.quartiles[1]) if results.quartiles[1] is not None else None,
                            'q2_median': float(results.quartiles[2]) if results.quartiles[2] is not None else None,
                            'q3': float(results.quartiles[3]) if results.quartiles[3] is not None else None,
                            'q4_max': float(results.quartiles[4]) if results.quartiles[4] is not None else None
                        }
                
                elif field.field_type == 'STRING':
                    col_analysis['string_stats'] = {
                        'min_length': results.min_length,
                        'max_length': results.max_length,
                        'avg_length': round(results.avg_length, 2) if results.avg_length else 0
                    }
                    
                    if hasattr(results, 'top_values') and results.top_values and include_examples:
                        col_analysis['top_values'] = [
                            {'value': item.value, 'count': item.count, 
                             'percentage': round(item.count / total_count * 100, 2)}
                            for item in results.top_values if item.value is not None
                        ][:10]  # Limit to top 10
                
                elif field.field_type in ['DATE', 'DATETIME', 'TIMESTAMP']:
                    col_analysis['temporal_stats'] = {
                        'min_value': str(results.min_value) if results.min_value else None,
                        'max_value': str(results.max_value) if results.max_value else None,
                        'range_days': results.range_days if hasattr(results, 'range_days') else None
                    }
                
                # Add classification
                col_analysis['classification'] = _classify_column(
                    col_name,
                    field.field_type,
                    null_ratio,
                    distinct_count,
                    total_count
                )
                
                # Add data quality indicators
                col_analysis['data_quality'] = {
                    'completeness': round((1 - null_ratio) * 100, 2),
                    'uniqueness': round((distinct_count / total_count * 100) if total_count > 0 else 0, 2),
                    'has_nulls': null_count > 0,
                    'has_empty_strings': False  # Could be enhanced with additional query
                }
                
                column_analyses.append(col_analysis)
                
            except Exception as e:
                logger.warning(f"Failed to analyze column {col_name}: {e}")
                column_analyses.append({
                    'column_name': col_name,
                    'data_type': field.field_type,
                    'error': str(e)
                })
        
        # Build response
        response = {
            'status': 'success',
            'table': f"{project}.{dataset}.{table}",
            'columns_analyzed': len(column_analyses),
            'sample_size': sample_size,
            'analysis_method': 'TABLESAMPLE' if table_ref.num_rows > sample_size else 'FULL_SCAN',
            'columns': column_analyses
        }
        
        # Add summary statistics in non-compact mode
        if not formatter.compact_mode:
            response['summary'] = {
                'high_null_columns': [
                    col['column_name'] for col in column_analyses
                    if col.get('null_analysis', {}).get('null_percentage', 0) > 50
                ],
                'unique_columns': [
                    col['column_name'] for col in column_analyses
                    if col.get('cardinality', {}).get('is_unique', False)
                ],
                'constant_columns': [
                    col['column_name'] for col in column_analyses
                    if col.get('cardinality', {}).get('distinct_count', 0) == 1
                ],
                'high_cardinality_columns': [
                    col['column_name'] for col in column_analyses
                    if col.get('cardinality', {}).get('distinct_percentage', 0) > 90
                ]
            }
        
        return response
        
    except Exception as e:
        if "404" in str(e):
            raise DatasetAccessError(
                f"Table not found: {table_path}. "
                "Please check the table path and ensure you have access."
            )
        raise


def register_analysis_tools(mcp_server, error_handler, bigquery_client, configuration, response_formatter):
    """Register analysis tools with the MCP server.
    
    This function is called by server.py to inject dependencies and register tools.
    """
    global mcp, handle_error, bq_client, config, formatter
    
    mcp = mcp_server
    handle_error = error_handler
    bq_client = bigquery_client  
    config = configuration
    formatter = response_formatter
    
    # Register tools with MCP
    mcp.tool()(handle_error(analyze_table))
    mcp.tool()(handle_error(analyze_columns))
    
    logger.info("Analysis tools registered successfully")
