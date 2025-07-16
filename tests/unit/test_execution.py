"""Unit tests for execution tools."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from tools.execution import (
    _format_query_results,
    _serialize_value,
    _validate_query_safety,
    execute_query,
    register_execution_tools,
)
from utils.errors import QueryExecutionError, SecurityError


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
            "DELETE",
            "DROP",
            "TRUNCATE",
            "INSERT",
            "UPDATE",
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
            "TRUNCATE TABLE dataset.table",
        ]

        for query in dangerous_queries:
            with pytest.raises(SecurityError) as exc_info:
                _validate_query_safety(query)
            assert "Forbidden SQL operation" in str(exc_info.value)

    def test_validate_non_select_query(self, mock_dependencies):
        """Test rejection of non-SELECT queries."""
        with pytest.raises(SecurityError) as exc_info:
            _validate_query_safety("DESCRIBE dataset.table")
        assert "Only SELECT statements and CTEs (WITH) are allowed" in str(exc_info.value)

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
        results = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        formatted = _format_query_results(results, "json")
        assert formatted == results

    def test_format_csv(self):
        """Test CSV formatting."""
        results = [
            {"id": 1, "name": "Alice", "score": 95.5},
            {"id": 2, "name": "Bob", "score": 87.0},
        ]
        csv_output = _format_query_results(results, "csv")

        lines = csv_output.strip().split("\n")
        assert lines[0].rstrip() == "id,name,score"
        assert lines[1].rstrip() == "1,Alice,95.5"
        assert lines[2].rstrip() == "2,Bob,87.0"

    def test_format_table(self):
        """Test table formatting."""
        results = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        table_output = _format_query_results(results, "table")

        lines = table_output.split("\n")
        assert "id" in lines[0] and "name" in lines[0]
        assert "---" in lines[1]  # Separator
        assert "Alice" in lines[2]
        assert "Bob" in lines[3]

    def test_format_empty_results(self):
        """Test formatting empty results."""
        assert _format_query_results([], "json") == []
        assert _format_query_results([], "csv") == ""
        assert _format_query_results([], "table") == "No results"

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
        nested = {"key": datetime(2023, 1, 1), "values": [Decimal("1.5"), None]}
        serialized = _serialize_value(nested)
        assert serialized["key"] == "2023-01-01T00:00:00"
        assert serialized["values"] == [1.5]  # None values filtered out for BigQuery compatibility


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
        from datetime import datetime

        # Mock query job
        mock_job = Mock()

        # Create mock row data
        row_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        # Create mock rows that behave like BigQuery Row objects
        mock_rows = []
        for data in row_data:
            mock_row = Mock()
            mock_row.__getitem__ = lambda self, key, data=data: data[key]
            mock_row.items = lambda data=data: data.items()
            mock_rows.append(mock_row)

        # Create mock RowIterator
        mock_row_iterator = Mock()
        mock_row_iterator.__iter__ = Mock(return_value=iter(mock_rows))

        # Mock schema on the iterator (preferred over query_job.schema)
        MockField = Mock()
        MockField.name = "id"
        MockField.field_type = "INT64"
        MockField.mode = "REQUIRED"
        MockField.description = ""

        MockField2 = Mock()
        MockField2.name = "name"
        MockField2.field_type = "STRING"
        MockField2.mode = "NULLABLE"
        MockField2.description = ""

        mock_row_iterator.schema = [MockField, MockField2]

        # result() should return the RowIterator
        mock_job.result = Mock(return_value=mock_row_iterator)

        mock_job.total_bytes_processed = 1024
        mock_job.total_bytes_billed = 1024
        mock_job.cache_hit = True
        mock_job.total_rows = 2
        mock_job.created = datetime(2024, 1, 1, 10, 0, 0)
        mock_job.ended = datetime(2024, 1, 1, 10, 0, 5)
        mock_job.schema = [MockField, MockField2]  # Fallback schema

        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)

        # Execute query
        result = execute_query("SELECT id, name FROM dataset.table")

        # Verify result
        assert result["status"] == "success"
        assert result["row_count"] == 2
        assert result["bytes_processed"] == 1024
        assert result["cache_hit"] is True
        assert len(result["results"]) == 2
        assert result["results"][0] == {"id": 1, "name": "Alice"}
        assert result["results"][1] == {"id": 2, "name": "Bob"}
        assert "schema" in result

    def test_execute_query_with_limit(self, mock_dependencies):
        """Test that LIMIT is added when not present."""
        from datetime import datetime

        mock_job = Mock()
        # Create empty mock RowIterator
        mock_row_iterator = Mock()
        mock_row_iterator.__iter__ = Mock(return_value=iter([]))
        mock_row_iterator.schema = []  # Empty schema
        mock_job.result = Mock(return_value=mock_row_iterator)
        mock_job.schema = []
        mock_job.total_bytes_processed = 0
        mock_job.total_bytes_billed = 0
        mock_job.cache_hit = False
        mock_job.created = datetime(2024, 1, 1, 10, 0, 0)
        mock_job.ended = datetime(2024, 1, 1, 10, 0, 1)

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
        assert result["status"] == "success"
        assert result["dry_run"] is True
        assert result["total_bytes_processed"] == 1048576
        assert "estimated_cost_usd" in result
        assert "results" not in result

    def test_execute_query_with_parameters(self, mock_dependencies):
        """Test parameterized query execution."""
        from datetime import datetime

        mock_job = Mock()
        # Create empty mock RowIterator
        mock_row_iterator = Mock()
        mock_row_iterator.__iter__ = Mock(return_value=iter([]))
        mock_row_iterator.schema = []  # Empty schema
        mock_job.result = Mock(return_value=mock_row_iterator)
        mock_job.schema = []
        mock_job.total_bytes_processed = 0
        mock_job.total_bytes_billed = 0
        mock_job.cache_hit = False
        mock_job.created = datetime(2024, 1, 1, 10, 0, 0)
        mock_job.ended = datetime(2024, 1, 1, 10, 0, 2)

        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)

        # Execute with parameters
        execute_query(
            "SELECT * FROM table WHERE id = @id AND name = @name",
            parameters={"id": 123, "name": "Alice"},
        )

        # Verify query was executed with parameters
        call_args = mock_dependencies.bq_client.client.query.call_args
        # query = call_args[0][0]  # Query content not needed for this test
        job_config = call_args[1]["job_config"]
        # Check that a job config was passed (parameters would be set there)
        assert job_config is not None

    def test_execute_query_csv_format(self, mock_dependencies):
        """Test CSV output format."""
        from datetime import datetime

        # Mock simple results
        mock_job = Mock()

        # Create mock row data
        row_data = [{"id": 1, "value": 10.5}, {"id": 2, "value": 20.0}]

        # Create mock rows that behave like BigQuery Row objects
        mock_rows = []
        for data in row_data:
            mock_row = Mock()
            mock_row.__getitem__ = lambda self, key, data=data: data[key]
            mock_row.items = lambda data=data: data.items()
            mock_rows.append(mock_row)

        # Create mock RowIterator
        mock_row_iterator = Mock()
        mock_row_iterator.__iter__ = Mock(return_value=iter(mock_rows))

        # Mock schema fields
        MockField = Mock()
        MockField.name = "id"
        MockField.field_type = "INT64"
        MockField.mode = "REQUIRED"
        MockField.description = ""

        MockField2 = Mock()
        MockField2.name = "value"
        MockField2.field_type = "FLOAT64"
        MockField2.mode = "NULLABLE"
        MockField2.description = ""

        mock_row_iterator.schema = [MockField, MockField2]
        mock_job.result = Mock(return_value=mock_row_iterator)

        # Add required attributes
        mock_job.total_bytes_processed = 1024
        mock_job.total_bytes_billed = 1024
        mock_job.cache_hit = False
        mock_job.total_rows = 2
        mock_job.created = datetime(2024, 1, 1, 10, 0, 0)
        mock_job.ended = datetime(2024, 1, 1, 10, 0, 3)
        mock_job.schema = [MockField, MockField2]  # Fallback schema

        mock_dependencies.bq_client.client.query = Mock(return_value=mock_job)

        # Execute with CSV format
        result = execute_query("SELECT * FROM table", format="csv")

        assert result["status"] == "success"
        assert result["format"] == "csv"
        assert "id,value" in result["data"]
        assert "1,10.5" in result["data"]

    def test_execute_query_permission_denied(self, mock_dependencies):
        """Test handling of permission errors."""
        mock_dependencies.bq_client.client.query = Mock(side_effect=Exception("403 Access Denied"))

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
        register_execution_tools(mock_mcp, mock_handler, mock_client, mock_config, mock_formatter)

        # Verify tools were registered (only execute_query exists)
        assert mock_mcp.tool.call_count == 1

        # Verify globals were set
        import tools.execution as execution

        assert execution.mcp == mock_mcp
        assert execution.handle_error == mock_handler
        assert execution.bq_client == mock_client
        assert execution.config == mock_config
        assert execution.formatter == mock_formatter
