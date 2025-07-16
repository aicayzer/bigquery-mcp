"""Main server entry point for BigQuery MCP."""

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
from config import get_config
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


def initialize_server():
    """Initialize server components."""
    global config, bq_client, formatter

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()

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
        import tools.context
        import tools.development
        import tools.discovery
        import tools.execution

        tools.discovery.register_discovery_tools(mcp, handle_error, bq_client, config, formatter)
        tools.analysis.register_analysis_tools(mcp, handle_error, bq_client, config, formatter)
        tools.execution.register_execution_tools(mcp, handle_error, bq_client, config, formatter)
        tools.development.register_development_tools(
            mcp, handle_error, bq_client, config, formatter
        )
        tools.context.register_context_tools(mcp, bq_client)

        # Verify tool registration
        registered_tools = [tool.name for tool in mcp.tools]
        logger.info(f"Registered {len(registered_tools)} tools: {', '.join(registered_tools)}")

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
