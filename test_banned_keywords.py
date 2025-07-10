#!/usr/bin/env python3
"""Test banned keyword validation on UNION query."""

import re

# Your query
union_query = """
SELECT 
  'stg_in_life_business_events' as table_name,
  COUNT(DISTINCT event_id) as distinct_event_ids,
  COUNT(DISTINCT event_name) as distinct_event_names,
  COUNT(DISTINCT event_type) as distinct_event_types,
  COUNT(*) as total_rows
FROM `august-cayzer-8793.business_banking_dataform.stg_in_life_business_events`
UNION ALL
SELECT 
  'stg_in_life_invitation_events',
  COUNT(DISTINCT event_id),
  COUNT(DISTINCT event_name),
  COUNT(DISTINCT event_type),
  COUNT(*)
FROM `august-cayzer-8793.business_banking_dataform.stg_in_life_invitation_events`
"""

# Banned keywords from config
banned_keywords = [
    "CREATE", "DELETE", "DROP", "TRUNCATE", "INSERT", "UPDATE", 
    "ALTER", "GRANT", "REVOKE", "MERGE", "CALL", "EXECUTE", "SCRIPT"
]

def remove_string_literals(sql: str) -> str:
    """Remove string literals from SQL to avoid false positives."""
    # Remove single-quoted strings
    sql = re.sub(r"'[^']*'", "''", sql)
    # Remove double-quoted strings (if any)
    sql = re.sub(r'"[^"]*"', '""', sql)
    # Remove backtick-quoted identifiers
    sql = re.sub(r"`[^`]*`", "``", sql)
    return sql

def check_banned_keywords(sql: str, banned_keywords: list) -> None:
    """Check for banned SQL keywords."""
    # Normalize SQL for checking
    sql_upper = sql.upper()
    
    # Remove string literals to avoid false positives
    sql_normalized = remove_string_literals(sql_upper)
    
    print("Normalized SQL:", sql_normalized[:200], "...")
    
    # Check each banned keyword
    for keyword in banned_keywords:
        # Use word boundaries to avoid partial matches
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, sql_normalized):
            print(f"FOUND BANNED KEYWORD: {keyword}")
            return
    
    print("No banned keywords found")

check_banned_keywords(union_query, banned_keywords)
