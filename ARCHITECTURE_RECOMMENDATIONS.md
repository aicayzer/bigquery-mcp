# BigQuery MCP Architecture Recommendations

## Tool Organization

### Core Tools (Essential for BigQuery Operations)

1. **Discovery Tools**
   - `list_projects()` - List accessible BigQuery projects
   - `list_datasets(project?)` - List datasets in a project
   - `list_tables(table_path, table_type?)` - List tables in a dataset

2. **Analysis Tools**  
   - `analyze_table(table_path, sample_size?)` - Analyze table structure
   - `analyze_columns(table_path, columns?, include_examples?, sample_size?)` - Deep column analysis

3. **Query Tools**
   - `execute_query(query, format?, max_rows?, timeout?, dry_run?, parameters?)` - Execute SQL
   - `validate_query(query)` - Validate SQL syntax and estimate cost

### Administrative Tools (Optional/Development)

1. **Monitoring Tools**
   - `get_server_info()` - Server configuration and capabilities
   - `health_check()` - Test BigQuery connectivity

2. **Audit Tools** (Consider Removing)
   - `get_query_history(limit?)` - Recent query history (has issues, not essential)

## Parameter Standardization Recommendations

### Current Inconsistencies

1. **Path Parameters**
   - Some tools use `dataset_path` for "project.dataset"
   - Some tools use `table_path` for "project.dataset.table"
   - Inconsistent whether project is optional or required

2. **Sample Size**
   - `analyze_table` uses `sample_size` (default: 1000)
   - `analyze_columns` uses `sample_size` (default: 10000)
   - Different defaults for similar purposes

### Proposed Standards

1. **Consistent Path Format**
   ```python
   # Always use explicit parameter names
   project: str          # "my-project" (optional, defaults to billing project)
   dataset: str          # "my_dataset" (required when needed)
   table: str           # "my_table" (required when needed)
   
   # OR use qualified paths consistently
   dataset_path: str    # "project.dataset" or "dataset"
   table_path: str      # "project.dataset.table" or "dataset.table"
   ```

2. **Consistent Defaults**
   ```python
   sample_size: int = 1000      # Same default across all sampling
   timeout: int = 60            # Same timeout default
   max_rows: int = 1000         # Same row limit default
   ```

3. **Consistent Parameter Names**
   ```python
   # Use these names consistently:
   format: Literal["json", "csv", "table"]  # Output format
   include_examples: bool                    # Include sample data
   dry_run: bool                            # Preview without executing
   ```

## Implementation Priority

### Phase 1: Fix Critical Issues (v0.4.3)
1. Fix BigQuery client region configuration
2. Fix SQL generation bugs
3. Fix timeout handling
4. Remove or fix `get_query_history`

### Phase 2: Standardize Interface (v0.5.0)
1. Standardize all parameter names
2. Reorganize tools into categories
3. Add comprehensive tests
4. Update documentation

### Phase 3: Production Ready (v1.0.0)
1. Security audit
2. Performance optimization
3. Docker packaging
4. Complete documentation

## Testing Requirements

### Unit Tests (Per Tool)
- Valid parameter combinations
- Invalid parameter handling
- Error scenarios
- Permission errors
- Network timeouts

### Integration Tests
- MCP protocol handling
- Cross-project access
- Large result sets
- Concurrent requests
- Authentication flows

### Security Tests
- SQL injection prevention
- Access control validation
- Resource limits enforcement
- Credential handling

## Configuration Recommendations

### Add to config.yaml:
```yaml
# Regional settings
bigquery:
  location: "US"  # or "EU", "asia-northeast1", etc.
  
# Tool-specific settings
tools:
  analysis:
    default_sample_size: 1000
    max_sample_size: 100000
  
  execution:
    default_timeout: 60
    max_timeout: 300
    default_row_limit: 1000
    
  # Feature flags
  admin_tools_enabled: true
  query_history_enabled: false
```

## Summary

The v0.4.2 parameter fix was correct, but revealed deeper architectural issues:

1. **Region configuration** is missing, breaking INFORMATION_SCHEMA queries
2. **SQL generation** has bugs in complex column analysis
3. **Parameter naming** is inconsistent across tools
4. **Tool organization** mixes essential and administrative functions
5. **Test coverage** is insufficient for production use

These should be addressed systematically in v0.4.3 and v0.5.0 before considering this production-ready.
