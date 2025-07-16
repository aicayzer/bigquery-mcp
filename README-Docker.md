# Docker Setup

## Configuration Templates

This repository includes template files for Docker configuration:

- `docker-compose.yml.example` - Template for production Docker Compose setup
- `docker-compose.dev.yml.example` - Template for development Docker Compose setup

## Setup Instructions

1. Copy the template files to create your local configuration:
   ```bash
   cp docker-compose.yml.example docker-compose.yml
   cp docker-compose.dev.yml.example docker-compose.dev.yml
   ```

2. Edit the files to replace placeholder values with your actual project IDs:
   - Replace `your-project-id` with your actual BigQuery project ID
   - Replace `your-billing-project` with your billing project ID
   - Update dataset patterns as needed

3. The actual `docker-compose.yml` and `docker-compose.dev.yml` files are in `.gitignore` to prevent committing personal project information.

## CLI vs Config File

- **CLI approach (recommended)**: Use `docker-compose.yml` with command-line arguments
- **Config file approach (deprecated)**: Use `docker-compose.yml` with config files

Both approaches are supported for backward compatibility. 