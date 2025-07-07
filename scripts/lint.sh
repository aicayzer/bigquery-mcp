#!/bin/bash
# Run code quality checks locally

echo "Running code formatters and linters..."
echo "======================================="

# Format with ruff
echo "1. Running ruff formatter..."
ruff format src tests

# Check with ruff
echo -e "\n2. Running ruff linter..."
ruff check src tests --fix

echo -e "\nCode quality checks complete!"
echo "Fix any issues above before committing."
