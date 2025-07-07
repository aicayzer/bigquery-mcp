"""Development and debugging tools for BigQuery MCP.

These tools are for development purposes only and should be disabled
in production deployments.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Global references that will be set by server.py
mcp = None
handle_error = None
bq_client = None
config = None
formatter = None

# Development tools are disabled by default
DEVELOPMENT_TOOLS_ENABLED = False


def _ensure_initialized():
    """Ensure that global dependencies are initialized."""
    if any(x is None for x in [mcp, bq_client, config, formatter]):
        raise RuntimeError(
            "Development tools not properly initialized. "
            "These tools must be used through the MCP server."
        )


def get_server_info() -> Dict[str, Any]:
    """Get information about the BigQuery MCP server.

    Returns server version, configuration, and available features.

    NOTE: This is a development tool and should not be used in production.
    """
    _ensure_initialized()

    if not DEVELOPMENT_TOOLS_ENABLED:
        return {
            "status": "error",
            "message": "Development tools are disabled in production",
        }

    return {
        "status": "success",
        "server": {
            "name": config.server_name,
            "version": config.server_version,
            "billing_project": bq_client.billing_project,
            "location": bq_client.client.location,
            "allowed_projects": len(config.projects),
            "features": {
                "cross_project_access": True,
                "column_analysis": True,
                "sql_validation": True,
                "compact_mode": formatter.compact_mode,
            },
        },
    }


def health_check() -> Dict[str, Any]:
    """Check server health and BigQuery connectivity.

    Tests configuration and BigQuery access.

    NOTE: This is a development tool and should not be used in production.
    """
    _ensure_initialized()

    if not DEVELOPMENT_TOOLS_ENABLED:
        return {
            "status": "error",
            "message": "Development tools are disabled in production",
        }

    health = {
        "status": "healthy",
        "checks": {
            "configuration": "ok",
            "bigquery_client": "ok",
            "authentication": "ok",
        },
    }

    try:
        # Test BigQuery access by listing datasets in billing project
        list(bq_client.client.list_datasets(bq_client.billing_project, max_results=1))
        health["checks"]["bigquery_access"] = "ok"
        health["checks"]["location"] = bq_client.client.location
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["bigquery_access"] = f"error: {str(e)}"

    return health


def register_development_tools(
    mcp_server, error_handler, bigquery_client, configuration, response_formatter
):
    """Register development tools with the MCP server.

    This function is called by server.py to inject dependencies and register tools.
    Development tools are only registered if DEVELOPMENT_TOOLS_ENABLED is True.
    """
    global mcp, handle_error, bq_client, config, formatter

    mcp = mcp_server
    handle_error = error_handler
    bq_client = bigquery_client
    config = configuration
    formatter = response_formatter

    # Only register if development tools are enabled
    if DEVELOPMENT_TOOLS_ENABLED:
        mcp.tool()(handle_error(get_server_info))
        mcp.tool()(handle_error(health_check))
        logger.info("Development tools registered (DEVELOPMENT MODE)")
    else:
        logger.info("Development tools disabled (PRODUCTION MODE)")
