"""Custom error classes for BigQuery MCP operations."""


class BigQueryMCPError(Exception):
    """Base exception for all BigQuery MCP errors."""
    pass


class ConfigurationError(BigQueryMCPError):
    """Raised when configuration is invalid or missing."""
    pass


class AuthenticationError(BigQueryMCPError):
    """Raised when authentication fails."""
    pass


class ProjectAccessError(BigQueryMCPError):
    """Raised when attempting to access a disallowed project."""
    pass


class DatasetAccessError(BigQueryMCPError):
    """Raised when attempting to access a disallowed dataset."""
    pass


class TableNotFoundError(BigQueryMCPError):
    """Raised when a requested table doesn't exist."""
    pass


class InvalidTablePathError(BigQueryMCPError):
    """Raised when table path format is invalid."""
    pass


class SQLValidationError(BigQueryMCPError):
    """Raised when SQL query contains forbidden operations."""
    pass


class SecurityError(BigQueryMCPError):
    """Raised when a security policy is violated."""
    pass


class QueryExecutionError(BigQueryMCPError):
    """Raised when query execution fails."""
    pass


class QueryTimeoutError(QueryExecutionError):
    """Raised when query exceeds timeout limit."""
    pass


class ResourceLimitError(BigQueryMCPError):
    """Raised when a resource limit is exceeded."""
    pass
