"""Unit tests for discovery tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Import test fixtures
from tests.conftest import sample_config, mock_bigquery_client, sample_table_schema


class TestListProjects:
    """Tests for list_projects tool."""
    
    def test_list_projects_standard_format(self, sample_config):
        """Test listing projects in standard format."""
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.formatter.compact_mode', False):
                with patch('tools.discovery.bq_client.billing_project', 'test-project'):
                    from tools.discovery import list_projects
                    
                    result = list_projects()
                    
                    assert result['status'] == 'success'
                    assert result['total_projects'] == 1
                    assert result['billing_project'] == 'test-project'
                    assert len(result['projects']) == 1
                    
                    project = result['projects'][0]
                    assert project['project_id'] == 'test-project'
                    assert project['project_name'] == 'Test Project'
                    assert project['description'] == 'Test project for unit tests'
                    assert 'dataset_patterns' in project
                    assert project['dataset_patterns'] == ['test_*', 'sample_*']
    
    def test_list_projects_compact_format(self, sample_config):
        """Test listing projects in compact format."""
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.formatter.compact_mode', True):
                with patch('tools.discovery.bq_client.billing_project', 'test-project'):
                    from tools.discovery import list_projects
                    
                    result = list_projects()
                    
                    assert result['status'] == 'success'
                    project = result['projects'][0]
                    assert 'dataset_patterns' not in project  # Not included in compact mode
    
    def test_list_projects_multiple_projects(self):
        """Test listing multiple projects."""
        multi_config = Mock()
        multi_config.projects = [
            Mock(
                project_id='project-1',
                project_name='Project One',
                description='First project',
                datasets=['prod_*']
            ),
            Mock(
                project_id='project-2',
                project_name='Project Two',
                description='Second project',
                datasets=['test_*']
            )
        ]
        
        with patch('tools.discovery.config', multi_config):
            with patch('tools.discovery.formatter.compact_mode', False):
                with patch('tools.discovery.bq_client.billing_project', 'project-1'):
                    from tools.discovery import list_projects
                    
                    result = list_projects()
                    
                    assert result['total_projects'] == 2
                    assert len(result['projects']) == 2
                    assert result['projects'][0]['project_id'] == 'project-1'
                    assert result['projects'][1]['project_id'] == 'project-2'


class TestListDatasets:
    """Tests for list_datasets tool."""
    
    def test_list_datasets_default_project(self, sample_config, mock_bigquery_client):
        """Test listing datasets in default billing project."""
        # Mock dataset objects
        mock_dataset1 = Mock()
        mock_dataset1.dataset_id = 'test_dataset1'
        mock_dataset1.reference = 'test-project.test_dataset1'
        
        mock_dataset2 = Mock()
        mock_dataset2.dataset_id = 'sample_dataset'
        mock_dataset2.reference = 'test-project.sample_dataset'
        
        # Mock dataset details
        mock_dataset1_full = Mock(
            dataset_id='test_dataset1',
            location='US',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            description='Test dataset 1',
            labels={}
        )
        
        mock_dataset2_full = Mock(
            dataset_id='sample_dataset',
            location='EU',
            created=datetime(2024, 1, 3),
            modified=datetime(2024, 1, 4),
            description='Sample dataset',
            labels={'env': 'test'}
        )
        
        # Mock BigQuery client behavior
        mock_bq_client = Mock()
        mock_bq_client.billing_project = 'test-project'
        mock_bq_client.list_datasets.return_value = [mock_dataset1, mock_dataset2]
        mock_bq_client.client.get_dataset.side_effect = [mock_dataset1_full, mock_dataset2_full]
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                with patch('tools.discovery.formatter.compact_mode', False):
                    from tools.discovery import list_datasets
                    
                    result = list_datasets()
                    
                    assert result['status'] == 'success'
                    assert result['project'] == 'test-project'
                    assert result['total_datasets'] == 2
                    assert len(result['datasets']) == 2
                    
                    # Check first dataset
                    ds1 = result['datasets'][0]
                    assert ds1['dataset_id'] == 'test_dataset1'
                    assert ds1['location'] == 'US'
                    assert ds1['description'] == 'Test dataset 1'
                    assert 'created' in ds1
                    assert 'modified' in ds1
    
    def test_list_datasets_specific_project(self, sample_config):
        """Test listing datasets in specific project."""
        mock_bq_client = Mock()
        mock_bq_client.billing_project = 'billing-project'
        mock_bq_client.list_datasets.return_value = []
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                from tools.discovery import list_datasets
                
                result = list_datasets(project='test-project')
                
                mock_bq_client.list_datasets.assert_called_once_with('test-project')
                assert result['project'] == 'test-project'
    
    def test_list_datasets_project_not_allowed(self, sample_config):
        """Test error when project is not in allowed list."""
        with patch('tools.discovery.config', sample_config):
            from tools.discovery import list_datasets
            from utils.errors import ProjectAccessError
            
            with pytest.raises(ProjectAccessError) as exc_info:
                list_datasets(project='forbidden-project')
            
            assert 'forbidden-project' in str(exc_info.value)
            assert 'not in allowed list' in str(exc_info.value)
    
    def test_list_datasets_permission_denied(self, sample_config):
        """Test handling permission denied errors."""
        mock_bq_client = Mock()
        mock_bq_client.billing_project = 'test-project'
        mock_bq_client.list_datasets.side_effect = Exception("403 Permission denied")
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                from tools.discovery import list_datasets
                from utils.errors import ProjectAccessError
                
                with pytest.raises(ProjectAccessError) as exc_info:
                    list_datasets()
                
                assert 'Permission denied' in str(exc_info.value)
                assert 'bigquery.datasets.list' in str(exc_info.value)
    
    def test_list_datasets_compact_format(self, sample_config):
        """Test listing datasets in compact format."""
        mock_dataset = Mock()
        mock_dataset.dataset_id = 'test_dataset'
        mock_dataset.reference = 'test-project.test_dataset'
        
        mock_dataset_full = Mock(
            dataset_id='test_dataset',
            location='US',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            description='Test dataset',
            labels={}
        )
        
        mock_bq_client = Mock()
        mock_bq_client.billing_project = 'test-project'
        mock_bq_client.list_datasets.return_value = [mock_dataset]
        mock_bq_client.client.get_dataset.return_value = mock_dataset_full
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                with patch('tools.discovery.formatter.compact_mode', True):
                    from tools.discovery import list_datasets
                    
                    result = list_datasets()
                    
                    dataset = result['datasets'][0]
                    assert 'dataset_id' in dataset
                    assert 'location' in dataset
                    assert 'description' in dataset  # Included because it has a value
                    assert 'created' not in dataset  # Not included in compact mode
                    assert 'modified' not in dataset
                    assert 'labels' not in dataset


class TestListTables:
    """Tests for list_tables tool."""
    
    def test_list_tables_all_types(self, sample_config):
        """Test listing all table types."""
        # Mock table objects
        mock_table1 = Mock()
        mock_table1.table_id = 'table1'
        mock_table1.reference = 'test-project.test_dataset.table1'
        
        mock_view1 = Mock()
        mock_view1.table_id = 'view1'
        mock_view1.reference = 'test-project.test_dataset.view1'
        
        # Mock full table metadata
        mock_table1_full = Mock(
            table_id='table1',
            table_type='TABLE',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            num_rows=1000,
            num_bytes=1048576,  # 1MB
            description='Test table',
            location='US',
            schema=[Mock(), Mock()],  # 2 fields
            time_partitioning=None,
            clustering_fields=None
        )
        
        mock_view1_full = Mock(
            table_id='view1',
            table_type='VIEW',
            created=datetime(2024, 1, 3),
            modified=datetime(2024, 1, 4),
            num_rows=None,
            num_bytes=None,
            description='Test view',
            location='US',
            schema=[Mock()],  # 1 field
            time_partitioning=None,
            clustering_fields=None
        )
        
        mock_bq_client = Mock()
        mock_bq_client.parse_dataset_path.return_value = ('test-project', 'test_dataset')
        mock_bq_client.list_tables.return_value = [mock_table1, mock_view1]
        mock_bq_client.client.get_table.side_effect = [mock_table1_full, mock_view1_full]
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                with patch('tools.discovery.formatter.compact_mode', False):
                    from tools.discovery import list_tables
                    
                    result = list_tables('test_dataset')
                    
                    assert result['status'] == 'success'
                    assert result['project'] == 'test-project'
                    assert result['dataset'] == 'test_dataset'
                    assert result['total_tables'] == 2
                    
                    # Check table
                    table = result['tables'][0]
                    assert table['table_id'] == 'table1'
                    assert table['table_type'] == 'TABLE'
                    assert table['num_rows'] == 1000
                    assert table['size_mb'] == 1.0
                    assert table['schema_field_count'] == 2
                    
                    # Check view
                    view = result['tables'][1]
                    assert view['table_id'] == 'view1'
                    assert view['table_type'] == 'VIEW'
                    assert view['num_rows'] == 0  # None becomes 0
                    assert view['size_mb'] == 0.0
    
    def test_list_tables_filtered_by_type(self, sample_config):
        """Test filtering tables by type."""
        mock_bq_client = Mock()
        mock_bq_client.parse_dataset_path.return_value = ('test-project', 'test_dataset')
        mock_bq_client.list_tables.return_value = []
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                from tools.discovery import list_tables
                
                result = list_tables('test_dataset', table_type='view')
                
                mock_bq_client.list_tables.assert_called_once_with('test_dataset', 'VIEW')
                assert result['filtered_by_type'] == 'VIEW'
    
    def test_list_tables_invalid_type(self, sample_config):
        """Test error with invalid table type."""
        with patch('tools.discovery.config', sample_config):
            from tools.discovery import list_tables
            
            with pytest.raises(ValueError) as exc_info:
                list_tables('test_dataset', table_type='invalid')
            
            assert 'Invalid table_type' in str(exc_info.value)
            assert 'all, table, view, materialized_view' in str(exc_info.value)
    
    def test_list_tables_dataset_not_allowed(self, sample_config):
        """Test error when dataset doesn't match patterns."""
        mock_bq_client = Mock()
        mock_bq_client.parse_dataset_path.return_value = ('test-project', 'forbidden_dataset')
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                from tools.discovery import list_tables
                from utils.errors import DatasetAccessError
                
                with pytest.raises(DatasetAccessError) as exc_info:
                    list_tables('forbidden_dataset')
                
                assert 'forbidden_dataset' in str(exc_info.value)
                assert 'not accessible' in str(exc_info.value)
    
    def test_list_tables_compact_format(self, sample_config):
        """Test listing tables in compact format."""
        mock_table = Mock()
        mock_table.table_id = 'table1'
        mock_table.reference = 'test-project.test_dataset.table1'
        
        mock_table_full = Mock(
            table_id='table1',
            table_type='TABLE',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            num_rows=5000,
            num_bytes=5242880,  # 5MB
            description='',
            location='US',
            schema=[],
            time_partitioning=Mock(type_='DAY', field='created_at'),
            clustering_fields=['user_id']
        )
        
        mock_bq_client = Mock()
        mock_bq_client.parse_dataset_path.return_value = ('test-project', 'test_dataset')
        mock_bq_client.list_tables.return_value = [mock_table]
        mock_bq_client.client.get_table.return_value = mock_table_full
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                with patch('tools.discovery.formatter.compact_mode', True):
                    from tools.discovery import list_tables
                    
                    result = list_tables('test_dataset')
                    
                    table = result['tables'][0]
                    assert 'table_id' in table
                    assert 'type' in table  # Shortened key name
                    assert 'rows' in table
                    assert 'size_mb' in table
                    assert table['size_mb'] == 5.0
                    
                    # These should not be in compact format
                    assert 'created' not in table
                    assert 'modified' not in table
                    assert 'location' not in table
                    assert 'partitioning' not in table
                    assert 'clustering_fields' not in table
                    assert 'description' not in table  # Empty description excluded
    
    def test_list_tables_with_partitioning_and_clustering(self, sample_config):
        """Test tables with partitioning and clustering info."""
        mock_table = Mock()
        mock_table.table_id = 'partitioned_table'
        mock_table.reference = 'test-project.test_dataset.partitioned_table'
        
        mock_table_full = Mock(
            table_id='partitioned_table',
            table_type='TABLE',
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            num_rows=10000,
            num_bytes=10485760,
            description='Partitioned and clustered table',
            location='US',
            schema=[Mock()],
            time_partitioning=Mock(type_='DAY', field='event_date'),
            clustering_fields=['user_id', 'event_type']
        )
        
        mock_bq_client = Mock()
        mock_bq_client.parse_dataset_path.return_value = ('test-project', 'test_dataset')
        mock_bq_client.list_tables.return_value = [mock_table]
        mock_bq_client.client.get_table.return_value = mock_table_full
        
        with patch('tools.discovery.config', sample_config):
            with patch('tools.discovery.bq_client', mock_bq_client):
                with patch('tools.discovery.formatter.compact_mode', False):
                    from tools.discovery import list_tables
                    
                    result = list_tables('test_dataset')
                    
                    table = result['tables'][0]
                    assert 'partitioning' in table
                    assert table['partitioning']['type'] == 'DAY'
                    assert table['partitioning']['field'] == 'event_date'
                    assert table['clustering_fields'] == ['user_id', 'event_type']
