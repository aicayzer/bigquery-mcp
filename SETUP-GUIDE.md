# BigQuery MCP Quick Setup - Other Mac

## 🚀 Simple Setup (Full Access)

### Step 1: Clean Docker
```bash
# Stop and remove old containers/images
docker-compose down --volumes --remove-orphans
docker system prune -f
```

### Step 2: Authenticate with Google Cloud
```bash
# This gives you access to everything your account can access
gcloud auth application-default login
```

### Step 3: Run with CLI (No Config File Needed)
```bash
# Build the image
docker-compose build

# Run with full access to all your projects (replace with your actual project IDs)
docker-compose run --rm bigquery-mcp python src/server.py your-project-1:* your-project-2:*
```

## 🎯 Claude Desktop Configuration

Update your Claude Desktop config with the **absolute path** to your repo:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/logs:/app/logs",
        "--env", "LOG_LEVEL=INFO",
        "--env", "COMPACT_FORMAT=true",
        "bigquery-mcp:latest",
        "your-project-1:*",
        "your-project-2:*"
      ]
    }
  }
}
```

**Replace:**
- `YOUR_USERNAME` with your macOS username
- `/ABSOLUTE/PATH/TO/bigquery-mcp` with the full path to your repo
- `your-project-1:*` and `your-project-2:*` with your actual project IDs

## 🧪 Test It Works

```bash
# Test the server starts
docker-compose run --rm bigquery-mcp python src/server.py your-project-1:* --version

# Test basic functionality
docker-compose run --rm bigquery-mcp python src/server.py your-project-1:* your-project-2:*
```

Then restart Claude Desktop and test: "List all my BigQuery projects"

---

## Alternative: Config File Method (If You Prefer)

If you prefer using a config file instead of CLI arguments:

### Step 1: Create config file
```bash
cp config/config.yaml.example config/config.yaml
```

### Step 2: Edit config for full access
```yaml
server:
  name: "BigQuery MCP Server"
  version: "1.1.0"

bigquery:
  billing_project: "your-billing-project-id"
  location: "US"

# For full access, leave projects empty OR use this:
projects:
  - project_id: "your-project-1"
    project_name: "Project 1"
    datasets: ["*"]  # * means all datasets
  - project_id: "your-project-2"
    project_name: "Project 2"
    datasets: ["*"]
```

### Step 3: Run with config
```bash
docker-compose run --rm bigquery-mcp
```

Claude Desktop config (without CLI args):
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/config:/app/config:ro",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/logs:/app/logs",
        "bigquery-mcp:latest"
      ]
    }
  }
}
``` 