# BigQuery MCP Server v1.1.0 - What's New and How to Test

## Overview

Version 1.1.0 resolves critical MCP agent compatibility issues that were causing parameter validation errors and tool execution failures.

## Key Fixes in v1.1.0

### ✅ Parameter Type Validation Fixed
**Problem**: Agents got errors like `"max_rows must be integer"` when passing string values
**Solution**: Automatic string-to-integer conversion for numeric parameters
**Test**: Try passing `max_rows="10"` (string) instead of `max_rows=10` (integer)

### ✅ analyze_columns Reliability Improved  
**Problem**: Random failures with `"No result received from client-side tool execution"`
**Solution**: Added SAFE.* functions and 60-second timeouts
**Test**: Run `analyze_columns` multiple times - should work consistently

### ✅ JSON/Array Display Fixed
**Problem**: `"Array cannot have a null element"` errors in results
**Solution**: Enhanced JSON serialization with NULL filtering
**Test**: Query tables with JSON/Array columns - should display properly

### ✅ Context Management Added
**Problem**: Had to repeatedly specify full table paths
**Solution**: New context tools and automatic tracking
**Test**: Try `get_current_context()` and `list_accessible_projects()`

### ✅ Better Error Messages
**Problem**: Generic errors that didn't help agents
**Solution**: Specific, actionable error messages
**Test**: Try intentional errors - should get helpful guidance

## Development Environment

For testing the latest changes, use the development MCP server:

```bash
# Set up development environment
./setup-dev.sh

# Start development server  
docker-compose -f docker-compose.dev.yml up -d
```

This gives you a separate "BigQuery Development MCP" server alongside your production one.

## Quick Validation Tests

### 1. Parameter Type Conversion
```python
# These should now work (previously failed):
execute_query(query="SELECT 1", max_rows="10", timeout="30")
analyze_columns(table="project.dataset.table", sample_size="1000")
```

### 2. Context Management
```python
# New tools available:
get_current_context()
list_accessible_projects()
```

### 3. Reliability Testing
```python
# Run this multiple times - should be consistent:
analyze_columns(table="your_table", columns="numeric_col,string_col")
```

## Migration Notes

- **Backward Compatible**: All existing functionality preserved
- **No Breaking Changes**: Existing integrations continue to work
- **Enhanced Reliability**: Better error handling and automatic type conversion
- **New Features**: Context management tools available

The BigQuery MCP Server v1.1.0 should now work seamlessly with AI agents without the parameter validation and execution issues of previous versions.
