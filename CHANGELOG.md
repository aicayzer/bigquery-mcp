# Changelog

All notable changes to the BigQuery MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
