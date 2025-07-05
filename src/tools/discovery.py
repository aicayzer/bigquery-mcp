"""Discovery tools for listing projects, datasets, and tables."""

import logging
from typing import Dict, Any, List, Optional

from utils.errors import ProjectAccessError, DatasetAccessError

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
            "Discovery tools not properly initialized. "
            "These tools must be used through the MCP server."
        )


def list_projects() -> Dict[str, Any]:
    """List accessible BigQuery projects with descriptions.
    
    Returns all configured projects that this server can access,
    including their names, descriptions, and allowed dataset patterns.
    
    Returns:
        Dictionary containing project list and metadata
    """
    _ensure_initialized()
    logger.info("Listing accessible projects")
    
    projects = []
    for project_config in config.projects:
        project_info = {
            'project_id': project_config.project_id,
            'project_name': project_config.project_name,
            'description': project_config.description
        }
        
        # Include dataset patterns in non-compact mode
        if not formatter.compact_mode:
            project_info['dataset_patterns'] = project_config.datasets
        
        projects.append(project_info)
    
    logger.info(f"Found {len(projects)} accessible projects")
    
    return {
        'status': 'success',
        'projects': projects,
        'total_projects': len(projects),
        'billing_project': bq_client.billing_project
    }


def list_datasets(project: Optional[str] = None) -> Dict[str, Any]:
    """List datasets in a project, filtered by allowlist patterns.
    
    Lists all datasets in the specified project that match the
    configured access patterns. Defaults to the billing project
    if no project is specified.
    
    Args:
        project: Project ID to list datasets from (optional)
        
    Returns:
        Dictionary containing dataset list with metadata
    """
    _ensure_initialized()
    target_project = project or bq_client.billing_project
    logger.info(f"Listing datasets in project: {target_project}")
    
    # Validate project access
    if not config.is_project_allowed(target_project):
        raise ProjectAccessError(
            f"Project '{target_project}' not in allowed list. "
            f"Use list_projects() to see available projects."
        )
    
    # Get project configuration for description
    project_config = config.get_project(target_project)
    
    # Get datasets from BigQuery
    try:
        all_datasets = bq_client.list_datasets(target_project)
        
        datasets = []
        filtered_count = 0
        
        for dataset_item in all_datasets:
            # Get full dataset info
            try:
                dataset_ref = bq_client.client.get_dataset(dataset_item.reference)
                
                dataset_info = {
                    'dataset_id': dataset_ref.dataset_id,
                    'location': dataset_ref.location
                }
                
                # Add additional fields in non-compact mode
                if not formatter.compact_mode:
                    dataset_info.update({
                        'created': dataset_ref.created.isoformat() if dataset_ref.created else None,
                        'modified': dataset_ref.modified.isoformat() if dataset_ref.modified else None,
                        'description': dataset_ref.description or '',
                        'labels': dataset_ref.labels or {}
                    })
                else:
                    # Compact mode: only include description if present
                    if dataset_ref.description:
                        dataset_info['description'] = dataset_ref.description
                
                datasets.append(dataset_info)
                
            except Exception as e:
                logger.warning(f"Failed to get details for dataset {dataset_item.dataset_id}: {e}")
                filtered_count += 1
        
        logger.info(f"Found {len(datasets)} accessible datasets in {target_project}")
        
        response = {
            'status': 'success',
            'project': target_project,
            'project_name': project_config.project_name if project_config else target_project,
            'datasets': datasets,
            'total_datasets': len(datasets)
        }
        
        if filtered_count > 0:
            response['filtered_count'] = filtered_count
            response['note'] = f"{filtered_count} datasets were filtered due to access restrictions"
        
        return response
        
    except Exception as e:
        if "403" in str(e):
            raise ProjectAccessError(
                f"Permission denied accessing project '{target_project}'. "
                "Please ensure the service account has bigquery.datasets.list permission."
            )
        raise


def list_tables(
    dataset_path: str,
    table_type: Optional[str] = "all"
) -> Dict[str, Any]:
    """List tables in a dataset with optional type filtering.
    
    Lists all tables, views, and materialized views in the specified
    dataset. Can filter by table type for specific resource types.
    
    Args:
        dataset_path: Dataset reference as 'dataset_id' or 'project.dataset_id'
        table_type: Filter by type - 'all', 'table', 'view', or 'materialized_view'
        
    Returns:
        Dictionary containing table list with metadata
    """
    _ensure_initialized()
    logger.info(f"Listing tables in dataset: {dataset_path}")
    
    # Validate table type
    valid_types = ['all', 'table', 'view', 'materialized_view']
    if table_type.lower() not in valid_types:
        raise ValueError(
            f"Invalid table_type '{table_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    # Parse dataset path and get tables
    try:
        project, dataset = bq_client.parse_dataset_path(dataset_path)
        
        # Validate access
        if not config.is_dataset_allowed(project, dataset):
            project_config = config.get_project(project)
            patterns = project_config.datasets if project_config else []
            raise DatasetAccessError(
                f"Dataset '{dataset}' in project '{project}' is not accessible. "
                f"Allowed patterns: {', '.join(patterns)}"
            )
        
        # Get tables from BigQuery
        all_tables = bq_client.list_tables(dataset_path, 
                                         table_type if table_type != 'all' else None)
        
        tables = []
        for table_item in all_tables:
            try:
                # Get full table metadata
                table_ref = bq_client.client.get_table(table_item.reference)
                
                if formatter.compact_mode:
                    # Compact format
                    table_info = {
                        'table_id': table_ref.table_id,
                        'type': table_ref.table_type,
                        'rows': table_ref.num_rows or 0,
                        'size_mb': round((table_ref.num_bytes or 0) / (1024 * 1024), 2)
                    }
                    
                    # Include description only if present
                    if table_ref.description:
                        table_info['description'] = table_ref.description
                else:
                    # Standard format with all metadata
                    table_info = {
                        'table_id': table_ref.table_id,
                        'table_type': table_ref.table_type,
                        'created': table_ref.created.isoformat() if table_ref.created else None,
                        'modified': table_ref.modified.isoformat() if table_ref.modified else None,
                        'num_rows': table_ref.num_rows or 0,
                        'size_bytes': table_ref.num_bytes or 0,
                        'size_mb': round((table_ref.num_bytes or 0) / (1024 * 1024), 2),
                        'description': table_ref.description or '',
                        'location': table_ref.location,
                        'schema_field_count': len(table_ref.schema) if table_ref.schema else 0
                    }
                    
                    # Add partition info if present
                    if table_ref.time_partitioning:
                        table_info['partitioning'] = {
                            'type': table_ref.time_partitioning.type_,
                            'field': table_ref.time_partitioning.field
                        }
                    
                    # Add clustering info if present
                    if table_ref.clustering_fields:
                        table_info['clustering_fields'] = table_ref.clustering_fields
                
                tables.append(table_info)
                
            except Exception as e:
                logger.warning(f"Failed to get metadata for table {table_item.table_id}: {e}")
        
        # Sort tables by name for consistency
        tables.sort(key=lambda t: t.get('table_id', ''))
        
        logger.info(
            f"Found {len(tables)} tables of type '{table_type}' "
            f"in {project}.{dataset}"
        )
        
        response = {
            'status': 'success',
            'project': project,
            'dataset': dataset,
            'full_path': f"{project}.{dataset}",
            'tables': tables,
            'total_tables': len(tables)
        }
        
        if table_type != 'all':
            response['filtered_by_type'] = table_type.upper()
            
            # Add type breakdown in non-compact mode
            if not formatter.compact_mode:
                type_counts = {}
                for t in tables:
                    t_type = t.get('table_type', 'TABLE')
                    type_counts[t_type] = type_counts.get(t_type, 0) + 1
                response['type_breakdown'] = type_counts
        
        return response
        
    except Exception as e:
        if "404" in str(e):
            raise DatasetAccessError(
                f"Dataset not found: {dataset_path}. "
                "Please check the dataset path and ensure you have access."
            )
        raise


def register_discovery_tools(mcp_server, error_handler, bigquery_client, configuration, response_formatter):
    """Register discovery tools with the MCP server.
    
    This function is called by server.py to inject dependencies and register tools.
    """
    global mcp, handle_error, bq_client, config, formatter
    
    mcp = mcp_server
    handle_error = error_handler
    bq_client = bigquery_client
    config = configuration
    formatter = response_formatter
    
    # Register tools with MCP
    mcp.tool()(handle_error(list_projects))
    mcp.tool()(handle_error(list_datasets))
    mcp.tool()(handle_error(list_tables))
    
    logger.info("Discovery tools registered successfully")
