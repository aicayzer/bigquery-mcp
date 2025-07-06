#!/usr/bin/env python3
"""Test v0.4.0 server with all tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_v4_server():
    """Test v0.4.0 server with all tools."""
    print("Testing BigQuery MCP v0.4.0...")
    print("-" * 60)
    
    try:
        # Import server components
        from server import initialize_server, mcp, get_server_info
        import tools.discovery
        import tools.analysis
        import tools.execution
        
        # Initialize server
        print("1. Initializing server...")
        initialize_server()
        print("   ✓ Server initialized")
        
        # Get globals for tool registration
        server_globals = sys.modules['__main__'].__dict__
        
        # Register all tools
        print("\n2. Registering tools...")
        tools.discovery.register_discovery_tools(
            mcp, server_globals['handle_error'],
            server_globals['bq_client'], 
            server_globals['config'], 
            server_globals['formatter']
        )
        print("   ✓ Discovery tools registered (3 tools)")
        
        tools.analysis.register_analysis_tools(
            mcp, server_globals['handle_error'],
            server_globals['bq_client'], 
            server_globals['config'], 
            server_globals['formatter']
        )
        print("   ✓ Analysis tools registered (2 tools)")
        
        tools.execution.register_execution_tools(
            mcp, server_globals['handle_error'],
            server_globals['bq_client'], 
            server_globals['config'], 
            server_globals['formatter']
        )
        print("   ✓ Execution tools registered (3 tools)")
        
        # Test server info
        print("\n3. Server info:")
        info = get_server_info()
        print(f"   Name: {info['server']['name']}")
        print(f"   Version: {info['server']['version']}")
        print(f"   Billing Project: {info['server']['billing_project']}")
        
        print("\n" + "="*60)
        print("✅ BigQuery MCP v0.4.0 ready!")
        print("\nAvailable tools (10 total):")
        print("\n  Server (2):")
        print("    - get_server_info")
        print("    - health_check")
        print("\n  Discovery (3):")
        print("    - list_projects")
        print("    - list_datasets")
        print("    - list_tables")
        print("\n  Analysis (2):")
        print("    - analyze_table")
        print("    - analyze_columns")
        print("\n  Execution (3):")
        print("    - execute_query")
        print("    - validate_query")
        print("    - get_query_history")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Need to set up the main module globals that server.py expects
    import sys
    main_module = sys.modules['__main__']
    main_module.config = None
    main_module.bq_client = None
    main_module.formatter = None
    main_module.handle_error = lambda f: f
    
    success = test_v4_server()
    sys.exit(0 if success else 1)
