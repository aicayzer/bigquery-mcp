"""Unit tests for execution tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

from tools.execution import (
    _validate_query_safety,
    _format_query_results,
    _serialize_value,
    execute_query,
    validate_query,
    get_query_history,
    register_execution_tools
)
from utils.errors import SecurityError, QueryExecutionError, SQLValidationError


class TestQueryValidation:
    """Test query safety validation."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies."""
        import tools.execution as execution
        
        # Mock global dependencies
        execution.mcp = Mock()
        execution.handle_error = lambda f: f
        execution.bq_client = Mock()
        execution.config = Mock()
        execution.formatter = Mock()
        
        # Configure security mocks
        execution.config.security.banned_sql_keywords = [
            "DELETE", "DROP", "TRUNCATE", "INSERT", "UPDATE"
        ]
        execution.config.security.require_explicit_limits = False
        execution.config.limits.default_row_limit = 100
        execution.config.limits.max_row_limit = 10000
        execution.config.limits.max_query_timeout = 60
        execution.config.limits.max_bytes_processed = 1073741824
        
        yield execution
        
        # Reset globals
        execution.mcp = None
        execution.bq_client = None
        execution.config = None
        execution.formatter = None
    
    def test_validate_safe_select_query(self, mock_dependencies):
        """Test validation of safe SELECT query."""
        # Should not raise
        _validate_query_safety("SELECT * FROM dataset.table")
        _validate_query_safety("SELECT COUNT(*) FROM table WHERE id > 100")
        _validate_query_safety("WITH cte AS (SELECT * FROM t) SELECT * FROM cte")
    
    def test_validate_dangerous_queries(self, mock_dependencies):
        """Test rejection of dangerous queries."""
        dangerous_queries = [
            "DELETE FROM table WHERE 1=1",
            "DROP TABLE dataset.table",
            "INSERT INTO table VALUES (1, 2, 3)",
            "UPDATE table SET column = 'value'",
            "TRUNCATE TABLE dataset.table"
        ]
        
        for query in dangerous_queries:
            with pytest.raises(SecurityError) as exc_info:
                _validate_query_safety(query)
            assert "forbidden operations" in str(exc_info.value)
    
    def test_validate_non_select_query(self, mock_dependencies):
        """Test rejection of non-SELECT queries."""
        with pytest.raises(SecurityError) as exc_info:
            _validate_query_safety("DESCRIBE dataset.table")
        assert "Only SELECT queries" in str(exc_info.value)
    
    def test_require_explicit_limits(self, mock_dependencies):
        """Test LIMIT requirement when configured."""
        mock_dependencies.config.security.require_explicit_limits = True
        
        # Should pass with LIMIT
        _validate_query_safety("SELECT * FROM table LIMIT 10")
        
        # Should fail without LIMIT
        with pytest.raises(SecurityError) as exc_info:
            _validate_query_safety("SELECT * FROM table")
        assert "must include an explicit LIMIT" in str(exc_info.value)


class TestResultFormatting:
    """Test result formatting functions."""
    
    def test_format_json(self):
        """Test JSON formatting (pass-through)."""
        results = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
        formatted = _format_query_results(results, 'json')
        assert formatted == results
    
    def test_format_csv(self):
        """Test CSV formatting."""
        results = [
            {'id': 1, 'name': 'Alice', 'score': 95.5},
            {'id': 2, 'name': 'Bob', 'score': 87.0}
        ]
        csv_output = _format_query_results(results, 'csv')
        
        lines = csv_output.strip().split('\n')
        assert lines[0] == 'id,name,score'
        assert lines[1] == '1,Alice,95.5'
        assert lines[2] == '2,Bob,87.0'
    
    def test_format_table(self):
        """Test table formatting."""
        results = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
        table_output = _format_query_results(results, 'table')
        
        lines = table_output.split('\n')
        assert 'id' in lines[0] and 'name' in lines[0]
        assert '---' in lines[1]  # Separator
        assert 'Alice' in lines[2]
        assert 'Bob' in lines[3]
    
    def test_format_empty_results(self):
        """Test formatting empty results."""
        assert _format_query_results([], 'json') == []
        assert _format_query_results([], 'csv') == ""
        assert _format_query_results([], 'table') == "No results"
    
    def test_serialize_value(self):
        """Test value serialization for BigQuery types."""
        # Basic types
        assert _serialize_value(None) is None
        assert _serialize_value("string") == "string"
        assert _serialize_value(123) == 123
        assert _serialize_value(45.67) == 45.67
        assert _serialize_value(True) is True
        
        # Datetime
        dt = datetime(2023, 1, 1, 12, 0, 0)
        assert _serialize_value(dt) == "2023-01-01T12:00:00"
        
        # Decimal
        assert _serialize_value(Decimal("123.45")) == 123.45
        
        # Bytes
        assert _serialize_value(b"hello") == "hello"
        
        # Nested structures
        nested = {'key': datetime(2023, 1, 1), 'values': [Decimal("1.5"), None]}
        serialized = _serialize_value(nested)
        assert serialized['key'] == "2023-01-01T00:00:00"
        assert serialized['values'] == [1.5, None]


class TestExecuteQuery:
    """Test execute_query functionality."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies."""
        import tools.execution as execution
        
        # Mock global dependencies
        execution.mcp = Mock()
        execution.handle_error = lambda f: f
        execution.bq_client = Mock()
        execution.config = Mock()
        execution.formatter = Mock()
        
        # Configure mocks
        execution.config.security.banned_sql_keywords = ["DELETE", "DROP"]
        execution.config.security.require_explicit_limits = False
        execution.config.limits.default_row_limit = 100
        execution.config.limits.max_row_limit = 10000
        execution.config.limits.max_query_timeout = 60
        execution.config.limits.max_bytes_processed = 1073741824
        execution.config.log_queries = True
        execution.config.log_results = False
        execution.config.max_query_log_length = 200
        execution.formatter.compact_mode = False
        
        yield execution
        
        # Reset globals
        execution.mcp = None
        execution.bq_client = None
        execution.config = None
        execution.formatter = None
    
    def test_execute_simple_query(self, mock_dependencies):
        """Test executing a simple SELECT query."""
        # Mock query job
        mock_job = Mock()
        mock_job.result = Mock(return_value=[
            Mock(id=1, name='Alice'),
            Mock(id=2, name='Bob')
        ])
        mock_job.total_bytes_processed = 1024
        mock_job.total_bytes_billed = 1024
        mock_job.cache_hit = True
        mock_job.total_rows = 2
        
        # Mock schema
        MockField = Mock()
        MockField.name = 'id'
        MockField.field_type = 'INT64'
        MockField.mode = 'REQUIRED'
        MockField.description = ''
        
        MockField2 = Mock()
        MockField2.name = 'name'
        MockField2.field_type = 'STRING'
        MockField2.mode = 'NULLABLE'
        MockField2.description = ''
        
        mock_job.schema = [MockField, MockField2]
        
        # Configure the mock to allow item access
        mock_job.result.return_value[0].__getitem__ = lambda self, key: {'id': 1, 'name': 'Alice'}[key]
        mock_job.result.return_value[1].__getitem__ = lambda self, key: {'id': 2, 'name': 'Bob'}[key]
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        # Execute query
        result = execute_query("SELECT id, name FROM dataset.table")
        
        # Verify result
        assert result['status'] == 'success'
        assert result['row_count'] == 2
        assert result['bytes_processed'] == 1024
        assert result['cache_hit'] is True
        assert len(result['results']) == 2
        assert result['results'][0] == {'id': 1, 'name': 'Alice'}
        assert result['results'][1] == {'id': 2, 'name': 'Bob'}
        assert 'schema' in result
    
    def test_execute_query_with_limit(self, mock_dependencies):
        """Test that LIMIT is added when not present."""
        mock_job = Mock()
        mock_job.result = Mock(return_value=[])
        mock_job.schema = []
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        # Execute query without LIMIT
        execute_query("SELECT * FROM table")
        
        # Verify LIMIT was added
        call_args = mock_dependencies.bq_client.client.query.call_args
        query = call_args[0][0]
        assert "LIMIT 100" in query
    
    def test_execute_query_dry_run(self, mock_dependencies):
        """Test dry run mode."""
        mock_job = Mock()
        mock_job.total_bytes_processed = 1048576  # 1 MB
        mock_job.total_bytes_billed = 1048576
        mock_job.schema = []
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        # Execute dry run
        result = execute_query("SELECT * FROM table", dry_run=True)
        
        # Verify dry run result
        assert result['status'] == 'success'
        assert result['dry_run'] is True
        assert result['total_bytes_processed'] == 1048576
        assert 'estimated_cost_usd' in result
        assert 'results' not in result
    
    def test_execute_query_with_parameters(self, mock_dependencies):
        """Test parameterized query execution."""
        mock_job = Mock()
        mock_job.result = Mock(return_value=[])
        mock_job.schema = []
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        # Execute with parameters
        execute_query(
            "SELECT * FROM table WHERE id = @id AND name = @name",
            parameters={'id': 123, 'name': 'Alice'}
        )
        
        # Verify parameters were set
        call_args = mock_dependencies.bq_client.client.query.call_args
        job_config = call_args[1]['job_config']
        assert hasattr(job_config, 'query_parameters')
        assert len(job_config.query_parameters) == 2
    
    def test_execute_query_csv_format(self, mock_dependencies):
        """Test CSV output format."""
        # Mock simple results
        mock_job = Mock()
        mock_job.result = Mock(return_value=[
            Mock(id=1, value=10.5),
            Mock(id=2, value=20.0)
        ])
        
        MockField = Mock()
        MockField.name = 'id'
        MockField.field_type = 'INT64'
        MockField.mode = 'REQUIRED'
        MockField.description = ''
        
        MockField2 = Mock()
        MockField2.name = 'value'
        MockField2.field_type = 'FLOAT64'
        MockField2.mode = 'NULLABLE'
        MockField2.description = ''
        
        mock_job.schema = [MockField, MockField2]
        mock_job.result.return_value[0].__getitem__ = lambda self, key: {'id': 1, 'value': 10.5}[key]
        mock_job.result.return_value[1].__getitem__ = lambda self, key: {'id': 2, 'value': 20.0}[key]
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        # Execute with CSV format
        result = execute_query("SELECT * FROM table", format='csv')
        
        assert result['status'] == 'success'
        assert result['format'] == 'csv'
        assert 'id,value' in result['data']
        assert '1,10.5' in result['data']
    
    def test_execute_query_permission_denied(self, mock_dependencies):
        """Test handling of permission errors."""
        mock_dependencies.bq_client.client.query = Mock(
            side_effect=Exception("403 Access Denied")
        )
        
        with pytest.raises(QueryExecutionError) as exc_info:
            execute_query("SELECT * FROM table")
        
        assert "Permission denied" in str(exc_info.value)
    
    def test_execute_query_table_not_found(self, mock_dependencies):
        """Test handling of table not found errors."""
        mock_dependencies.bq_client.client.query = Mock(
            side_effect=Exception("404 Not found: Table dataset.table")
        )
        
        with pytest.raises(QueryExecutionError) as exc_info:
            execute_query("SELECT * FROM dataset.table")
        
        assert "Table not found" in str(exc_info.value)


class TestValidateQuery:
    """Test validate_query functionality."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies."""
        import tools.execution as execution
        
        # Mock global dependencies
        execution.mcp = Mock()
        execution.handle_error = lambda f: f
        execution.bq_client = Mock()
        execution.config = Mock()
        execution.formatter = Mock()
        
        # Configure mocks
        execution.config.security.banned_sql_keywords = ["DELETE", "DROP"]
        execution.config.security.require_explicit_limits = False
        execution.config.limits.default_row_limit = 100
        execution.config.limits.max_row_limit = 10000
        execution.config.limits.max_query_timeout = 60
        execution.config.limits.max_bytes_processed = 1073741824
        
        yield execution
        
        # Reset globals
        execution.mcp = None
        execution.bq_client = None
        execution.config = None
        execution.formatter = None
    
    def test_validate_valid_query(self, mock_dependencies):
        """Test validation of valid query."""
        # Mock successful dry run
        mock_job = Mock()
        mock_job.total_bytes_processed = 1024
        mock_job.total_bytes_billed = 1024
        mock_job.schema = []
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        result = validate_query("SELECT * FROM table")
        
        assert result['status'] == 'success'
        assert result['valid'] is True
        assert result['message'] == 'Query is valid'
        assert 'estimated_bytes' in result
        assert 'estimated_cost_usd' in result
    
    def test_validate_invalid_security(self, mock_dependencies):
        """Test validation of query with security violations."""
        result = validate_query("DELETE FROM table WHERE 1=1")
        
        assert result['status'] == 'error'
        assert result['valid'] is False
        assert result['error_type'] == 'security'
        assert 'forbidden operations' in result['message']
    
    def test_validate_invalid_syntax(self, mock_dependencies):
        """Test validation of query with syntax errors."""
        mock_dependencies.bq_client.client.query = Mock(
            side_effect=Exception("Syntax error: Unexpected token")
        )
        
        result = validate_query("SELECT * FORM table")  # Typo: FORM instead of FROM
        
        assert result['status'] == 'error'
        assert result['valid'] is False
        assert result['error_type'] == 'syntax'


class TestQueryHistory:
    """Test get_query_history functionality."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Set up mock dependencies."""
        import tools.execution as execution
        
        # Mock global dependencies
        execution.mcp = Mock()
        execution.handle_error = lambda f: f
        execution.bq_client = Mock()
        execution.config = Mock()
        execution.formatter = Mock()
        
        # Configure mocks
        execution.bq_client.billing_project = 'test-project'
        execution.bq_client.client.location = 'US'
        
        yield execution
        
        # Reset globals
        execution.mcp = None
        execution.bq_client = None
        execution.config = None
        execution.formatter = None
    
    def test_get_query_history_success(self, mock_dependencies):
        """Test successful query history retrieval."""
        # Mock query results
        MockRow = Mock()
        MockRow.creation_time = datetime.now()
        MockRow.project_id = 'test-project'
        MockRow.user_email = 'user@example.com'
        MockRow.state = 'DONE'
        MockRow.duration_ms = 1500
        MockRow.total_bytes_processed = 1024
        MockRow.total_slot_ms = 500
        MockRow.query = "SELECT * FROM dataset.table LIMIT 10"
        MockRow.error_message = None
        
        mock_job = Mock()
        mock_job.result = Mock(return_value=[MockRow])
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        result = get_query_history(limit=5)
        
        assert result['status'] == 'success'
        assert result['query_count'] == 1
        assert len(result['queries']) == 1
        
        query_info = result['queries'][0]
        assert query_info['project'] == 'test-project'
        assert query_info['user'] == 'user@example.com'
        assert query_info['state'] == 'DONE'
        assert 'query_preview' in query_info
    
    def test_get_query_history_with_error(self, mock_dependencies):
        """Test query history with failed query."""
        # Mock query with error
        MockRow = Mock()
        MockRow.creation_time = datetime.now()
        MockRow.project_id = 'test-project'
        MockRow.user_email = 'user@example.com'
        MockRow.state = 'FAILED'
        MockRow.duration_ms = 100
        MockRow.total_bytes_processed = 0
        MockRow.total_slot_ms = 0
        MockRow.query = "SELECT * FROM nonexistent_table"
        MockRow.error_message = "Table not found"
        
        mock_job = Mock()
        mock_job.result = Mock(return_value=[MockRow])
        
        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)
        
        result = get_query_history()
        
        query_info = result['queries'][0]
        assert query_info['state'] == 'FAILED'
        assert query_info['error'] == 'Table not found'
    
    def test_get_query_history_failure(self, mock_dependencies):
        """Test handling of query history retrieval failure."""
        mock_dependencies.bq_client.client.query = Mock(
            side_effect=Exception("Access denied to INFORMATION_SCHEMA")
        )
        
        result = get_query_history()
        
        assert result['status'] == 'error'
        assert 'Could not fetch query history' in result['error']
        assert 'INFORMATION_SCHEMA' in result['note']


class TestToolRegistration:
    """Test tool registration."""
    
    def test_register_execution_tools(self):
        """Test that execution tools are properly registered."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        mock_handler = Mock()
        mock_client = Mock()
        mock_config = Mock()
        mock_formatter = Mock()
        
        # Register tools
        register_execution_tools(
            mock_mcp,
            mock_handler,
            mock_client,
            mock_config,
            mock_formatter
        )
        
        # Verify tools were registered
        assert mock_mcp.tool.call_count == 3  # execute_query, validate_query, get_query_history
        
        # Verify globals were set
        import tools.execution as execution
        assert execution.mcp == mock_mcp
        assert execution.handle_error == mock_handler
        assert execution.bq_client == mock_client
        assert execution.config == mock_config
        assert execution.formatter == mock_formatter
