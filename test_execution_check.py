#!/usr/bin/env python3
"""Test the execution.py safety check logic."""

# Your query as it might be received
union_query = """
-- Check event field patterns across tables
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

# Test the execution.py logic
query_upper = union_query.upper().strip()
print("Query starts with:")
print(repr(query_upper[:50]))
print()
print("Starts with SELECT?", query_upper.startswith("SELECT"))
print("Starts with WITH?", query_upper.startswith("WITH"))
print()
print("Would pass execution.py check?", 
      query_upper.startswith("SELECT") or query_upper.startswith("WITH"))
