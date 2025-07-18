# Changelog

All notable changes to the BigQuery MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-07-18

### Fixed
- Race condition in tool registration causing intermittent "No server found with tool" errors
- Improved initialization validation to prevent global variable timing issues

### Changed
- Cleaned up informal comments throughout codebase for better code quality

## [1.1.1] - 2025-07-17

### Added
- 20-second default timeout (reduced from 60 seconds) with configurable `--timeout` CLI argument
- Clean configuration structure with proper .example files and gitignored personal configs
- Comprehensive CLI arguments for all configuration options with proper precedence (CLI > Config > Env > Defaults)
- Enterprise pattern system supporting multiple projects with dataset patterns
- AI-friendly error messages with source classification and actionable suggestions

### Fixed
- Runtime crashes from missing `log_results` attribute in Config class
- Error handling bugs in QueryExecutionError constructor
- Configuration inconsistencies between config files and examples
- Version management removed from config files (now code-only)
- Configuration file structure inconsistencies
- Docker setup confusion - simplified to single service architecture
- Broken documentation links and outdated examples

### Changed
- Simplified Docker setup to single `bigquery-mcp` service
- Moved setup guide from root to docs/setup.md
- Updated README to be more concise and to-the-point
- Cleaned up repository structure - removed redundant files

## [1.1.0] - 2025-07-16

### Added
- CLI argument support for project configuration with `project:dataset` patterns
- Query complexity estimation and execution time tracking
- Comprehensive parameter documentation

### Fixed
- Parameter type validation errors for MCP protocol compatibility
- analyze_columns intermittent failures with enhanced NULL handling
- Complex data type serialization issues
- Parameter naming inconsistencies across configuration files

### Changed
- Consolidated validation logic into SQLValidator class
- Improved tool registration with enhanced debugging

### Removed
- Duplicate and redundant tools for cleaner architecture

## [1.0.0] - 2025-07-10

### Added
- MkDocs documentation site with Material theme
- GitHub Actions workflow for automatic documentation deployment
- Comprehensive Claude Desktop setup guide with Docker and Python options
- MIT license

### Changed
- Migrated from scattered markdown files to organized MkDocs documentation
- Converted from Poetry to pip-native package configuration in pyproject.toml
- Updated dependencies: added mkdocs and mkdocs-material, removed mypy and types-PyYAML
- Organized setup guides under dedicated navigation section

### Fixed
- Removed all workplace-specific references from tracked files
- Fixed test mocks for execute_query function
- Fixed unused variable linting issues in analysis.py (removed 8 F841 errors)
- Updated all version references to 1.0.0
- Corrected development guide to reference ruff instead of deprecated tools

### Removed
- Poetry configuration and dependencies (now pip-native)
- Unused lint scripts and development artifacts

## [0.5.2] - 2025-07-09

### Fixed
- Fixed execute_query function returning empty results
- Cleaned up debug logging from previous debugging attempts
- Improved schema handling for query results

## [0.5.1] - 2025-07-09

### Fixed
- Fixed execute_query NoneType error when iterating query results
  - query_job.result() returns a RowIterator that we iterate over
  - Added defensive None check for edge cases
  - Manual row limiting applied during iteration
  - Prevents "'NoneType' object is not iterable" error

### Added
- Docker MCP integration for Cursor IDE
  - Complete Docker configuration for MCP server deployment
  - Cursor-specific setup documentation with step-by-step instructions
  - Proper Google Cloud authentication handling in containers

### Changed
- Migrated from black/flake8 to ruff for code formatting and linting
  - Updated pyproject.toml with ruff configuration
  - Removed legacy black and flake8 configurations
  - Updated GitHub Actions CI workflow to use ruff
  - Removed mypy from CI pipeline (type checking deferred)
- Improved code quality:
  - Fixed all ruff linting issues
  - Removed unused variables and imports
  - Updated lint script to use ruff exclusively

### Removed
- Cleaned up accidentally added directories:
  - Removed `/genai-toolbox/` (unrelated Go project)
  - Removed `/servers/` (unrelated TypeScript project)
  - Already added to .gitignore to prevent re-addition
- Legacy linting tools:
  - Removed black and flake8 configurations
  - Removed mypy from GitHub Actions workflow

## [0.5.0] - 2025-01-07

### Added
- Docker support with multi-stage build for production deployment
- Docker Compose configuration for easy local development
- GitHub Actions workflow for automatic releases on main branch
- Scripts directory with lint.sh for local code quality checks
- Comprehensive documentation in docs/ folder:
  - architecture.md - System design and specification
  - tools.md - Detailed tool reference with examples

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
- Simplified README to focus on quick start, moved details to docs/
- Updated all version references to 0.5.0

### Removed
- TESTING.md (content integrated into README)

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
