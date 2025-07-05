# Claude Development Guidelines

This document provides guidelines for Claude when working on the BigQuery MCP project.

## Task Management

### Working with TASKS.md

1. **Completing Tasks**: When you complete a task, mark it as done by changing `[ ]` to `[x]`
2. **Version Batches**: Once all tasks for a version are complete:
   - Remove completed tasks from TASKS.md
   - Update CHANGELOG.md with the version changes
   - Ask about incrementing the version number

### Version Management

- Pre-1.0 versions use 0.x.y format
- Minor version (0.x.0) for new features/significant changes
- Patch version (0.x.y) for bug fixes and minor improvements
- When in doubt, ask whether changes warrant a new version

## Code Style

### Comments
- Use inline comments sparingly, only where logic is non-obvious
- Keep comments concise and to the point
- No decorative comment blocks or ASCII art
- Docstrings for all public functions/classes

### Code Organization
- Functions should do one thing well
- Keep files focused and under 300 lines where possible
- Use descriptive variable names, but concise where appropriate
- Follow PEP 8 style guidelines

## Git Commits

### Commit Messages
- Single line, imperative mood: "Add list_projects tool"
- No emoji or decorative elements
- Be specific but concise
- Examples:
  - "Add BigQuery client initialization"
  - "Fix SQL validation for nested queries"
  - "Update dependencies to latest versions"

### Commit Frequency
- Logical, atomic commits
- One feature/fix per commit where possible
- Commit after completing each meaningful unit of work

## Development Workflow

1. **Before Making Changes**:
   - Review current TASKS.md
   - Ensure understanding of the specific task
   - Check for any blocking dependencies

2. **While Developing**:
   - Write tests alongside implementation
   - Run tests frequently
   - Keep security in mind (no credentials in code)

3. **After Changes**:
   - Update TASKS.md
   - Make appropriate git commit(s)
   - Update documentation if needed
   - Note any new tasks discovered

## Testing

### Test Organization
- `tests/unit/` - Fast tests with mocked dependencies
- `tests/integration/` - Tests requiring BigQuery connection
- Use fixtures for test data, never real company data

### Test Data
- Anonymize any data from sandbox environments
- No company-specific information in tests
- Use generic examples (e.g., "analytics_dataset" not "business_banking_demo")

## Documentation

### README Updates
- Keep examples generic and professional
- Update when adding new features
- Ensure all code examples are tested

### Changelog
- Group changes by type: Added, Changed, Fixed, Removed
- Use clear, user-focused language
- Date entries when releasing versions

## Security Reminders

1. Never commit credentials or sensitive data
2. All SQL operations must be read-only
3. Validate all user inputs
4. Use parameterized queries where applicable
5. Keep dependencies updated

## Quality Checklist

Before considering work complete:
- [ ] Tests pass
- [ ] Code is clean and follows style guidelines
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] TASKS.md is updated
- [ ] Appropriate commits made

## Common Patterns

### Error Handling
```python
try:
    result = perform_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return {"status": "error", "error": str(e)}
```

### Tool Response Format
```python
return {
    "status": "success",  # or "error"
    "data": result_data,
    "metadata": {
        "row_count": len(results),
        "execution_time_ms": elapsed_time
    }
}
```

## Notes

- When unsure about a decision, ask for clarification
- Prioritize security and reliability over features
- Keep the user experience simple and intuitive
- Remember this is a read-only tool for data exploration
