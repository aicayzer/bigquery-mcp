# Installation Guide

This guide covers different ways to install and deploy the BigQuery MCP Server.

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 512MB RAM
- **Network**: Internet access for BigQuery API calls

### Google Cloud Requirements

- Google Cloud Project with BigQuery enabled
- BigQuery datasets you want to access
- Appropriate IAM permissions (see [Permissions](#permissions) below)

## Installation Methods

### Method 1: Local Python Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aicayzer/bigquery-mcp.git
   cd bigquery-mcp
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python src/server.py --help
   ```

### Method 2: Docker Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aicayzer/bigquery-mcp.git
   cd bigquery-mcp
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Or build manually:**
   ```bash
   docker build -t bigquery-mcp .
   docker run --rm bigquery-mcp python --version
   ```

## Authentication Setup

### Option 1: Application Default Credentials (Recommended)

This is the easiest method for development:

```bash
# Install Google Cloud SDK if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate with your Google account
gcloud auth application-default login

# Set your default project (optional)
gcloud config set project your-project-id
```

### Option 2: Service Account Key

For production deployments:

1. **Create a service account:**
   ```bash
   gcloud iam service-accounts create bigquery-mcp-server \
     --display-name="BigQuery MCP Server"
   ```

2. **Grant necessary permissions:**
   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:bigquery-mcp-server@your-project-id.iam.gserviceaccount.com" \
     --role="roles/bigquery.user"
   ```

3. **Create and download key:**
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=bigquery-mcp-server@your-project-id.iam.gserviceaccount.com
   ```

4. **Set environment variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

## Configuration

### Basic Configuration

1. **Copy the example configuration:**
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

2. **Edit the configuration file:**
   ```yaml
   server:
     name: "BigQuery MCP Server"
     version: "1.1.0"

   bigquery:
     billing_project: "your-billing-project"
     location: "US"  # or "EU", "asia-northeast1", etc.

   projects:
     - project_id: "your-data-project"
       project_name: "My Data Project"
       description: "Main data warehouse"
       datasets: ["dataset1", "dataset2_*"]  # Specific or wildcard patterns
   ```

3. **Set environment variables (optional):**
   ```bash
   export BIGQUERY_BILLING_PROJECT=your-billing-project
   export LOG_LEVEL=INFO
   export COMPACT_FORMAT=true
   ```

### Docker Configuration

For Docker deployments, mount your configuration and credentials:

```bash
docker run -d \
  --name bigquery-mcp \
  -v $(pwd)/config:/app/config:ro \
  -v ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
  -e BIGQUERY_BILLING_PROJECT=your-billing-project \
  bigquery-mcp
```

## Permissions

### Required BigQuery IAM Roles

The service account or user needs these minimum permissions:

- **`roles/bigquery.user`** - Basic BigQuery access
- **`roles/bigquery.dataViewer`** - Read access to datasets/tables
- **`roles/bigquery.jobUser`** - Create and run queries

### Custom Role (Recommended)

For tighter security, create a custom role:

```bash
gcloud iam roles create bigqueryMcpServer \
  --project=your-project-id \
  --title="BigQuery MCP Server" \
  --description="Minimal permissions for BigQuery MCP Server" \
  --permissions="bigquery.datasets.get,bigquery.tables.list,bigquery.tables.get,bigquery.tables.getData,bigquery.jobs.create"
```

## Verification

### Test Local Installation

```bash
# Test server startup
python src/server.py &
SERVER_PID=$!

# Test basic functionality (requires additional MCP client setup)
# Kill the test server
kill $SERVER_PID
```

### Test Docker Installation

```bash
# Test container
docker run --rm bigquery-mcp python -c "import src.server; print('OK')"
```

### Test BigQuery Access

```bash
# Test gcloud access
gcloud auth list
gcloud config list project

# Test BigQuery access
bq ls  # Should list your datasets
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Could not automatically determine credentials
```
**Solution:** Run `gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS`

#### Permission Denied
```
403 Forbidden: Access Denied
```
**Solution:** Check IAM permissions and ensure the service account has BigQuery access

#### Project Not Found
```
404 Not Found: Project not found
```
**Solution:** Verify project ID in configuration and ensure billing is enabled

#### Docker Permission Issues
```
Permission denied: /home/mcpuser/.config/gcloud
```
**Solution:** Check volume mount permissions:
```bash
chmod -R 755 ~/.config/gcloud
```

### Getting Help

If you encounter issues:

1. Check the `logs/` directory in your project root for detailed error messages
2. Verify your configuration matches the [examples](configuration.md)
3. Test BigQuery access independently with `gcloud` or `bq` commands
4. Review the setup guide for debugging tips

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Tools Reference](tools.md) - Available MCP tools and examples
- [Client Setup Guide](setup.md) - Claude Desktop and Cursor setup