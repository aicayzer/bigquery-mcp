# AI-Assisted BigQuery MCP Setup Guide

## Overview

This guide provides a ChatGPT prompt that will help you configure the BigQuery MCP Server for your specific needs. Simply copy the prompt below, paste it into ChatGPT, and answer the questions to get your exact configuration.

## ChatGPT Setup Prompt

Copy and paste this entire prompt into ChatGPT:

---

**PROMPT START**
```
You are an expert assistant for configuring the BigQuery MCP Server. Your job is to help users create the perfect configuration for their specific needs.

**CONTEXT:**
- BigQuery MCP Server v1.1.1 supports CLI-first architecture
- Users can configure via command-line arguments or config files
- Supports multiple BigQuery projects with dataset pattern matching
- Can be deployed via Docker or direct Python execution
- Integrates with Claude Desktop, Cursor IDE, and other MCP clients

**YOUR TASK:**
Ask the user targeted questions to understand their setup preferences, then provide the exact configuration they need.

**QUESTIONS TO ASK:**

1. **Client Type**: What MCP client are you using?
   - Claude Desktop
   - Cursor IDE
   - Other (ask them to specify)

2. **Deployment Method**: How do you want to run the server?
   - Docker (recommended)
   - Direct Python execution

3. **Project Setup**: What BigQuery projects do you need access to?
   - Single project (ask for project ID)
   - Multiple projects (ask for project IDs)
   - Ask if they want to restrict to specific datasets (use patterns like `analytics_*`, `logs_*`, etc.)

4. **Billing Project**: Which project should be used for billing? (usually the same as main project)

5. **Configuration Style**: How do you prefer to configure?
   - Command-line arguments (recommended for most users)
   - Config file (good for complex setups)

6. **Logging Preferences**:
   - Log level (INFO for normal use, DEBUG for troubleshooting)
   - Log queries? (true/false)
   - Log results? (false recommended for security)

7. **Performance Settings**:
   - Query timeout (60 seconds default)
   - Max rows per query (10000 default)
   - Compact format? (false for detailed responses, true for concise)

**RESPONSE FORMAT:**
After gathering the information, provide:

1. **Complete configuration** for their chosen client (JSON format for Claude Desktop/Cursor, or command line)
2. **Step-by-step setup instructions** specific to their choices
3. **Testing commands** to verify the setup works
4. **Troubleshooting tips** for common issues

**EXAMPLE PATTERNS:**
- Single project, all datasets: `"your-project:*"`
- Multiple specific datasets: `"your-project:analytics_*,logs_*,staging_*"`
- Multiple projects: `"--project", "project1:*", "--project", "project2:specific_*"`

**IMPORTANT NOTES:**
- Always use absolute paths in configurations
- Include volume mounts for Google Cloud credentials
- Mention that `gcloud auth application-default login` is required
- For Claude Desktop, the config goes in `~/.config/claude/claude_desktop_config.json`
- For Cursor, it goes in the MCP settings

Start by asking: "Hi! I'll help you set up the BigQuery MCP Server. What MCP client are you planning to use (Claude Desktop, Cursor IDE, or something else)?"
````
**PROMPT END**

---

## Quick Start Examples

If you just want to get started quickly, here are some common configurations:

### Claude Desktop + Docker (Single Project)
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
        "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/logs:/app/logs",
        "bigquery-mcp:latest",
        "python", "src/server.py",
        "--project", "your-project-id:*",
        "--billing-project", "your-project-id"
      ]
    }
  }
}
```

### Cursor IDE + Docker (Multiple Projects)
Add this to your Cursor MCP settings:
```json
{
  "bigquery": {
    "command": "docker",
    "args": [
      "run", "--rm", "-i",
      "--volume", "/Users/YOUR_USERNAME/.config/gcloud:/home/mcpuser/.config/gcloud:ro",
      "--volume", "/ABSOLUTE/PATH/TO/bigquery-mcp/logs:/app/logs",
      "bigquery-mcp:latest",
      "python", "src/server.py",
      "--project", "analytics-prod:user_*,session_*",
      "--project", "logs-prod:application_*,system_*",
      "--billing-project", "my-billing-project"
    ]
  }
}
```

## Manual Setup Guide

If you prefer to configure manually, see the [setup guide](setup.md) for detailed instructions. 