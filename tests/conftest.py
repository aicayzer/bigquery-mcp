"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock, patch
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client for testing."""
    with patch('google.cloud.bigquery.Client') as mock_client:
        yield mock_client


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'bigquery': {
            'billing_project': 'test-project',
            'service_account_path': ''
        },
        'projects': [
            {
                'project_id': 'test-project',
                'project_name': 'Test Project',
                'description': 'Test project for unit tests',
                'datasets': ['test_*', 'sample_*']
            }
        ],
        'limits': {
            'default_row_limit': 20,
            'max_query_timeout': 60
        },
        'security': {
            'banned_sql_keywords': ['CREATE', 'DROP', 'DELETE']
        }
    }


@pytest.fixture
def sample_table_schema():
    """Sample BigQuery table schema."""
    return [
        {'name': 'id', 'type': 'STRING', 'description': 'Unique identifier'},
        {'name': 'created_at', 'type': 'TIMESTAMP', 'description': 'Creation timestamp'},
        {'name': 'amount', 'type': 'NUMERIC', 'description': 'Transaction amount'}
    ]
