"""Custom error classes for BigQuery MCP operations."""


class BigQueryMCPError(Exception):
    """Base exception for all BigQuery MCP errors."""

    def __init__(
        self,
        message: str,
        error_source: str = "MCP_SERVER",
        error_code: str = None,
        suggested_action: str = None,
        context: dict = None,
    ):
        """Initialize BigQuery MCP error with enhanced information.

        Args:
            message: Error message
            error_source: Source of error (BIGQUERY_API, MCP_SERVER, USER_QUERY, CONFIGURATION)
            error_code: Specific error code for categorization
            suggested_action: Actionable suggestion for resolution
            context: Additional context information
        """
        super().__init__(message)
        self.error_source = error_source
        self.error_code = error_code
        self.suggested_action = suggested_action
        self.context = context or {}

    def to_dict(self) -> dict:
        """Convert error to dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "error_source": self.error_source,
            "error_code": self.error_code,
            "suggested_action": self.suggested_action,
            "context": self.context,
        }


class ConfigurationError(BigQueryMCPError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_source="CONFIGURATION", **kwargs)


class AuthenticationError(BigQueryMCPError):
    """Raised when authentication fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_source="BIGQUERY_API", error_code="AUTH_FAILED", **kwargs)


class ProjectAccessError(BigQueryMCPError):
    """Raised when attempting to access a disallowed project."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="MCP_SERVER", error_code="PROJECT_ACCESS_DENIED", **kwargs
        )


class DatasetAccessError(BigQueryMCPError):
    """Raised when attempting to access a disallowed dataset."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="MCP_SERVER", error_code="DATASET_ACCESS_DENIED", **kwargs
        )


class TableNotFoundError(BigQueryMCPError):
    """Raised when a requested table doesn't exist."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="BIGQUERY_API", error_code="TABLE_NOT_FOUND", **kwargs
        )


class InvalidTablePathError(BigQueryMCPError):
    """Raised when table path format is invalid."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="USER_QUERY", error_code="INVALID_TABLE_PATH", **kwargs
        )


class SQLValidationError(BigQueryMCPError):
    """Raised when SQL query contains forbidden operations."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="MCP_SERVER", error_code="SQL_VALIDATION_FAILED", **kwargs
        )


class SecurityError(BigQueryMCPError):
    """Raised when a security policy is violated."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="MCP_SERVER", error_code="SECURITY_VIOLATION", **kwargs
        )


class QueryExecutionError(BigQueryMCPError):
    """Raised when query execution fails."""

    def __init__(self, message: str, **kwargs):
        # Extract error_code from kwargs if provided, otherwise use default
        error_code = kwargs.pop("error_code", "QUERY_EXECUTION_FAILED")
        super().__init__(message, error_source="BIGQUERY_API", error_code=error_code, **kwargs)


class QueryTimeoutError(QueryExecutionError):
    """Raised when query exceeds timeout limit."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_source="BIGQUERY_API", error_code="QUERY_TIMEOUT", **kwargs)


class ResourceLimitError(BigQueryMCPError):
    """Raised when a resource limit is exceeded."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_source="BIGQUERY_API", error_code="RESOURCE_LIMIT_EXCEEDED", **kwargs
        )


def create_ai_friendly_error(original_error: Exception, context: dict = None) -> BigQueryMCPError:
    """Create an AI-friendly error from any exception.

    Args:
        original_error: The original exception
        context: Additional context information

    Returns:
        Enhanced BigQueryMCPError with AI-friendly information
    """
    error_str = str(original_error)
    context = context or {}

    # Classify error source and provide suggestions
    if "403" in error_str or "Permission denied" in error_str:
        return QueryExecutionError(
            f"Permission denied: {error_str}",
            error_code="PERMISSION_DENIED",
            suggested_action="Ensure you have bigquery.jobs.create permission and access to the referenced tables. Check your service account permissions.",
            context=context,
        )
    elif "404" in error_str or "Not found" in error_str:
        return QueryExecutionError(
            f"Resource not found: {error_str}",
            error_code="RESOURCE_NOT_FOUND",
            suggested_action="Verify the project ID, dataset name, and table name are correct. Check if the resource exists in BigQuery.",
            context=context,
        )
    elif "Syntax error" in error_str or "syntax" in error_str.lower():
        return BigQueryMCPError(
            f"SQL syntax error: {error_str}",
            error_source="USER_QUERY",
            error_code="SYNTAX_ERROR",
            suggested_action="Review your SQL syntax. Common issues: missing quotes, incorrect keywords, or malformed expressions.",
            context=context,
        )
    elif "Array cannot have a null element" in error_str:
        return BigQueryMCPError(
            f"BigQuery array contains NULL values: {error_str}",
            error_source="USER_QUERY",
            error_code="ARRAY_NULL_ELEMENT",
            suggested_action="Use COALESCE() to handle NULL values or filter them out before creating arrays.",
            context=context,
        )
    elif "timeout" in error_str.lower():
        return QueryTimeoutError(
            f"Query timeout: {error_str}",
            suggested_action="Try adding LIMIT clause, filtering data, or increase timeout parameter. Consider breaking complex queries into smaller parts.",
            context=context,
        )
    elif "quota" in error_str.lower() or "rate limit" in error_str.lower():
        return ResourceLimitError(
            f"BigQuery quota exceeded: {error_str}",
            suggested_action="Wait and retry later, or reduce query complexity. Check your BigQuery quotas and limits.",
            context=context,
        )
    else:
        return QueryExecutionError(
            f"Query execution failed: {error_str}",
            error_code="UNKNOWN_ERROR",
            suggested_action="Check the error details and BigQuery documentation. If the issue persists, verify your query and data.",
            context=context,
        )
