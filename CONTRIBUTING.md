# Contributing to BigQuery MCP Server

## Development Process

1. Fork the repository
2. Clone your fork
3. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

4. Make your changes:
   - Add tests for new functionality
   - Update documentation as needed
   - Follow existing code patterns

5. Run tests and quality checks:
   ```bash
   pytest
   ruff format
   ruff check
   ```

6. Commit your changes:
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```

7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

8. Create a Pull Request:
   - Target branch: `develop` (not main)
   - Provide clear description of changes
   - Reference any related issues

## Code Standards

- Python 3.11+ compatibility
- Type hints for function parameters
- Docstrings for public functions
- Tests for new functionality
- No debug print statements
- No commented-out code

## Testing

All new features must include tests. Place tests in:
- `tests/unit/` for isolated component tests
- `tests/integration/` for cross-component tests

## Questions

Open an issue for questions or discussions before implementing major changes.
