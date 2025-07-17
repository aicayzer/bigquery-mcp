# BigQuery MCP Development Standards

## Code Quality
- Write clean, efficient, minimal code
- No unnecessary complexity or over-engineering
- Follow existing patterns and conventions
- Use descriptive variable names, avoid abbreviations

## Version Control
- Update version numbers consistently across all files when making releases
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Keep commits focused and atomic
- Write clear, concise commit messages

## Code Standards
- Run `ruff format` before committing
- Run `ruff check --fix` to resolve linting issues
- Add type hints for function parameters and returns
- Include docstrings for public functions and classes

## Testing
- Add tests for new functionality
- Run `pytest` before committing
- Ensure all tests pass in CI

## Documentation
- Keep documentation minimal and focused
- Update relevant docs when changing functionality
- Use clear, direct language - no fluff or emojis
- Focus on what users need to know, not implementation details

## Changelog Formatting
- Use clean, elegant formatting without bold text
- Write concise, descriptive entries
- No unnecessary formatting or emphasis
- Keep entries focused on what actually changed

## Architecture
- Prefer command-line arguments over config files
- Keep dependencies minimal
- Follow MCP protocol standards
- Maintain backwards compatibility when possible

## Error Handling
- Use custom exception classes for specific error types
- Provide actionable error messages
- Log errors appropriately for debugging

## User Preferences
- Avoid over-engineering and unnecessary complexity
- Don't overthink security implementations unless specifically requested
- Focus on what's needed, not what could be possible
- Maintain high repository standards suitable for GitHub
- Keep configuration clean with proper .example files and gitignored personal configs 