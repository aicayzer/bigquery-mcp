"""SQL validation utilities for query safety."""

import logging
import re
from typing import List, Optional

import sqlparse

from config import get_config
from utils.errors import SQLValidationError

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates SQL queries for safety and compliance."""

    def __init__(self, config=None):
        """Initialize validator with configuration."""
        self.config = config or get_config()
        self.banned_keywords = [kw.upper() for kw in self.config.security.banned_sql_keywords]

    def validate_query(self, sql: str) -> None:
        """
        Validate SQL query for safety.

        Args:
            sql: SQL query to validate

        Raises:
            SQLValidationError: If query contains forbidden operations
        """
        # Basic validation
        if not sql or not sql.strip():
            raise SQLValidationError("Empty SQL query")

        # Check for banned keywords
        self._check_banned_keywords(sql)

        # Parse and validate statement type
        if self.config.security.select_only:
            self._validate_select_only(sql)

        # Check for required LIMIT if configured
        if self.config.security.require_explicit_limits:
            self._validate_has_limit(sql)

    def _check_banned_keywords(self, sql: str) -> None:
        """Check for banned SQL keywords."""
        # Normalize SQL for checking
        sql_upper = sql.upper()

        # Remove string literals to avoid false positives
        sql_normalized = self._remove_string_literals(sql_upper)

        # Check each banned keyword
        for keyword in self.banned_keywords:
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, sql_normalized):
                raise SQLValidationError(f"Forbidden SQL operation: {keyword} (read-only server)")

    def _remove_string_literals(self, sql: str) -> str:
        """Remove string literals from SQL to avoid false positives."""
        # Remove single-quoted strings
        sql = re.sub(r"'[^']*'", "''", sql)
        # Remove double-quoted strings (if any)
        sql = re.sub(r'"[^"]*"', '""', sql)
        # Remove backtick-quoted identifiers
        sql = re.sub(r"`[^`]*`", "``", sql)
        return sql

    def _validate_select_only(self, sql: str) -> None:
        """Ensure query is SELECT-only."""
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                raise SQLValidationError("Failed to parse SQL query")

            # Get the first statement
            statement = parsed[0]

            # Get the statement type
            stmt_type = statement.get_type()

            # Handle CTEs: sqlparse returns "UNKNOWN" for WITH statements
            # Check if it's a CTE by looking at the actual SQL
            sql_normalized = sql.strip().upper()
            if stmt_type == "UNKNOWN" and sql_normalized.startswith("WITH"):
                # This is a CTE (Common Table Expression) - allowed
                return

            if stmt_type != "SELECT":
                if sql_normalized.startswith("WITH"):
                    # CTE should be allowed
                    return
                else:
                    raise SQLValidationError(
                        f"Only SELECT statements and CTEs (WITH) are allowed, got: {stmt_type}"
                    )

        except SQLValidationError:
            raise
        except Exception as e:
            logger.warning(f"Failed to parse SQL for validation: {e}")
            # Fall back to simple check
            sql_normalized = sql.strip().upper()
            if not sql_normalized.startswith("SELECT") and not sql_normalized.startswith("WITH"):
                raise SQLValidationError("Only SELECT statements and CTEs (WITH) are allowed")

    def _validate_has_limit(self, sql: str) -> None:
        """Check if query has a LIMIT clause."""
        sql_upper = sql.upper()

        # Simple check for LIMIT keyword
        if " LIMIT " not in sql_upper:
            raise SQLValidationError("Query must include an explicit LIMIT clause")

    def add_limit_if_needed(self, sql: str, limit: Optional[int] = None) -> str:
        """
        Add LIMIT clause to query if not present.

        Args:
            sql: Original SQL query
            limit: Limit to apply (defaults to config default)

        Returns:
            SQL query with LIMIT clause
        """
        sql_upper = sql.upper().strip()

        # Check if already has LIMIT
        if " LIMIT " in sql_upper:
            return sql

        # Get limit value
        if limit is None:
            limit = self.config.limits.default_limit

        # Remove trailing semicolon if present
        sql_clean = sql.rstrip().rstrip(";")

        # Add LIMIT clause
        return f"{sql_clean} LIMIT {limit}"

    def extract_table_references(self, sql: str) -> List[str]:
        """
        Extract table references from SQL query.

        Args:
            sql: SQL query

        Returns:
            List of table references found in query
        """
        tables = []

        try:
            parsed = sqlparse.parse(sql)
            for statement in parsed:
                # This is simplified - a full implementation would need
                # more sophisticated parsing
                tokens = statement.tokens
                from_seen = False

                for token in tokens:
                    if token.ttype is None and token.value.upper() == "FROM":
                        from_seen = True
                    elif from_seen and token.ttype is None:
                        # Potential table reference
                        table_ref = token.value.strip()
                        if table_ref and table_ref.upper() not in (
                            "WHERE",
                            "GROUP",
                            "ORDER",
                            "LIMIT",
                        ):
                            tables.append(table_ref)
                            from_seen = False

        except Exception as e:
            logger.warning(f"Failed to extract table references: {e}")

        return tables


# Singleton instance
_validator: Optional[SQLValidator] = None


def get_validator(config=None) -> SQLValidator:
    """Get or create SQL validator instance."""
    global _validator
    if _validator is None:
        _validator = SQLValidator(config)
    return _validator
