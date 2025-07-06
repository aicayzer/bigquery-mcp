# Development Guide

## Code Quality & Linting

The project uses automated code quality tools to maintain consistent standards:

### Running Code Quality Checks

```bash
# Make the script executable (first time only)
chmod +x scripts/lint.sh

# Run all checks
./scripts/lint.sh
```

This script runs:
1. **black** - Automatic code formatting
2. **flake8** - Style guide enforcement
3. **mypy** - Static type checking

### Quick Fixes

Some issues can be automatically fixed:

```bash
# Auto-format code with black
black src tests

# The rest need manual fixes
```

### Common Issues & Solutions

#### Line Length (E501)
- Maximum line length is 79 characters (flake8 config)
- Break long lines at logical points
- Use parentheses for multi-line expressions

#### Unused Imports (F401)
- Remove imports that aren't used in the file
- Common in `__init__.py` files for re-exports

#### Type Annotations
- Add type hints to function parameters and return values
- Use `-> None` for functions that don't return anything

### Pre-Commit Checks

Before committing:
1. Run `./scripts/lint.sh`
2. Fix any issues reported
3. Run tests: `pytest`
4. Commit your changes

## Docker Troubleshooting

If the Docker container isn't connecting to Claude:

1. **Verify the image name matches exactly**:
   ```bash
   docker images | grep bigquery-mcp
   ```

2. **Test the container manually**:
   ```bash
   docker run --rm -it \
     -v /Users/august.cayzer/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
     bigquery-mcp:test
   ```

3. **Check logs in Claude Desktop**:
   - Open Developer Tools (View → Toggle Developer Tools)
   - Check Console tab for errors

4. **Common issues**:
   - Image name mismatch (bigquery-mcp vs bigquery-mcp:test)
   - Volume mount permissions
   - Container not built with latest changes
