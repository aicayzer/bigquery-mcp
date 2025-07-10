#!/usr/bin/env python3
"""Test the fixed execution safety check."""

import re


def test_query_validation(query):
    """Test the new query validation logic."""
    query_normalized = query.strip()
    # Remove single-line comments (-- comments)
    query_normalized = re.sub(r"--.*?(?=\n|$)", "", query_normalized, flags=re.MULTILINE)
    # Remove multi-line comments (/* comments */)
    query_normalized = re.sub(r"/\*.*?\*/", "", query_normalized, flags=re.DOTALL)
    # Remove extra whitespace and get first significant token
    query_normalized = query_normalized.strip().upper()

    print(f"Normalized query starts with: {repr(query_normalized[:50])}")

    # Check if it's a SELECT query (WITH is allowed for CTEs)
    valid = query_normalized.startswith("SELECT") or query_normalized.startswith("WITH")
    print(f"Valid: {valid}")
    return valid


# Test cases
test_queries = [
    # Your original query with comment
    """-- Check event field patterns across tables
SELECT 
  'stg_in_life_business_events' as table_name
FROM `august-cayzer-8793.business_banking_dataform.stg_in_life_business_events`
UNION ALL
SELECT 
  'stg_in_life_invitation_events'
FROM `august-cayzer-8793.business_banking_dataform.stg_in_life_invitation_events`""",
    # CTE query
    """WITH cte AS (SELECT * FROM table)
SELECT * FROM cte""",
    # Multi-line comment
    """/* This is a comment */
SELECT * FROM table""",
    # Should fail - DELETE
    """-- Comment
DELETE FROM table""",
    # Simple SELECT
    "SELECT * FROM table",
]

for i, query in enumerate(test_queries, 1):
    print(f"\n=== Test {i} ===")
    print("Query:", query[:50].replace("\n", "\\n"), "...")
    test_query_validation(query)
