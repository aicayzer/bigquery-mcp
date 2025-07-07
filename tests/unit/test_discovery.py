"""Unit tests for discovery tools."""

import os
import sys
from datetime import datetime
from unittest.mock import Mock

import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))


class TestListProjects:
    """Tests for list_projects tool."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for discovery tools."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda x: x)
        mock_handle_error = lambda x: x
        mock_bq_client = Mock()
        mock_bq_client.billing_project = "test-project"
        mock_config = Mock()
        mock_formatter = Mock()
        mock_formatter.compact_mode = False

        return mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter

    def test_list_projects_standard_format(self, mock_dependencies):
        """Test listing projects in standard format."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        # Set up mock config
        mock_project = Mock()
        mock_project.project_id = "test-project"
        mock_project.project_name = "Test Project"
        mock_project.description = "Test project for unit tests"
        mock_project.datasets = ["test_*", "sample_*"]
        mock_config.projects = [mock_project]

        # Import and register tools
        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        # Call the function directly
        result = discovery.list_projects()

        assert result["status"] == "success"
        assert result["total_projects"] == 1
        assert result["billing_project"] == "test-project"
        assert len(result["projects"]) == 1

        project = result["projects"][0]
        assert project["project_id"] == "test-project"
        assert project["project_name"] == "Test Project"
        assert project["description"] == "Test project for unit tests"
        assert "dataset_patterns" in project
        assert project["dataset_patterns"] == ["test_*", "sample_*"]

    def test_list_projects_compact_format(self, mock_dependencies):
        """Test listing projects in compact format."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies
        mock_formatter.compact_mode = True

        # Set up mock config
        mock_project = Mock()
        mock_project.project_id = "test-project"
        mock_project.project_name = "Test Project"
        mock_project.description = "Test project"
        mock_project.datasets = ["test_*"]
        mock_config.projects = [mock_project]

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        result = discovery.list_projects()

        assert result["status"] == "success"
        project = result["projects"][0]
        assert "dataset_patterns" not in project  # Not included in compact mode

    def test_list_projects_multiple_projects(self, mock_dependencies):
        """Test listing multiple projects."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        # Create multiple mock projects
        project1 = Mock()
        project1.project_id = "project-1"
        project1.project_name = "Project One"
        project1.description = "First project"
        project1.datasets = ["prod_*"]

        project2 = Mock()
        project2.project_id = "project-2"
        project2.project_name = "Project Two"
        project2.description = "Second project"
        project2.datasets = ["test_*"]

        mock_config.projects = [project1, project2]

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        result = discovery.list_projects()

        assert result["total_projects"] == 2
        assert len(result["projects"]) == 2
        assert result["projects"][0]["project_id"] == "project-1"
        assert result["projects"][1]["project_id"] == "project-2"


class TestListDatasets:
    """Tests for list_datasets tool."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for discovery tools."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda x: x)
        mock_handle_error = lambda x: x
        mock_bq_client = Mock()
        mock_bq_client.billing_project = "test-project"
        mock_config = Mock()
        mock_formatter = Mock()
        mock_formatter.compact_mode = False

        return mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter

    def test_list_datasets_default_project(self, mock_dependencies):
        """Test listing datasets in default billing project."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        # Mock dataset objects
        mock_dataset1 = Mock()
        mock_dataset1.dataset_id = "test_dataset1"
        mock_dataset1.reference = "test-project.test_dataset1"

        mock_dataset2 = Mock()
        mock_dataset2.dataset_id = "sample_dataset"
        mock_dataset2.reference = "test-project.sample_dataset"

        # Mock dataset details
        mock_dataset1_full = Mock(
            dataset_id="test_dataset1",
            location="US",
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            description="Test dataset 1",
            labels={},
        )

        mock_dataset2_full = Mock(
            dataset_id="sample_dataset",
            location="EU",
            created=datetime(2024, 1, 3),
            modified=datetime(2024, 1, 4),
            description="Sample dataset",
            labels={"env": "test"},
        )

        # Configure mocks
        mock_config.is_project_allowed.return_value = True
        mock_config.get_project.return_value = Mock(project_name="Test Project")
        mock_bq_client.list_datasets.return_value = [mock_dataset1, mock_dataset2]
        mock_bq_client.client.get_dataset.side_effect = [
            mock_dataset1_full,
            mock_dataset2_full,
        ]

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        result = discovery.list_datasets()

        assert result["status"] == "success"
        assert result["project"] == "test-project"
        assert result["total_datasets"] == 2
        assert len(result["datasets"]) == 2

        # Check first dataset
        ds1 = result["datasets"][0]
        assert ds1["dataset_id"] == "test_dataset1"
        assert ds1["location"] == "US"
        assert ds1["description"] == "Test dataset 1"
        assert "created" in ds1
        assert "modified" in ds1

    def test_list_datasets_project_not_allowed(self, mock_dependencies):
        """Test error when project is not in allowed list."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        mock_config.is_project_allowed.return_value = False

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        from utils.errors import ProjectAccessError

        with pytest.raises(ProjectAccessError) as exc_info:
            discovery.list_datasets(project="forbidden-project")

        assert "forbidden-project" in str(exc_info.value)
        assert "not in allowed list" in str(exc_info.value)

    def test_list_datasets_permission_denied(self, mock_dependencies):
        """Test handling permission denied errors."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        mock_config.is_project_allowed.return_value = True
        mock_bq_client.list_datasets.side_effect = Exception("403 Permission denied")

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        from utils.errors import ProjectAccessError

        with pytest.raises(ProjectAccessError) as exc_info:
            discovery.list_datasets()

        assert "Permission denied" in str(exc_info.value)
        assert "bigquery.datasets.list" in str(exc_info.value)


class TestListTables:
    """Tests for list_tables tool."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for discovery tools."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda x: x)
        mock_handle_error = lambda x: x
        mock_bq_client = Mock()
        mock_bq_client.billing_project = "test-project"
        mock_config = Mock()
        mock_formatter = Mock()
        mock_formatter.compact_mode = False

        return mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter

    def test_list_tables_all_types(self, mock_dependencies):
        """Test listing all table types."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        # Mock table objects
        mock_table1 = Mock()
        mock_table1.table_id = "articles"
        mock_table1.reference = "test-project.test_dataset.articles"

        mock_view1 = Mock()
        mock_view1.table_id = "article_summary"
        mock_view1.reference = "test-project.test_dataset.article_summary"

        # Mock full table metadata
        mock_table1_full = Mock(
            table_id="articles",
            table_type="TABLE",
            created=datetime(2024, 1, 1),
            modified=datetime(2024, 1, 2),
            num_rows=1000,
            num_bytes=1048576,  # 1MB
            description="News articles",
            location="US",
            schema=[Mock(), Mock()],  # 2 fields
            time_partitioning=None,
            clustering_fields=None,
        )

        mock_view1_full = Mock(
            table_id="article_summary",
            table_type="VIEW",
            created=datetime(2024, 1, 3),
            modified=datetime(2024, 1, 4),
            num_rows=None,
            num_bytes=None,
            description="Article summary view",
            location="US",
            schema=[Mock()],  # 1 field
            time_partitioning=None,
            clustering_fields=None,
        )

        # Configure mocks
        mock_bq_client.parse_dataset_path.return_value = (
            "test-project",
            "test_dataset",
        )
        mock_config.is_dataset_allowed.return_value = True
        mock_config.get_project.return_value = Mock(datasets=["test_*"])
        mock_bq_client.list_tables.return_value = [mock_table1, mock_view1]
        mock_bq_client.client.get_table.side_effect = [
            mock_table1_full,
            mock_view1_full,
        ]

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        result = discovery.list_tables("test_dataset")

        assert result["status"] == "success"
        assert result["project"] == "test-project"
        assert result["dataset"] == "test_dataset"
        assert result["total_tables"] == 2

        # Check table (tables are sorted by table_id)
        table = result["tables"][0]
        assert table["table_id"] == "article_summary"  # Comes first alphabetically
        assert table["table_type"] == "VIEW"

    def test_list_tables_invalid_type(self, mock_dependencies):
        """Test error with invalid table type."""
        mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter = mock_dependencies

        from tools import discovery

        discovery.register_discovery_tools(
            mock_mcp, mock_handle_error, mock_bq_client, mock_config, mock_formatter
        )

        with pytest.raises(ValueError) as exc_info:
            discovery.list_tables("test_dataset", table_type="invalid")

        assert "Invalid table_type" in str(exc_info.value)
        assert "all, table, view, materialized_view" in str(exc_info.value)
