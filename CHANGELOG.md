# Changelog

All notable changes to the BigQuery MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
