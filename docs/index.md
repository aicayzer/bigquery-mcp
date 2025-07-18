# BigQuery MCP Server

MCP server for secure BigQuery access across multiple Google Cloud projects.

## Overview

The BigQuery MCP Server provides secure access to Google BigQuery datasets through the Model Context Protocol (MCP). Query across projects, analyze data, and execute queries with built-in safety controls.

## Features

- **Multi-Project Access** - Query across BigQuery projects with pattern matching
- **Advanced Analytics** - Column analysis, data quality checks, schema exploration
- **Security Controls** - SQL validation, query limits, read-only operations
- **CLI Configuration** - Command-line arguments with config file fallback
- **Docker Support** - Containerized deployment for easy integration

## Quick Start

Choose your setup method:

- **[Installation Guide](installation.md)** - Install and configure the server
- **[AI Setup Assistant](ai-setup.md)** - Interactive setup with ChatGPT
- **[Client Setup](setup.md)** - Manual configuration for different clients

## Tools

- **`list_projects()`** - List configured BigQuery projects
- **`list_datasets(project)`** - List datasets in a project  
- **`list_tables(dataset, table_type)`** - List tables in a dataset
- **`analyze_table(table)`** - Get table structure and statistics
- **`analyze_columns(table, columns, sample_size)`** - Deep column analysis
- **`execute_query(query, format, limit, timeout)`** - Execute SELECT queries

## Configuration

Configure via CLI arguments or config files:

- **CLI Arguments** - Direct command-line configuration
- **Config Files** - YAML-based configuration for complex setups
- **Environment Variables** - Override settings via environment

See the [Configuration Guide](configuration.md) for detailed options.

## Documentation

- **[Tools Reference](tools.md)** - Complete API documentation
- **[GitHub Repository](https://github.com/aicayzer/bigquery-mcp)** - Source code and contributions

## License

MIT License
