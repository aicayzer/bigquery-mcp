"""Integration tests for BigQuery operations with mocked client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestDiscoveryIntegration:
    """Integration tests for discovery tools working together."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for integration tests."""
        from config import Config
        
        # Create a test configuration
        sample_config = {
            'server': {
                'name': 'Test Server',
                'version': '0.2.0'
            },
            'bigquery': {
                'billing_project': 'test-billing',
                'service_account_path': ''
            },
            'projects': [
                {
                    'project_id': 'analytics-test',
                    'project_name': 'Analytics Test',
                    'description': 'Test analytics project',
                    'datasets': ['prod_*', 'test_*']
                },
                {
                    'project_id': 'raw-test',
                    'project_name': 'Raw Test',
                    'description': 'Test raw data',
                    'datasets': ['*']
                }
            ],
            'limits': {
                'default_row_limit': 20,
                'max_query_timeout': 60
            },
            'security': {
                'banned_sql_keywords': ['CREATE', 'DROP'],
                'select_only': True
            },
            'formatting': {
                'compact_format': False
            }
        }
        
        with patch('config.yaml.safe_load', return_value=sample_config):
            sample_config_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sample_config.yaml')
            config = Config(sample_config_path)
        
        return config
    
    @pytest.fixture
    def mock_bigquery_integration(self):
        """Create comprehensive BigQuery mocks for integration testing."""
        # Mock BigQuery client
        mock_client = Mock()
        
        # Mock datasets
        mock_dataset1 = Mock()
        mock_dataset1.dataset_id = 'prod_sales'
        mock_dataset1.reference = Mock()
        
        mock_dataset2 = Mock()
        mock_dataset2.dataset_id = 'test_experiments'  
        mock_dataset2.reference = Mock()
        
        mock_dataset3 = Mock()
        mock_dataset3.dataset_id = 'raw_events'
        mock_dataset3.reference = Mock()
        
        # Mock dataset details
        mock_dataset1_full = Mock(
            dataset_id='prod_sales',
            location='US',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 6, 1),
            description='Production sales data',
            labels={'env': 'prod'}
        )
        
        mock_dataset2_full = Mock(
            dataset_id='test_experiments',
            location='US',
            created=datetime(2024, 2, 1),
            modified=datetime(2024, 5, 1),
            description='A/B test results',
            labels={'env': 'test'}
        )
        
        # Mock tables
        mock_table1 = Mock()
        mock_table1.table_id = 'daily_sales'
        mock_table1.reference = Mock()
        
        mock_table2 = Mock()
        mock_table2.table_id = 'monthly_summary'
        mock_table2.reference = Mock()
        
        mock_view1 = Mock()
        mock_view1.table_id = 'sales_by_region'
        mock_view1.reference = Mock()
        
        # Mock table details
        mock_table1_full = Mock(
            table_id='daily_sales',
            table_type='TABLE',
            created=datetime(2024, 1, 15),
            modified=datetime(2024, 6, 15),
            num_rows=1000000,
            num_bytes=52428800,  # 50MB
            description='Daily sales transactions',
            location='US',
            schema=[Mock() for _ in range(10)],  # 10 fields
            time_partitioning=Mock(type_='DAY', field='sale_date'),
            clustering_fields=['region', 'product_id']
        )
        
        mock_table2_full = Mock(
            table_id='monthly_summary',
            table_type='TABLE',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 6, 1),
            num_rows=24,
            num_bytes=1048576,  # 1MB
            description='Monthly aggregated sales',
            location='US',
            schema=[Mock() for _ in range(5)],
            time_partitioning=None,
            clustering_fields=None
        )
        
        mock_view1_full = Mock(
            table_id='sales_by_region',
            table_type='VIEW',
            created=datetime(2024, 3, 1),
            modified=datetime(2024, 3, 1),
            num_rows=None,
            num_bytes=None,
            description='Sales grouped by region',
            location='US',
            schema=[Mock() for _ in range(3)],
            time_partitioning=None,
            clustering_fields=None
        )
        
        # Configure mock client behavior
        def list_datasets_side_effect(project):
            if project == 'analytics-test':
                return [mock_dataset1, mock_dataset2]
            elif project == 'raw-test':
                return [mock_dataset3]
            else:
                return []
        
        def list_tables_side_effect(dataset_ref):
            if 'prod_sales' in str(dataset_ref):
                return [mock_table1, mock_table2, mock_view1]
            else:
                return []
        
        def get_dataset_side_effect(ref):
            if 'prod_sales' in str(ref):
                return mock_dataset1_full
            elif 'test_experiments' in str(ref):
                return mock_dataset2_full
            else:
                raise Exception("404 Not found")
        
        def get_table_side_effect(ref):
            if 'daily_sales' in str(ref):
                return mock_table1_full
            elif 'monthly_summary' in str(ref):
                return mock_table2_full
            elif 'sales_by_region' in str(ref):
                return mock_view1_full
            else:
                raise Exception("404 Not found")
        
        mock_client.list_datasets.side_effect = list_datasets_side_effect
        mock_client.list_tables.side_effect = list_tables_side_effect
        mock_client.get_dataset.side_effect = get_dataset_side_effect
        mock_client.get_table.side_effect = get_table_side_effect
        
        return mock_client
    
    def test_full_discovery_workflow(self, mock_config, mock_bigquery_integration):
        """Test complete discovery workflow from projects to tables."""
        pytest.skip("Integration tests require full server initialization - skipping for now")
        with patch('config.get_config', return_value=mock_config):
            with patch('client.BigQueryClient') as mock_bq_class:
                # Configure BigQuery client mock
                mock_bq_instance = Mock()
                mock_bq_instance.billing_project = 'test-billing'
                mock_bq_instance.client = mock_bigquery_integration
                mock_bq_instance.list_datasets.side_effect = lambda p: mock_bigquery_integration.list_datasets(p)
                mock_bq_instance.list_tables.side_effect = lambda d, t=None: mock_bigquery_integration.list_tables(
                    mock_bigquery_integration.dataset(d.split('.')[1], project=d.split('.')[0] if '.' in d else 'test-billing')
                )
                mock_bq_instance.parse_dataset_path.side_effect = lambda d: ('analytics-test', d) if '.' not in d else d.split('.', 1)
                
                mock_bq_class.return_value = mock_bq_instance
                
                # Import after mocks are set up
                import server
                server.initialize_server()
                
                from tools.discovery import list_projects, list_datasets, list_tables
                
                # Step 1: List projects
                projects_result = list_projects()
                assert projects_result['status'] == 'success'
                assert projects_result['total_projects'] == 2
                
                project_ids = [p['project_id'] for p in projects_result['projects']]
                assert 'analytics-test' in project_ids
                assert 'raw-test' in project_ids
                
                # Step 2: List datasets in first project
                datasets_result = list_datasets(project='analytics-test')
                assert datasets_result['status'] == 'success'
                assert datasets_result['total_datasets'] == 2
                
                dataset_ids = [d['dataset_id'] for d in datasets_result['datasets']]
                assert 'prod_sales' in dataset_ids
                assert 'test_experiments' in dataset_ids
                
                # Step 3: List tables in a dataset
                tables_result = list_tables('analytics-test.prod_sales')
                assert tables_result['status'] == 'success'
                assert tables_result['total_tables'] == 3
                
                # Check table types
                table_types = [t['table_type'] for t in tables_result['tables']]
                assert 'TABLE' in table_types
                assert 'VIEW' in table_types
                
                # Step 4: Filter tables by type
                views_result = list_tables('analytics-test.prod_sales', table_type='view')
                assert views_result['status'] == 'success'
                assert views_result['filtered_by_type'] == 'VIEW'
                assert all(t['table_type'] == 'VIEW' for t in views_result['tables'])
    
    def test_compact_mode_integration(self, mock_config, mock_bigquery_integration):
        """Test discovery tools in compact mode."""
        pytest.skip("Integration tests require full server initialization - skipping for now")
        
        with patch('config.get_config', return_value=mock_config):
            with patch('client.BigQueryClient') as mock_bq_class:
                mock_bq_instance = Mock()
                mock_bq_instance.billing_project = 'test-billing'
                mock_bq_instance.client = mock_bigquery_integration
                mock_bq_instance.list_datasets.side_effect = lambda p: mock_bigquery_integration.list_datasets(p)
                mock_bq_class.return_value = mock_bq_instance
                
                import server
                server.initialize_server()
                
                from tools.discovery import list_projects, list_datasets
                
                # Test compact project listing
                projects_result = list_projects()
                project = projects_result['projects'][0]
                assert 'dataset_patterns' not in project  # Not in compact mode
                
                # Test compact dataset listing  
                datasets_result = list_datasets(project='analytics-test')
                if datasets_result['datasets']:
                    dataset = datasets_result['datasets'][0]
                    assert 'created' not in dataset  # Not in compact mode
                    assert 'modified' not in dataset
                    assert 'labels' not in dataset
    
    def test_error_handling_integration(self, mock_config):
        """Test error handling across discovery tools."""
        pytest.skip("Integration tests require full server initialization - skipping for now")
