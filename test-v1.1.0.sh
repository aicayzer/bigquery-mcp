#!/bin/bash

# BigQuery MCP v1.1.0 Validation Test Script
# This script helps validate the key fixes in v1.1.0

echo "🚀 BigQuery MCP Server v1.1.0 Validation Test"
echo "=============================================="

# Build and start the test environment
echo "📦 Building test environment..."
docker-compose -f docker-compose.test.yml build

echo "🔄 Starting test server..."
docker-compose -f docker-compose.test.yml up -d bigquery-mcp-test

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
sleep 10

# Check if server is running
if ! docker ps | grep -q "bigquery-mcp-v1.1.0-test"; then
    echo "❌ Test server failed to start"
    docker-compose -f docker-compose.test.yml logs bigquery-mcp-test
    exit 1
fi

echo "✅ Test server is running on port 3001"

# Show validation instructions
echo ""
echo "🧪 VALIDATION INSTRUCTIONS"
echo "=========================="
echo ""
echo "The BigQuery MCP Server v1.1.0 is now running for testing."
echo ""
echo "Test the following key fixes:"
echo ""
echo "1. 🔢 Parameter Type Validation:"
echo "   - Try passing string values for max_rows, timeout, sample_size"
echo "   - Should auto-convert without errors"
echo ""
echo "2. 📊 analyze_columns Reliability:"
echo "   - Run analyze_columns multiple times"
echo "   - Should work consistently without timeouts"
echo ""
echo "3. 🗂️ Context Management:"
echo "   - Try: get_current_context()"
echo "   - Try: list_accessible_projects()"
echo ""
echo "4. 📋 Complex Data Types:"
echo "   - Query tables with JSON/Array columns"
echo "   - Results should display properly"
echo ""
echo "5. ❌ Error Message Quality:"
echo "   - Try intentional errors"
echo "   - Should get specific, actionable messages"
echo ""
echo "📖 See VALIDATION_CONTEXT.md for detailed test cases"
echo ""
echo "🔧 Commands:"
echo "  View logs:    docker-compose -f docker-compose.test.yml logs -f"
echo "  Stop server:  docker-compose -f docker-compose.test.yml down"
echo "  Restart:      docker-compose -f docker-compose.test.yml restart"
echo ""
echo "🌐 Server URL: http://localhost:3001"
echo ""

# Optional: Run automated tests if available
if [ "$1" = "--run-tests" ]; then
    echo "🧪 Running automated tests..."
    docker-compose -f docker-compose.test.yml --profile test up test-client
fi

echo "✨ Ready for v1.1.0 validation testing!"
