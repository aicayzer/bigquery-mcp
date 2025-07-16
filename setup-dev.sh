#!/bin/bash

# BigQuery MCP Development Environment Setup
# This script sets up a proper development MCP server instance

set -e

echo "🔧 BigQuery MCP Development Environment Setup"
echo "=============================================="

# Check if required files exist
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "❌ docker-compose.dev.yml not found"
    exit 1
fi

if [ ! -f "config/config.dev.yaml" ]; then
    echo "❌ config/config.dev.yaml not found"
    exit 1
fi

# Check if development config is properly configured
echo "📋 Checking development configuration..."

# Check if billing project is configured
if grep -q "your-billing-project" config/config.dev.yaml; then
    echo "⚠️  WARNING: config/config.dev.yaml still contains placeholder values"
    echo "   Please edit config/config.dev.yaml with your actual project details"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please configure config/config.dev.yaml first."
        exit 1
    fi
fi

# Check for Google Cloud authentication
echo "🔐 Checking Google Cloud authentication..."

if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ Using service account: $GOOGLE_APPLICATION_CREDENTIALS"
elif gcloud auth application-default print-access-token > /dev/null 2>&1; then
    echo "✅ Using Application Default Credentials"
else
    echo "❌ No Google Cloud authentication found"
    echo "Please run: gcloud auth application-default login"
    echo "Or set GOOGLE_APPLICATION_CREDENTIALS environment variable"
    exit 1
fi

# Build the development Docker image
echo "📦 Building development Docker image..."
docker-compose -f docker-compose.dev.yml build

# Check if the production MCP server is running
if docker ps | grep -q "bigquery-mcp-server"; then
    echo "ℹ️  Production MCP server is running (this is fine)"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🚀 Usage Instructions:"
echo "======================"
echo ""
echo "1. Start development server:"
echo "   docker-compose -f docker-compose.dev.yml up -d"
echo ""
echo "2. View logs:"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "3. Stop development server:"
echo "   docker-compose -f docker-compose.dev.yml down"
echo ""
echo "4. Add to your MCP client (Claude Desktop, Cursor, etc.):"
echo ""
echo "   For Claude Desktop (.claude_desktop_config.json):"
echo '   {'
echo '     "mcpServers": {'
echo '       "bigquery-dev": {'
echo '         "command": "docker",'
echo '         "args": ['
echo '           "exec", "-i", "bigquery-mcp-dev-server",'
echo '           "python", "/app/src/server.py"'
echo '         ]'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "📝 Configuration:"
echo "- Server Name: BigQuery Development MCP"
echo "- Container: bigquery-mcp-dev-server"
echo "- Config: config/config.dev.yaml"
echo "- Debug logging enabled"
echo ""
echo "🎯 This gives you:"
echo "- Separate development server alongside production"
echo "- Debug logging and verbose output"
echo "- Independent configuration"
echo "- Easy testing of latest changes"
echo ""
