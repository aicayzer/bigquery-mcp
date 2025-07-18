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
    # Use temporary directory if logs directory creation fails
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
  python src/server.py --project "sandbox-dev:*"
  
  # Multiple projects with specific patterns
  python src/server.py --project "sandbox-dev:dev_*" --project "sandbox-main:main_*"
  
  # Multiple dataset patterns for same project
  python src/server.py --project "cayzer-xyz:demo_*,analytics_*"
  
  # Complex enterprise usage with multiple projects and patterns
  python src/server.py \\
    --project "analytics-prod:user_*,session_*" \\
    --project "logs-prod:application_*,system_*" \\
    --billing-project "my-project" \\
    --log-level INFO
  
  # Use config file if no projects specified
  python src/server.py --config config.yaml
        """,
    )

    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="Project access patterns in format 'project_id:dataset_pattern[:table_pattern]' (e.g., 'sandbox-dev:dev_*'). Can be used multiple times.",
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

    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-queries",
        type=lambda x: x.lower() == "true",
        default=True,
        help="Log queries for audit purposes (default: true)",
    )

    parser.add_argument(
        "--log-results",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Log query results - be careful with sensitive data (default: false)",
    )

    # Query execution limits
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Query timeout in seconds (default: 20)",
    )

    parser.add_argument(
        "--max-limit",
        type=int,
        default=10000,
        help="Maximum rows that can be requested (default: 10000)",
    )

    parser.add_argument(
        "--max-bytes-processed",
        type=int,
        default=1073741824,
        help="Maximum bytes that will be processed for cost control (default: 1073741824 = 1GB)",
    )

    # Response formatting
    parser.add_argument(
        "--compact-format",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Use compact response format (default: false)",
    )

    # Security settings
    parser.add_argument(
        "--select-only",
        type=lambda x: x.lower() == "true",
        default=True,
        help="Allow only SELECT statements (default: true)",
    )

    parser.add_argument(
        "--require-explicit-limits",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Require explicit LIMIT clause in SELECT queries (default: false)",
    )

    parser.add_argument(
        "--banned-keywords",
        default="CREATE,DELETE,DROP,TRUNCATE,ALTER,INSERT,UPDATE",
        help="Comma-separated list of banned SQL keywords (default: CREATE,DELETE,DROP,TRUNCATE,ALTER,INSERT,UPDATE)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="BigQuery MCP Server 1.1.1",
    )

    return parser.parse_args()


def parse_project_patterns(project_args):
    """Parse project:dataset:table patterns from command line arguments.

    Supports formats:
    - project_id:*                              (all datasets)
    - project_id:dataset_pattern                (specific dataset patterns)
    - project_id:dataset_pattern:table_pattern  (dataset and table patterns)
    - project_id:dataset1,dataset2:table1,table2 (multiple patterns)

    Args:
        project_args: List of project pattern strings

    Returns:
        Dict mapping project_id to list of dataset patterns
    """
    projects = {}

    for pattern in project_args:
        if ":" not in pattern:
            logger.error(
                f"Invalid project pattern '{pattern}'. Expected format: 'project_id:dataset_pattern[:table_pattern]'"
            )
            sys.exit(1)

        # Split into components
        parts = pattern.split(":", 2)  # Max 3 parts: project:dataset:table

        if len(parts) < 2:
            logger.error(
                f"Invalid project pattern '{pattern}'. Expected format: 'project_id:dataset_pattern[:table_pattern]'"
            )
            sys.exit(1)

        project_id = parts[0].strip()
        dataset_part = parts[1].strip()
        table_part = parts[2].strip() if len(parts) > 2 else None

        if not project_id or not dataset_part:
            logger.error(
                f"Invalid project pattern '{pattern}'. Both project_id and dataset_pattern are required"
            )
            sys.exit(1)

        # Parse dataset patterns (comma-separated)
        dataset_patterns = [p.strip() for p in dataset_part.split(",") if p.strip()]

        if not dataset_patterns:
            logger.error(f"Invalid project pattern '{pattern}'. Dataset pattern cannot be empty")
            sys.exit(1)

        # Table patterns will be handled in future enhancement
        if table_part:
            logger.warning(
                f"Table patterns not yet fully implemented. Ignoring table pattern '{table_part}' for project '{project_id}'"
            )

        # Add to projects dict
        if project_id not in projects:
            projects[project_id] = []
        projects[project_id].extend(dataset_patterns)

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
                log_level=args.log_level,
                log_queries=args.log_queries,
                log_results=args.log_results,
                timeout=args.timeout,
                max_limit=args.max_limit,
                max_bytes_processed=args.max_bytes_processed,
                compact_format=args.compact_format,
                select_only=args.select_only,
                require_explicit_limits=args.require_explicit_limits,
                banned_keywords=args.banned_keywords,
            )
        else:
            # Use config file
            config = get_config(args.config)

        # Log configuration source for debugging
        config.log_configuration_source()

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
