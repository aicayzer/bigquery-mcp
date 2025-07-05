#!/usr/bin/env python3
"""Quick test to verify v0.3.0 server starts properly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_v3_server():
    """Test v0.3.0 server with analysis tools."""
    print("Testing BigQuery MCP v0.3.0...")
    print("-" * 50)
    
    try:
        # Import server components
        from server import initialize_server, mcp, get_server_info, health_check
        import tools.discovery
        import tools.analysis
        
        # Initialize server
        print("1. Initializing server...")
        initialize_server()
        print("   ✓ Server initialized")
        
        # Register tools
        print("\n2. Registering tools...")
        tools.discovery.register_discovery_tools(
            mcp, health_check.__wrapped__, 
            globals()['bq_client'], 
            globals()['config'], 
            globals()['formatter']
        )
        print("   ✓ Discovery tools registered")
        
        tools.analysis.register_analysis_tools(
            mcp, health_check.__wrapped__,
            globals()['bq_client'], 
            globals()['config'], 
            globals()['formatter']
        )
        print("   ✓ Analysis tools registered")
        
        # Test server info
        print("\n3. Server info:")
        info = get_server_info()
        print(f"   Name: {info['server']['name']}")
        print(f"   Version: {info['server']['version']}")
        print(f"   Billing Project: {info['server']['billing_project']}")
        
        print("\n" + "="*50)
        print("✅ BigQuery MCP v0.3.0 ready!")
        print("\nAvailable tools:")
        print("  Discovery:")
        print("    - list_projects")
        print("    - list_datasets")
        print("    - list_tables")
        print("  Analysis:")
        print("    - analyze_table")
        print("    - analyze_columns")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_v3_server()
    sys.exit(0 if success else 1)
