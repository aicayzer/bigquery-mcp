# Changelog

All notable changes to the BigQuery MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2025-01-07

### Fixed
- Fixed all failing unit tests (42 tests now passing)
- Corrected analyze_table test calls by removing deprecated sample_size parameter
- Fixed analyze_columns test calls by changing list parameters to comma-separated strings
- Updated error message assertions to match actual implementation
- Fixed mock configurations for datetime arithmetic operations
- Fixed mock configurations for subscript access in query results
- Resolved integration test config file path issues
- Fixed pytest warnings about test functions returning values instead of using assertions

### Changed
- Reorganized test structure by moving server tests to integration folder
- Improved test coverage to 65% total coverage
- Enhanced mock configurations for better test reliability

## [0.4.7] - 2025-01-07

### Fixed
- Fixed analyze_columns parameter validation issue by changing `columns` from Optional[List[str]] to string (comma-separated)
- Replaced TABLESAMPLE with RAND()-based sampling to fix STRING column analysis errors
- Fixed broken test imports (removed references to non-existent functions: get_server_info, health_check, validate_query, get_query_history)
- Moved debug_timeout.py to test fixtures directory

### Changed
- Updated sampling method from TABLESAMPLE SYSTEM to WHERE RAND() < ratio for better compatibility
- Simplified analyze_columns parameter handling for better FastMCP compatibility
- analysis_method in response now shows 'RANDOM_SAMPLING' instead of 'TABLESAMPLE'

## [0.4.6] - 2025-01-07

### Fixed
- Fixed import path for FastMCP - changed from `mcp.server.fastmcp` to `fastmcp`
- Improved error handling in execute_query to avoid false timeout errors
- Fixed error message logic that was incorrectly catching any error containing "timeout"

### Changed
- Updated README to reflect correct analyze_columns parameters

### Removed
- Removed outdated test_server_startup.py that referenced non-existent functions

## [0.4.5] - 2025-01-07

### Fixed
- Fixed TABLESAMPLE syntax in `analyze_columns` - now uses PERCENT instead of ROWS
- Fixed query execution timeout by properly passing timeout to result() method
- Fixed timeout handling in BigQuery client - removed incorrect timeout parameter from query() method
- Updated dependencies - added `fastmcp>=0.1.0` to requirements.txt

### Changed 
- Simplified `analyze_table` output:
  - Removed `sample_info` section (function analyzes full table schema)
  - Removed `mode` field from column info (redundant with nullable)
  - Removed `classification` object (overcomplicated)
  - Removed `null_percentage` field (redundant given null_count)
  - Removed `sample_values` from analyze_table (use analyze_columns for sampling)
- analyze_table no longer accepts sample_size parameter

### Removed
- Deleted legacy test files: `test_v3_server.py`, `test_v4_server.py`
- Cleaned up old development notes files

## [0.4.4] - 2025-07-06

### Fixed
- Fixed SQL generation bug in `analyze_columns` for string columns
  - Removed problematic LEFT JOIN USING clause
  - Simplified query structure to avoid JOIN errors
  - String column analysis now works correctly

### Changed
- Compact mode now properly enabled via COMPACT_FORMAT environment variable
  - Output is more concise when enabled
  - Reduces verbosity for better readability

### Removed
- Removed `validate_query()` tool - redundant with `execute_query(dry_run=True)`
  - Dry run functionality provides same validation capabilities
  - Simplifies API surface

## [0.4.3] - 2025-07-06

### Fixed
- Fixed BigQuery client location/region configuration
  - Added location property to BigQuery client initialization
  - Location now configurable via config.yaml (defaults to EU)
  - Fixed INFORMATION_SCHEMA queries by using proper region qualifier
- Fixed SQL generation bug in `analyze_columns` tool
  - Simplified complex queries to avoid JOIN issues
  - Improved TABLESAMPLE usage for better performance
- Fixed query timeout configuration
  - Timeout now properly configurable per tool
  - Default timeout applied from configuration

### Changed
- Standardized parameter names across all tools:
  - `dataset_path` → `dataset` in `list_tables()`
  - `table_path` → `table` in `analyze_table()` and `analyze_columns()`
- Moved development tools to separate module:
  - `get_server_info()` and `health_check()` moved to `tools/development.py`
  - Development tools disabled by default (set `DEVELOPMENT_TOOLS_ENABLED = True` to enable)
  - These tools are for debugging only and should not be used in production

### Removed
- Removed `get_query_history()` tool - not essential for core functionality
- Deleted unnecessary files:
  - `src/utils/mcp_adapter.py.bak` - backup from failed v0.4.1 approach
  - `test_fastmcp.py` - debugging artifact
  - `run_test.sh` - debugging artifact

### Configuration
- Added `location` setting to bigquery configuration section
- Default location is now EU (was US)
- Location can be overridden via `BIGQUERY_LOCATION` environment variable

## [0.4.2] - 2025-07-06

### Fixed
- Properly fixed parameter handling by removing unnecessary `mcp_tool_adapter`
- Let FastMCP handle all MCP protocol translation as designed
- All 10 tools now work correctly with proper parameter passing

### Changed
- Simplified tool registration to use only `@mcp.tool()` and `@handle_error` decorators
- Updated all tool registration functions to remove adapter parameter
- Tools are now registered as `mcp.tool()(handle_error(function))`

### Removed
- Removed `utils/mcp_adapter.py` - it was interfering with FastMCP's built-in protocol handling
- Removed all references to `mcp_tool_adapter` from codebase

### Developer Notes
- FastMCP already handles translation from MCP protocol to function calls
- Adding our own parameter translation layer was the root cause of the issue
- The `handle_error` decorator properly preserves function signatures using `functools.wraps`

## [0.4.1] - 2025-07-06 [YANKED]

### Fixed
- Attempted to fix parameter mismatch issue with custom MCP adapter (incorrect approach)

### Added
- `utils/mcp_adapter.py` - MCP protocol adapter (removed in v0.4.2)

### Note
- This version was based on a misunderstanding of how FastMCP works
- The custom adapter interfered with FastMCP's built-in protocol handling
- Version 0.4.2 properly fixes the issue

## [0.4.0] - 2025-01-05

### Added
- Query execution tools implementation:
  - `execute_query()` - Execute SELECT queries with safety validation
  - `validate_query()` - Validate query syntax and estimate costs without execution
  - `get_query_history()` - Retrieve recent query history from INFORMATION_SCHEMA
- SQL safety validation with configurable banned keywords
- Multiple output formats (JSON, CSV, table)
- Query result serialization for complex BigQuery types
- Parameterized query support
- Dry run capability for cost estimation
- Automatic LIMIT injection for safety
- Query timeout and byte limit enforcement
- Cache hit detection and slot usage reporting

### Security
- Enforced SELECT-only queries
- Configurable banned SQL keywords
- Maximum bytes billed limit
- Required LIMIT clause option

## [0.3.0] - 2025-01-05

### Added
- Analysis tools implementation:
  - `analyze_table()` - Comprehensive table structure and statistics analysis
  - `analyze_columns()` - Deep column profiling with null and cardinality analysis
- Column classification system (identifier, measure, categorical, temporal, etc.)
- Statistical analysis for numeric columns (min, max, avg, stddev, quartiles)
- String pattern analysis with length statistics
- Temporal data range analysis
- Data quality indicators (completeness, uniqueness)
- Top value frequency analysis for categorical columns
- Efficient sampling using TABLESAMPLE for large tables
- Smart column categorization based on name patterns and data characteristics

### Fixed
- Config file path resolution for Claude Desktop compatibility
- Working directory issues when run from different locations

## [0.2.0] - 2025-01-06

### Added
- Discovery tools implementation:
  - `list_projects()` - List accessible BigQuery projects with metadata
  - `list_datasets()` - List datasets with pattern filtering support
  - `list_tables()` - List tables with type filtering (TABLE, VIEW, MATERIALIZED_VIEW)
- Response formatting modes (standard and compact) for all tools
- Comprehensive unit tests for discovery tools
- Integration tests with mocked BigQuery client
- Tool registration in FastMCP server
- sqlparse dependency for SQL validation

### Changed
- Updated server.py to import and register discovery tools
- Enhanced error messages with actionable suggestions

## [0.1.0] - 2025-01-06

### Added
- Initial project structure
- Basic documentation (README, CLAUDE guidelines)
- Development environment setup
- Core infrastructure implementation:
  - Configuration management with YAML support and environment overrides
  - BigQuery client with cross-project support and validation
  - SQL validation utilities for query safety
  - Response formatting for standard and compact modes
  - FastMCP server initialization with error handling
  - Comprehensive logging setup
- Testing infrastructure with pytest
- CI/CD pipeline with GitHub Actions
- Docker configuration for deployment
- Custom error classes for better error handling

## Versions

<!-- 
Version template:

## [0.x.y] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features
-->
