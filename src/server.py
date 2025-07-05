"""Main server entry point for BigQuery MCP."""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from config import get_config
from client import BigQueryClient
from utils.errors import BigQueryMCPError
from utils.formatting import ResponseFormatter

# Load environment variables
load_dotenv()

# Configure logging with more robust path handling
log_level = os.getenv('LOG_LEVEL', 'INFO')

# Try to create logs directory, but if it fails, use temp directory
try:
    script_dir = Path(__file__).parent.parent
    logs_dir = script_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / 'bigquery_mcp.log'
except Exception as e:
    # Fallback to temp directory if we can't create logs dir
    import tempfile
    logs_dir = Path(tempfile.gettempdir()) / 'bigquery_mcp_logs'
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / 'bigquery_mcp.log'
    print(f"Warning: Using temp directory for logs: {logs_dir}", file=sys.stderr)

# Configure logging
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Always log to stderr first
        logging.FileHandler(log_file)
    ]
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

# Import and register tools after mcp is created
# This will be done in the next step when we implement the tools


def handle_error(func):
    """Decorator to handle errors consistently across tools."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BigQueryMCPError as e:
            logger.error(f"MCP Error in {func.__name__}: {e}")
            return formatter.format_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return formatter.format_error(e)
    
    # Preserve function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# Server metadata tool
@mcp.tool()
@handle_error
def get_server_info() -> Dict[str, Any]:
    """Get information about the BigQuery MCP server.
    
    Returns server version, configuration, and available features.
    """
    return {
        'status': 'success',
        'server': {
            'name': config.server_name,
            'version': config.server_version,
            'billing_project': bq_client.billing_project,
            'allowed_projects': len(config.projects),
            'features': {
                'cross_project_access': True,
                'column_analysis': True,
                'sql_validation': True,
                'compact_mode': formatter.compact_mode
            }
        }
    }


# Health check tool
@mcp.tool()
@handle_error
def health_check() -> Dict[str, Any]:
    """Check server health and BigQuery connectivity.
    
    Tests configuration and BigQuery access.
    """
    health = {
        'status': 'healthy',
        'checks': {
            'configuration': 'ok',
            'bigquery_client': 'ok',
            'authentication': 'ok'
        }
    }
    
    try:
        # Test BigQuery access by listing datasets in billing project
        datasets = list(bq_client.client.list_datasets(
            bq_client.billing_project,
            max_results=1
        ))
        health['checks']['bigquery_access'] = 'ok'
    except Exception as e:
        health['status'] = 'degraded'
        health['checks']['bigquery_access'] = f'error: {str(e)}'
    
    return health


def main():
    """Main entry point."""
    try:
        # Initialize server components
        initialize_server()
        
        # Import and register tools
        import tools.discovery
        tools.discovery.register_discovery_tools(mcp, handle_error, bq_client, config, formatter)
        # import tools.analysis  # TODO: Implement analysis tools
        # import tools.execution  # TODO: Implement execution tools
        
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
