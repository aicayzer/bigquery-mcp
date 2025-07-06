# BigQuery MCP Server - v0.4.2 Tasks

## Overview
v0.4.2 is a bug fix release that properly fixes the parameter handling issue by removing unnecessary wrapper layers and letting FastMCP handle protocol translation as designed.

## Root Cause Analysis
The v0.4.1 "fix" was based on a misunderstanding. We thought we needed to handle MCP protocol translation ourselves, but FastMCP already does this. By adding our own `mcp_tool_adapter`, we were interfering with FastMCP's proper functioning.

## Tasks for v0.4.2

### 1. Remove mcp_tool_adapter
- [ ] Delete `src/utils/mcp_adapter.py` entirely
- [ ] Remove all imports of `mcp_tool_adapter` from server.py
- [ ] Remove the adapter parameter from all tool registration functions

### 2. Update Tool Registration  
- [ ] In server.py:
  - [ ] Change tool registration to: `mcp.tool()(handle_error(function))`
  - [ ] Remove mcp_adapter parameter from register_*_tools calls
  
- [ ] In tools/discovery.py:
  - [ ] Update function signature to remove mcp_adapter parameter
  - [ ] Change registration to: `mcp.tool()(handle_error(function))`
  
- [ ] In tools/analysis.py:
  - [ ] Update function signature to remove mcp_adapter parameter  
  - [ ] Change registration to: `mcp.tool()(handle_error(function))`
  
- [ ] In tools/execution.py:
  - [ ] Update function signature to remove mcp_adapter parameter
  - [ ] Change registration to: `mcp.tool()(handle_error(function))`

### 3. Verify handle_error Decorator
- [ ] Ensure it uses `@functools.wraps(func)` correctly
- [ ] Verify it preserves function signatures properly
- [ ] Test that FastMCP can introspect wrapped functions

### 4. Add Integration Tests
- [ ] Create tests that verify tool parameter passing works correctly
- [ ] Test tools with no parameters
- [ ] Test tools with optional parameters  
- [ ] Test tools with required parameters
- [ ] Test error handling through the decorator

### 5. Update Documentation
- [ ] Update CHANGELOG.md with v0.4.2 fixes
- [ ] Document the correct way to register tools with FastMCP
- [ ] Add notes about not interfering with FastMCP's protocol handling

## Key Principles
1. **Let FastMCP handle MCP protocol** - Don't try to translate parameters ourselves
2. **Minimal wrapping** - Only wrap for error handling, not protocol translation
3. **Preserve signatures** - Ensure decorators preserve function signatures for FastMCP introspection
4. **Test thoroughly** - Add tests to prevent similar issues in the future

## Expected Outcome
After v0.4.2, all 10 tools should work correctly in Claude Desktop:
- Tools receive their actual parameters (not args/kwargs)
- FastMCP handles all protocol translation
- Error handling still works through the handle_error decorator
- Clean, maintainable code without unnecessary abstractions
