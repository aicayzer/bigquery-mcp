"""Unit tests for SQL validation utilities."""

from unittest.mock import Mock

import pytest

from utils.errors import SQLValidationError
from utils.validation import SQLValidator


class TestSQLValidator:
    """Test SQL validation functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock()
        config.security.banned_sql_keywords = [
            "DELETE",
            "DROP",
            "TRUNCATE",
            "INSERT",
            "UPDATE",
            "ALTER",
            "GRANT",
            "REVOKE",
            "MERGE",
            "CALL",
            "EXECUTE",
            "SCRIPT",
        ]
        config.security.require_explicit_limits = False
        config.security.select_only = True
        config.limits.default_row_limit = 100
        return config

    @pytest.fixture
    def validator(self, mock_config):
        """Create SQLValidator instance with mock config."""
        return SQLValidator(mock_config)

    def test_validate_simple_select(self, validator):
        """Test validation of simple SELECT queries."""
        queries = [
            "SELECT * FROM dataset.table",
            "SELECT COUNT(*) FROM table WHERE id > 100",
            "SELECT id, name FROM users LIMIT 10",
        ]

        for query in queries:
            # Should not raise
            validator.validate_query(query)

    def test_validate_cte_queries(self, validator):
        """Test validation of CTE (WITH) queries."""
        cte_queries = [
            "WITH cte AS (SELECT * FROM t) SELECT * FROM cte",
            """
            WITH sample AS (
                SELECT uuid, action, date 
                FROM events 
                LIMIT 10
            )
            SELECT * FROM sample ORDER BY date
            """,
            """
            WITH RECURSIVE tree AS (
                SELECT id, parent_id, name FROM categories WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, c.parent_id, c.name 
                FROM categories c 
                JOIN tree t ON c.parent_id = t.id
            )
            SELECT * FROM tree
            """,
        ]

        for query in cte_queries:
            # Should not raise
            validator.validate_query(query)

    def test_validate_banned_keywords(self, validator):
        """Test rejection of queries with banned keywords."""
        dangerous_queries = [
            "DELETE FROM table WHERE 1=1",
            "DROP TABLE dataset.table",
            "INSERT INTO table VALUES (1, 2, 3)",
            "UPDATE table SET column = 'value'",
            "TRUNCATE TABLE dataset.table",
            "ALTER TABLE table ADD COLUMN new_col STRING",
            "GRANT SELECT ON table TO user",
            "REVOKE SELECT ON table FROM user",
            "MERGE INTO target USING source ON condition",
            "CALL procedure()",
            "EXECUTE statement",
        ]

        for query in dangerous_queries:
            with pytest.raises(SQLValidationError) as exc_info:
                validator.validate_query(query)
            assert "Forbidden SQL operation" in str(exc_info.value)

    def test_validate_non_select_statements(self, validator):
        """Test rejection of non-SELECT statements."""
        non_select_queries = [
            "DESCRIBE table",
            "SHOW TABLES",
            "EXPLAIN SELECT * FROM table",
            "CREATE TABLE test (id INT)",
        ]

        for query in non_select_queries:
            with pytest.raises(SQLValidationError) as exc_info:
                validator.validate_query(query)
            assert "Only SELECT statements and CTEs (WITH) are allowed" in str(exc_info.value)

    def test_validate_empty_query(self, validator):
        """Test rejection of empty queries."""
        empty_queries = ["", "   ", "\n\t  \n"]

        for query in empty_queries:
            with pytest.raises(SQLValidationError) as exc_info:
                validator.validate_query(query)
            assert "Empty SQL query" in str(exc_info.value)

    def test_require_explicit_limits(self, mock_config):
        """Test LIMIT requirement when configured."""
        mock_config.security.require_explicit_limits = True
        validator = SQLValidator(mock_config)

        # Should pass with LIMIT
        validator.validate_query("SELECT * FROM table LIMIT 10")

        # Should fail without LIMIT
        with pytest.raises(SQLValidationError) as exc_info:
            validator.validate_query("SELECT * FROM table")
        assert "must include an explicit LIMIT clause" in str(exc_info.value)

    def test_add_limit_if_needed(self, validator):
        """Test automatic LIMIT addition."""
        # Query without LIMIT should get one added
        result = validator.add_limit_if_needed("SELECT * FROM table", 50)
        assert "LIMIT 50" in result

        # Query with existing LIMIT should be unchanged
        query_with_limit = "SELECT * FROM table LIMIT 10"
        result = validator.add_limit_if_needed(query_with_limit, 50)
        assert result == query_with_limit

        # Should use default limit if none specified
        result = validator.add_limit_if_needed("SELECT * FROM table")
        assert "LIMIT 100" in result  # Default from mock config
