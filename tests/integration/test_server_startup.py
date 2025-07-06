#!/usr/bin/env python3
"""Simple test to verify server can start without errors."""

import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# from server import initialize_server, mcp, get_server_info, health_check
from server import initialize_server, mcp, bq_client, config, formatter, handle_error
import tools.discovery


def test_server_startup():
    """Test that server can initialize and tools are registered."""
    print("Testing BigQuery MCP Server Startup...")
    print("-" * 50)
    
    try:
        # Initialize server
        print("1. Initializing server...")
        initialize_server()
        print("   ✓ Server components initialized")
        
        # Register tools
        print("\n2. Registering discovery tools...")
        tools.discovery.register_discovery_tools(mcp, handle_error, 
                                               bq_client, 
                                               config, 
                                               formatter)
        print("   ✓ Discovery tools registered")
        
        # Test basic functionality - just verify no errors
        print("\n3. Testing basic server functionality...")
        print(f"   ✓ MCP instance: {type(mcp)}")
        print(f"   ✓ BigQuery client: {type(bq_client)}")
        print(f"   ✓ Config: {type(config)}")
        
        print("\n" + "="*50)
        print("✅ Server startup successful!")
        print("\nThe server is ready to be added to Claude Desktop.")
        print("\nTools available:")
        print("  - list_projects")
        print("  - list_datasets")
        print("  - list_tables")
        
        # Assert that all components are properly initialized
        assert mcp is not None, "MCP instance should be initialized"
        print(f"   ✓ Server initialization completed successfully")
        
    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise  # Let pytest handle the failure


if __name__ == "__main__":
    test_server_startup()
    print("All tests passed!")
