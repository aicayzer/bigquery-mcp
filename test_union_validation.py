#!/usr/bin/env python3
"""Quick test to see how sqlparse handles UNION queries."""

import sqlparse

# Your query
union_query = """
SELECT 
  'stg_in_life_business_events' as table_name,
  COUNT(DISTINCT event_id) as distinct_event_ids
FROM `august-cayzer-8793.business_banking_dataform.stg_in_life_business_events`
UNION ALL
SELECT 
  'stg_in_life_invitation_events',
  COUNT(DISTINCT event_id)
FROM `august-cayzer-8793.business_banking_dataform.stg_in_life_invitation_events`
"""

# Simple SELECT query
simple_query = "SELECT * FROM table"

print("=== UNION Query ===")
parsed_union = sqlparse.parse(union_query)
if parsed_union:
    stmt = parsed_union[0]
    print(f"Statement type: {stmt.get_type()}")
    print(f"First token: {stmt.tokens[0] if stmt.tokens else 'None'}")

print("\n=== Simple SELECT Query ===")
parsed_simple = sqlparse.parse(simple_query)
if parsed_simple:
    stmt = parsed_simple[0]
    print(f"Statement type: {stmt.get_type()}")
    print(f"First token: {stmt.tokens[0] if stmt.tokens else 'None'}")
