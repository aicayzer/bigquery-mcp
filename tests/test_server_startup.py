#!/usr/bin/env python3
"""Simple test to verify server can start without errors."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import initialize_server, mcp, get_server_info, health_check
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
        tools.discovery.register_discovery_tools(mcp, health_check.__wrapped__, 
                                               globals()['bq_client'], 
                                               globals()['config'], 
                                               globals()['formatter'])
        print("   ✓ Discovery tools registered")
        
        # Test server info
        print("\n3. Testing get_server_info()...")
        info = get_server_info()
        print(f"   ✓ Server: {info['server']['name']} v{info['server']['version']}")
        print(f"   ✓ Billing Project: {info['server']['billing_project']}")
        
        # Test health check
        print("\n4. Testing health_check()...")
        health = health_check()
        print(f"   ✓ Status: {health['status']}")
        
        print("\n" + "="*50)
        print("✅ Server startup successful!")
        print("\nThe server is ready to be added to Claude Desktop.")
        print("\nTools available:")
        print("  - get_server_info")
        print("  - health_check") 
        print("  - list_projects")
        print("  - list_datasets")
        print("  - list_tables")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_server_startup()
    sys.exit(0 if success else 1)
