# Development Guide

This guide covers setting up a development environment and contributing to the BigQuery MCP Server.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Google Cloud SDK (for testing)
- Docker (optional, for container testing)

### Local Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bigquery-mcp.git
   cd bigquery-mcp
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration:**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your development settings
   ```

5. **Set up authentication:**
   ```bash
   gcloud auth application-default login
   ```

## Code Quality & Formatting

The project uses **ruff** for code formatting and linting to maintain consistent standards.

### Running Code Quality Checks

```bash
# Format code automatically
ruff format src tests

# Check for linting issues and auto-fix where possible
ruff check src tests --fix

# Check without auto-fixing
ruff check src tests
```

### Ruff Configuration

The project configuration is in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]  # pycodestyle, Pyflakes, import sorting
ignore = [
    "E501",  # Line too long (handled by line-length)
    "E203",  # Whitespace before ':'
    "E731",  # Do not assign a lambda expression, use a def
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Pre-Commit Workflow

Before committing code:

1. **Format and check code:**
   ```bash
   ruff format src tests
   ruff check src tests --fix
   ```

2. **Run tests:**
   ```bash
   pytest tests/unit -v
   ```

3. **Run integration tests (if BigQuery access available):**
   ```bash
   pytest tests/integration -v
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Your commit message"
   ```

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests (no external dependencies)
├── integration/    # Integration tests (require BigQuery access)
├── fixtures/       # Test configuration files
└── conftest.py     # Pytest configuration
```

### Running Tests

```bash
# Run all unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_execution.py -v

# Run integration tests (requires BigQuery setup)
pytest tests/integration -v

# Run all tests
pytest -v
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from unittest.mock import Mock
from src.tools.execution import execute_query

def test_execute_query_basic():
    """Test basic query execution."""
    # Mock dependencies
    mock_client = Mock()
    mock_config = Mock()

    # Test implementation
    result = execute_query("SELECT 1 as test")

    # Assertions
    assert result["status"] == "success"
    assert len(result["results"]) > 0
```

#### Integration Test Example

```python
import pytest
from src.client import BigQueryClient

@pytest.mark.integration
def test_bigquery_connection():
    """Test actual BigQuery connection."""
    client = BigQueryClient("tests/fixtures/test_config.yaml")

    # Test basic functionality
    datasets = client.list_datasets("your-test-project")
    assert isinstance(datasets, list)
```

### Test Configuration

Create test-specific configuration in `tests/fixtures/test_config.yaml`:

```yaml
bigquery:
  billing_project: "your-test-project"
  location: "US"

projects:
  - project_id: "your-test-project"
    project_name: "Test Project"
    datasets: ["test_*"]

limits:
  default_row_limit: 5
  max_row_limit: 100
  max_query_timeout: 30
```

## Docker Development

### Building and Testing

```bash
# Build the Docker image
docker build -t bigquery-mcp-dev .

# Test the container
docker run --rm bigquery-mcp-dev python -c "import src.server; print('OK')"

# Run with development configuration
docker run --rm -it \
  -v $(pwd)/config:/app/config:ro \
  -v ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro \
  bigquery-mcp-dev
```

### Docker Compose for Development

```yaml
# docker-compose.dev.yml
services:
  bigquery-mcp:
    build: .
    volumes:
      - ./src:/app/src  # Mount source for live reloading
      - ./config:/app/config:ro
      - ~/.config/gcloud:/home/mcpuser/.config/gcloud:ro
    environment:
      - LOG_LEVEL=DEBUG
      - COMPACT_FORMAT=false
```

## Documentation

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

### Documentation Structure

- `docs/index.md` - Homepage and overview
- `docs/installation.md` - Installation guide
- `docs/tools.md` - Tool reference
- `docs/configuration.md` - Configuration guide
- `docs/development.md` - This development guide

### Writing Documentation

- Use clear, concise language
- Include code examples for complex concepts
- Test all code examples
- Update documentation when adding features

## Contributing

### Code Style Guidelines

1. **Follow PEP 8** - Use ruff for formatting
2. **Type hints** - Add type annotations for function parameters and returns
3. **Docstrings** - Document all public functions and classes
4. **Error handling** - Use custom exceptions from `utils.errors`
5. **Logging** - Use appropriate log levels and structured messages

### Example Function

```python
def analyze_table(table: str) -> Dict[str, Any]:
    """Analyze table structure and statistics.

    Args:
        table: Full table path as 'project.dataset.table'

    Returns:
        Dictionary containing table analysis results

    Raises:
        DatasetAccessError: If table is not accessible
        QueryExecutionError: If analysis query fails
    """
    _ensure_initialized()
    logger.info(f"Analyzing table: {table}")

    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Table analysis failed: {e}")
        raise QueryExecutionError(f"Failed to analyze table: {e}")
```

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run the full test suite** and ensure all tests pass
6. **Submit a pull request** with a clear description

### Commit Message Format

Use clear, descriptive commit messages:

```bash
# Good examples
git commit -m "Add column analysis for STRING data types"
git commit -m "Fix timeout handling in query execution"
git commit -m "Update documentation for configuration options"

# Avoid
git commit -m "Fix bug"
git commit -m "Update stuff"
```

## Troubleshooting

### Common Development Issues

#### Import Errors
```
ModuleNotFoundError: No module named 'src'
```
**Solution:** Ensure you're running from the project root and `PYTHONPATH` is set correctly

#### Authentication Issues
```
google.auth.exceptions.DefaultCredentialsError
```
**Solution:** Run `gcloud auth application-default login`

#### Permission Errors in Docker
```
Permission denied: /home/mcpuser/.config/gcloud
```
**Solution:** Check file permissions:
```bash
chmod -R 755 ~/.config/gcloud
```

#### Test Failures
```
Tests failing with BigQuery errors
```
**Solution:**
1. Check your test configuration in `tests/fixtures/test_config.yaml`
2. Ensure you have access to the test BigQuery project
3. Verify your authentication is working

### Getting Help

1. **Check the logs** in the `logs/` directory
2. **Run tests** to identify specific issues
3. **Review configuration** for common mistakes
4. **Check GitHub issues** for similar problems

## Release Process

### Preparing a Release

1. **Update version numbers:**
   - `pyproject.toml`
   - `config/config.yaml.example`
   - Documentation references

2. **Update CHANGELOG.md** with new version details

3. **Run full test suite:**
   ```bash
   pytest tests/ -v
   ruff check src tests
   ```

4. **Build and test Docker image:**
   ```bash
   docker build -t bigquery-mcp:test .
   docker run --rm bigquery-mcp:test python -c "import src.server; print('OK')"
   ```

5. **Commit and tag:**
   ```bash
   git commit -m "Release v1.0.0"
   git tag v1.0.0
   git push origin main --tags
   ```

The GitHub Actions workflow will automatically create a release when the version in `pyproject.toml` changes.

## Next Steps

- [Configuration Guide](configuration.md) - Set up your development configuration
- [Tools Reference](tools.md) - Learn about the available MCP tools
- [Installation Guide](installation.md) - Different deployment options
