"""Main server entry point for BigQuery MCP."""

import argparse
import functools
import logging
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastmcp import FastMCP

from client import BigQueryClient
from config import Config, get_config
from utils.errors import BigQueryMCPError
from utils.formatting import ResponseFormatter

# Load environment variables
load_dotenv()

# Configure logging with more robust path handling
log_level = os.getenv("LOG_LEVEL", "INFO")

# Try to create logs directory, but if it fails, use temp directory
try:
    script_dir = Path(__file__).parent.parent
    logs_dir = script_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "bigquery_mcp.log"
except Exception:
    # Fallback to temp directory if we can't create logs dir
    import tempfile

    logs_dir = Path(tempfile.gettempdir()) / "bigquery_mcp_logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "bigquery_mcp.log"
    print(f"Warning: Using temp directory for logs: {logs_dir}", file=sys.stderr)

# Configure logging
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # Always log to stderr first
        logging.FileHandler(log_file),
    ],
)
logger = logging.getLogger(__name__)

# Global instances
config = None
bq_client = None
formatter = None


def parse_arguments():
    """Parse command-line arguments for project:dataset patterns."""
    parser = argparse.ArgumentParser(
        description="BigQuery MCP Server - Access BigQuery datasets via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single project with all datasets
  python src/server.py sandbox-dev:*
  
  # Multiple projects with specific patterns
  python src/server.py sandbox-dev:dev_* sandbox-main:main_*
  
  # Multiple patterns for same project
  python src/server.py cayzer-xyz:demo_* cayzer-xyz:analytics_*
  
  # Fallback to config file if no arguments
  python src/server.py
        """,
    )

    parser.add_argument(
        "projects",
        nargs="*",
        help="Project access patterns in format 'project_id:dataset_pattern' (e.g., 'sandbox-dev:dev_*')",
    )

    parser.add_argument(
        "--config",
        help="Path to configuration file (used as fallback if no projects specified)",
    )

    parser.add_argument(
        "--billing-project",
        help="BigQuery billing project (overrides config and environment)",
    )

    parser.add_argument(
        "--location",
        default="EU",
        help="BigQuery location (default: EU)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="BigQuery MCP Server 1.1.0",
    )

    return parser.parse_args()


def parse_project_patterns(project_args):
    """Parse project:dataset patterns from command line arguments."""
    projects = {}

    for pattern in project_args:
        if ":" not in pattern:
            logger.error(
                f"Invalid project pattern '{pattern}'. Expected format: 'project_id:dataset_pattern'"
            )
            sys.exit(1)

        project_id, dataset_pattern = pattern.split(":", 1)

        if not project_id or not dataset_pattern:
            logger.error(
                f"Invalid project pattern '{pattern}'. Both project_id and dataset_pattern are required"
            )
            sys.exit(1)

        if project_id not in projects:
            projects[project_id] = []
        projects[project_id].append(dataset_pattern)

    return projects


def initialize_server():
    """Initialize server components."""
    global config, bq_client, formatter

    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Initialize configuration
        if args.projects:
            # Use command-line arguments
            logger.info("Using command-line project patterns")
            project_patterns = parse_project_patterns(args.projects)

            # Create config from CLI args
            config = Config.from_cli_args(
                project_patterns=project_patterns,
                billing_project=args.billing_project,
                location=args.location,
            )
        else:
            # Fall back to config file with deprecation warning
            logger.warning(
                "DEPRECATED: Using config file. Please migrate to command-line arguments."
            )
            logger.warning("Example: python src/server.py sandbox-dev:dev_* sandbox-main:main_*")
            config = get_config(args.config)

        # Initialize BigQuery client
        logger.info("Initializing BigQuery client...")
        bq_client = BigQueryClient(config)

        # Initialize formatter
        formatter = ResponseFormatter(config)

        logger.info(f"Server initialized: {config.server_name} v{config.server_version}")
        logger.info(f"Billing project: {bq_client.billing_project}")
        logger.info(f"Allowed projects: {', '.join(config.get_allowed_projects())}")

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


# Initialize FastMCP server
mcp = FastMCP("BigQuery MCP Server")


def handle_error(func):
    """Decorator to handle errors consistently across tools.

    This decorator wraps tool functions to catch and format errors appropriately.
    It uses functools.wraps to preserve the original function's metadata,
    which is critical for FastMCP to properly introspect function signatures.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BigQueryMCPError as e:
            logger.error(f"MCP Error in {func.__name__}: {e}")
            return formatter.format_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return formatter.format_error(e)

    return wrapper


def main():
    """Main entry point."""
    try:
        # Initialize server components
        initialize_server()

        # Import and register tools
        import tools.analysis
        import tools.discovery
        import tools.execution

        tools.discovery.register_discovery_tools(mcp, handle_error, bq_client, config, formatter)
        tools.analysis.register_analysis_tools(mcp, handle_error, bq_client, config, formatter)
        tools.execution.register_execution_tools(mcp, handle_error, bq_client, config, formatter)

        # Log tool registration completion
        logger.info("All tools registered successfully")

        # Run the MCP server
        logger.info("Starting BigQuery MCP server...")
        mcp.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
