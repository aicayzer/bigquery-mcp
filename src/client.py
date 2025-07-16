"""BigQuery client wrapper for cross-project access."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from google.auth import default
from google.cloud import bigquery
from google.cloud.bigquery.dataset import DatasetListItem
from google.cloud.bigquery.table import TableListItem
from google.oauth2 import service_account

from config import get_config
from utils.errors import (
    AuthenticationError,
    DatasetAccessError,
    InvalidTablePathError,
    ProjectAccessError,
    TableNotFoundError,
)

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Wrapper for BigQuery client with cross-project support and validation."""

    def __init__(self, config=None):
        """Initialize BigQuery client with configuration."""
        self.config = config or get_config()
        self._client = None
        # Simple context tracking for better UX
        self._last_project = None
        self._last_dataset = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the BigQuery client with appropriate credentials."""
        try:
            if self.config.service_account_path:
                # Use service account if specified
                logger.info(f"Using service account: {self.config.service_account_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.service_account_path,
                    scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
                )
                self._client = bigquery.Client(
                    project=self.config.billing_project,
                    credentials=credentials,
                    location=self.config.location,
                )
            else:
                # Use Application Default Credentials
                logger.info("Using Application Default Credentials")
                credentials, project = default(
                    scopes=["https://www.googleapis.com/auth/bigquery.readonly"]
                )
                # Use configured billing project or discovered project
                billing_project = self.config.billing_project or project
                if not billing_project:
                    raise AuthenticationError(
                        "No billing project specified and none could be determined from credentials"
                    )
                self._client = bigquery.Client(
                    project=billing_project,
                    credentials=credentials,
                    location=self.config.location,
                )

            logger.info(f"BigQuery client initialized with billing project: {self._client.project}")

        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise AuthenticationError(f"Failed to initialize BigQuery client: {str(e)}")

    @property
    def client(self) -> bigquery.Client:
        """Get the underlying BigQuery client."""
        if self._client is None:
            self._initialize_client()
        return self._client

    @property
    def billing_project(self) -> str:
        """Get the billing project ID."""
        return self.client.project

    def get_context_info(self) -> dict:
        """
        Get current context information for better user experience.

        Returns:
            Dict with current project/dataset context and available resources
        """
        context = {
            "billing_project": self.billing_project,
            "allowed_projects": list(self.config.allowed_projects)
            if self.config.allowed_projects
            else ["all"],
            "allowed_datasets": list(self.config.allowed_datasets)
            if self.config.allowed_datasets
            else ["all"],
            "last_accessed": {"project": self._last_project, "dataset": self._last_dataset},
            "location": self.config.location,
        }
        return context

    def update_context(self, project: str = None, dataset: str = None) -> None:
        """Update the context tracking for better UX."""
        if project:
            self._last_project = project
        if dataset:
            self._last_dataset = dataset

    def parse_table_path(self, table_path: str) -> Tuple[str, str, str]:
        """
        Parse table path into project, dataset, and table components.

        Args:
            table_path: Table reference as 'dataset.table' or 'project.dataset.table'

        Returns:
            Tuple of (project_id, dataset_id, table_id)

        Raises:
            InvalidTablePathError: If path format is invalid
            ProjectAccessError: If project is not allowed
            DatasetAccessError: If dataset is not allowed
        """
        parts = table_path.split(".")

        if len(parts) == 2:
            # dataset.table format - use billing project
            dataset, table = parts
            project = self.billing_project
        elif len(parts) == 3:
            # project.dataset.table format
            project, dataset, table = parts
        else:
            raise InvalidTablePathError(
                f"Invalid table path: '{table_path}'. "
                "Expected 'dataset.table' or 'project.dataset.table'"
            )

        # Validate project access
        if not self.config.is_project_allowed(project):
            allowed = ", ".join(self.config.get_allowed_projects())
            raise ProjectAccessError(
                f"Project '{project}' not in allowed list. Allowed projects: {allowed}"
            )

        # Validate dataset access
        if not self.config.is_dataset_allowed(project, dataset):
            project_config = self.config.get_project(project)
            patterns = ", ".join(project_config.datasets) if project_config else "none"
            raise DatasetAccessError(
                f"Dataset '{dataset}' not allowed in project '{project}'. "
                f"Allowed patterns: {patterns}"
            )

        # Update context tracking
        self.update_context(project=project, dataset=dataset)

        return project, dataset, table

    def parse_dataset_path(self, dataset_path: str) -> Tuple[str, str]:
        """
        Parse dataset path into project and dataset components.

        Args:
            dataset_path: Dataset reference as 'dataset' or 'project.dataset'

        Returns:
            Tuple of (project_id, dataset_id)
        """
        parts = dataset_path.split(".")

        if len(parts) == 1:
            # Just dataset - use billing project
            return self.billing_project, parts[0]
        elif len(parts) == 2:
            # project.dataset format
            return parts[0], parts[1]
        else:
            raise InvalidTablePathError(
                f"Invalid dataset path: '{dataset_path}'. Expected 'dataset' or 'project.dataset'"
            )

    def get_table(self, table_path: str) -> bigquery.Table:
        """
        Get table object with validation.

        Args:
            table_path: Table reference

        Returns:
            BigQuery Table object

        Raises:
            TableNotFoundError: If table doesn't exist
        """
        project, dataset, table = self.parse_table_path(table_path)
        table_ref = self.client.dataset(dataset, project=project).table(table)

        try:
            return self.client.get_table(table_ref)
        except Exception as e:
            if "Not found" in str(e):
                raise TableNotFoundError(
                    f"Table '{table}' not found in dataset '{project}.{dataset}'"
                )
            raise

    def list_datasets(self, project: Optional[str] = None) -> List[DatasetListItem]:
        """
        List datasets in a project, filtered by configuration.

        Args:
            project: Project ID (defaults to billing project)

        Returns:
            List of allowed datasets
        """
        target_project = project or self.billing_project

        if not self.config.is_project_allowed(target_project):
            raise ProjectAccessError(f"Project '{target_project}' not in allowed list")

        all_datasets = list(self.client.list_datasets(target_project))

        # Filter by allowed patterns
        allowed_datasets = []
        for dataset in all_datasets:
            if self.config.is_dataset_allowed(target_project, dataset.dataset_id):
                allowed_datasets.append(dataset)

        return allowed_datasets

    def list_tables(
        self, dataset_path: str, table_type: Optional[str] = None
    ) -> List[TableListItem]:
        """
        List tables in a dataset.

        Args:
            dataset_path: Dataset reference
            table_type: Filter by type ('TABLE', 'VIEW', 'MATERIALIZED_VIEW')

        Returns:
            List of tables
        """
        project, dataset = self.parse_dataset_path(dataset_path)

        # Validate access
        if not self.config.is_project_allowed(project):
            raise ProjectAccessError(f"Project '{project}' not in allowed list")

        if not self.config.is_dataset_allowed(project, dataset):
            raise DatasetAccessError(f"Dataset '{dataset}' not allowed in project '{project}'")

        dataset_ref = self.client.dataset(dataset, project=project)
        all_tables = list(self.client.list_tables(dataset_ref))

        if table_type:
            # Filter by type
            table_type_upper = table_type.upper()
            return [t for t in all_tables if t.table_type == table_type_upper]

        return all_tables

    def query(
        self,
        sql: str,
        project: Optional[str] = None,
        timeout: Optional[float] = None,
        max_results: Optional[int] = None,
    ) -> bigquery.QueryJob:
        """
        Execute a query with the appropriate project context.

        Args:
            sql: SQL query to execute
            project: Project to bill the query to (defaults to billing project)
            timeout: Query timeout in seconds
            max_results: Maximum number of results

        Returns:
            QueryJob object
        """
        target_project = project or self.billing_project

        if not self.config.is_project_allowed(target_project):
            raise ProjectAccessError(f"Project '{target_project}' not in allowed list")

        job_config = bigquery.QueryJobConfig()
        if max_results:
            job_config.max_results = max_results

        # Note: timeout parameter is passed to result() method, not query() method
        return self.client.query(sql, project=target_project, job_config=job_config)

    def get_table_schema(self, table_path: str) -> List[Dict[str, Any]]:
        """
        Get table schema as a list of field dictionaries.

        Args:
            table_path: Table reference

        Returns:
            List of schema field dictionaries
        """
        table = self.get_table(table_path)

        schema = []
        for field in table.schema:
            schema.append(
                {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description or "",
                }
            )

        return schema
