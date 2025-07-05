"""MCP tools for BigQuery operations."""

# Import tools to make them available when the package is imported
from .discovery import list_projects, list_datasets, list_tables

__all__ = [
    'list_projects',
    'list_datasets', 
    'list_tables',
]
