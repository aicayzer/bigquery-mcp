"""Context management tools for BigQuery MCP server."""

import logging

from fastmcp import FastMCP

from client import BigQueryClient

logger = logging.getLogger(__name__)


def register_context_tools(mcp: FastMCP, bq_client: BigQueryClient) -> None:
    """Register context management tools."""

    @mcp.tool()
    def get_current_context() -> dict:
        """
        Get the current BigQuery context including billing project, last accessed resources,
        and allowed projects/datasets for better query planning.

        Returns:
            Dict containing current context information
        """
        try:
            context = bq_client.get_context_info()
            return {"success": True, "context": context}
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def list_accessible_projects() -> dict:
        """
        List all projects accessible through the current configuration.

        Returns:
            Dict with list of accessible projects and their allowed datasets
        """
        try:
            config = bq_client.config

            if not config.allowed_projects:
                # If no restrictions, list available projects from client
                projects = [bq_client.billing_project]
                project_details = {
                    bq_client.billing_project: {
                        "is_billing_project": True,
                        "allowed_datasets": list(config.allowed_datasets)
                        if config.allowed_datasets
                        else ["all"],
                    }
                }
            else:
                projects = list(config.allowed_projects)
                project_details = {}
                for project in projects:
                    project_config = config.get_project(project)
                    project_details[project] = {
                        "is_billing_project": project == bq_client.billing_project,
                        "allowed_datasets": project_config.datasets if project_config else ["all"],
                    }

            return {
                "success": True,
                "accessible_projects": projects,
                "project_details": project_details,
                "total_count": len(projects),
            }
        except Exception as e:
            logger.error(f"Failed to list accessible projects: {e}")
            return {"success": False, "error": str(e)}
