#!/bin/bash
# Run code quality checks locally

echo "Running code formatters and linters..."
echo "======================================="

# Format with black
echo "1. Running black formatter..."
black src tests

# Check with flake8
echo -e "\n2. Running flake8 linter..."
flake8 src tests

# Type check with mypy
echo -e "\n3. Running mypy type checker..."
mypy src

echo -e "\nCode quality checks complete!"
echo "Fix any issues above before committing."
