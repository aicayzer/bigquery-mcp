"""Configuration management for BigQuery MCP Server."""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ProjectConfig:
    """Configuration for a single BigQuery project."""

    project_id: str
    project_name: str
    description: str = ""
    datasets: List[str] = field(default_factory=list)

    def is_dataset_allowed(self, dataset_id: str) -> bool:
        """Check if dataset matches allowed patterns."""
        if not self.datasets:
            return False

        import fnmatch

        return any(fnmatch.fnmatch(dataset_id, pattern) for pattern in self.datasets)


@dataclass
class SecurityConfig:
    """Security settings configuration."""

    banned_sql_keywords: List[str] = field(default_factory=list)
    select_only: bool = True
    require_explicit_limits: bool = False


@dataclass
class LimitsConfig:
    """Query and response limits configuration."""

    default_limit: int = 20
    max_query_timeout: int = 20
    max_limit: int = 10000
    max_bytes_processed: int = 1073741824  # 1GB


@dataclass
class FormattingConfig:
    """Response formatting configuration."""

    compact_format: bool = False


class Config:
    """Main configuration manager for BigQuery MCP Server."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file and environment."""
        if config_path is None:
            config_path = self._find_config_file()

        self.config_path = config_path
        self._from_cli_args = False  # Indicate this instance was created from config file
        self._raw_config = self._load_yaml(config_path)
        self._parse_config()
        self._apply_env_overrides()

    @classmethod
    def from_cli_args(
        cls,
        project_patterns: Dict[str, List[str]],
        billing_project: Optional[str] = None,
        location: str = "EU",
        log_level: str = "INFO",
        log_queries: bool = True,
        log_results: bool = False,
        timeout: int = 20,
        max_limit: int = 10000,
        max_bytes_processed: int = 1073741824,
        compact_format: bool = False,
        select_only: bool = True,
        require_explicit_limits: bool = False,
        banned_keywords: str = "CREATE,DELETE,DROP,TRUNCATE,ALTER,INSERT,UPDATE",
    ):
        """Create configuration from command-line arguments."""
        instance = cls.__new__(cls)
        instance.config_path = None
        instance._raw_config = {}
        instance._from_cli_args = True  # Indicate that this instance was created from CLI args

        # Server info
        instance.server_name = "BigQuery MCP Server"
        instance.server_version = "1.1.1"

        # BigQuery settings
        instance.billing_project = billing_project or os.getenv("BIGQUERY_BILLING_PROJECT", "")
        instance.service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        instance.location = location

        # Projects from CLI patterns
        instance.projects = []
        for project_id, dataset_patterns in project_patterns.items():
            instance.projects.append(
                ProjectConfig(
                    project_id=project_id,
                    project_name=project_id,
                    description=f"Project {project_id} (configured via CLI)",
                    datasets=dataset_patterns,
                )
            )

        # Security settings from CLI args
        banned_keywords_list = [kw.strip().upper() for kw in banned_keywords.split(",")]
        instance.security = SecurityConfig(
            banned_sql_keywords=banned_keywords_list,
            select_only=select_only,
            require_explicit_limits=require_explicit_limits,
        )

        # Limits from CLI args
        instance.limits = LimitsConfig(
            default_limit=20,  # Keep default for backward compatibility
            max_query_timeout=timeout,
            max_limit=max_limit,
            max_bytes_processed=max_bytes_processed,
        )

        # Formatting from CLI args
        instance.formatting = FormattingConfig(
            compact_format=compact_format,
        )

        # Logging from CLI args
        instance.log_queries = log_queries
        instance.log_results = log_results

        # Apply environment overrides
        instance._apply_env_overrides()

        return instance

    def _find_config_file(self) -> str:
        """Find configuration file in standard locations."""
        # Get the directory where this script is located
        script_dir = Path(__file__).parent.parent

        search_paths = [
            script_dir / "config" / "config.yaml",
            script_dir / "config.yaml",
            Path("config/config.yaml"),  # Current directory
            Path("config.yaml"),
            Path("/app/config/config.yaml"),  # Docker path
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        # Fall back to example file
        example_paths = [
            script_dir / "config" / "config.yaml.example",
            Path("config/config.yaml.example"),
        ]

        for path in example_paths:
            if path.exists():
                logger.warning(f"Using example config from {path}")
                return str(path)

        raise FileNotFoundError(
            f"No configuration file found. Searched in: {[str(p) for p in search_paths]}\n"
            f"Consider using command-line arguments instead: python src/server.py project:dataset_pattern"
        )

    def _load_yaml(self, config_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config or {}
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise

    def _parse_config(self) -> None:
        """Parse raw configuration into typed objects."""
        # Server info
        server_config = self._raw_config.get("server", {})
        self.server_name = server_config.get("name", "BigQuery MCP Server")
        self.server_version = server_config.get("version", "1.1.0")

        # BigQuery settings
        bq_config = self._raw_config.get("bigquery", {})
        self.billing_project = bq_config.get("billing_project", "")
        self.service_account_path = bq_config.get("service_account_path", "")
        self.location = bq_config.get("location", "EU")  # Default to EU

        # Projects
        self.projects = []
        for proj in self._raw_config.get("projects", []):
            self.projects.append(
                ProjectConfig(
                    project_id=proj["project_id"],
                    project_name=proj.get("project_name", proj["project_id"]),
                    description=proj.get("description", ""),
                    datasets=proj.get("datasets", []),
                )
            )

        # Security
        security_dict = self._raw_config.get("security", {})
        self.security = SecurityConfig(
            banned_sql_keywords=security_dict.get(
                "banned_sql_keywords",
                [
                    "CREATE",
                    "DELETE",
                    "DROP",
                    "TRUNCATE",
                    "INSERT",
                    "UPDATE",
                    "ALTER",
                    "GRANT",
                    "REVOKE",
                    "MERGE",
                ],
            ),
            select_only=security_dict.get("select_only", True),
            require_explicit_limits=security_dict.get("require_explicit_limits", False),
        )

        # Limits
        limits_dict = self._raw_config.get("limits", {})
        self.limits = LimitsConfig(
            default_limit=limits_dict.get(
                "default_limit", limits_dict.get("default_row_limit", 20)
            ),
            max_query_timeout=limits_dict.get("max_query_timeout", 60),
            max_limit=limits_dict.get("max_limit", limits_dict.get("max_row_limit", 10000)),
            max_bytes_processed=limits_dict.get("max_bytes_processed", 1073741824),
        )

        # Formatting
        formatting_dict = self._raw_config.get("formatting", {})
        self.formatting = FormattingConfig(
            compact_format=formatting_dict.get("compact_format", False),
        )

        # Logging
        logging_dict = self._raw_config.get("logging", {})
        self.log_queries = logging_dict.get("log_queries", True)
        self.log_results = logging_dict.get("log_results", False)

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        This method applies environment variable overrides to the configuration.
        Note: CLI arguments (when using from_cli_args) take precedence over both
        config file and environment variables.
        """
        # Billing project
        if env_billing := os.getenv("BIGQUERY_BILLING_PROJECT"):
            if not self.billing_project:  # Only override if not already set
                self.billing_project = env_billing
                logger.info(f"Using billing project from env: {env_billing}")

        # Service account
        if env_creds := os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            if not self.service_account_path:  # Only override if not already set
                self.service_account_path = env_creds
                logger.info("Using service account from GOOGLE_APPLICATION_CREDENTIALS")

        # Location
        if env_location := os.getenv("BIGQUERY_LOCATION"):
            if self.location == "EU":  # Only override if using default
                self.location = env_location
                logger.info(f"Using location from env: {env_location}")

        # Compact format (only if not explicitly set)
        if env_compact := os.getenv("COMPACT_FORMAT"):
            # For CLI args, this would have been set explicitly, so only override for config file usage
            if hasattr(self, "_from_cli_args") and not self._from_cli_args:
                self.formatting.compact_format = env_compact.lower() == "true"
                logger.info(f"Using compact format from env: {self.formatting.compact_format}")

        # Log level (handled by logging setup in server.py)
        # Additional environment variables for comprehensive support
        if env_log_queries := os.getenv("LOG_QUERIES"):
            if not hasattr(self, "_from_cli_args") or not self._from_cli_args:
                self.log_queries = env_log_queries.lower() == "true"
                logger.info(f"Using log_queries from env: {self.log_queries}")

        if env_log_results := os.getenv("LOG_RESULTS"):
            if not hasattr(self, "_from_cli_args") or not self._from_cli_args:
                self.log_results = env_log_results.lower() == "true"
                logger.info(f"Using log_results from env: {self.log_results}")

    def log_configuration_source(self) -> None:
        """Log the source of configuration values for debugging."""
        logger.info("Configuration precedence: CLI > Config File > Environment > Defaults")

        if hasattr(self, "_from_cli_args") and self._from_cli_args:
            logger.info("Configuration source: CLI arguments (highest precedence)")
        elif self.config_path:
            logger.info(
                f"Configuration source: Config file ({self.config_path}) + Environment overrides"
            )
        else:
            logger.info("Configuration source: Environment variables + Defaults")

        logger.info(
            f"Final configuration: billing_project={self.billing_project}, "
            f"location={self.location}, compact_format={self.formatting.compact_format}"
        )

    def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        """Get project configuration by ID."""
        for project in self.projects:
            if project.project_id == project_id:
                return project
        return None

    def get_allowed_projects(self) -> List[str]:
        """Get list of allowed project IDs."""
        return [p.project_id for p in self.projects]

    def is_project_allowed(self, project_id: str) -> bool:
        """Check if project is in allowed list."""
        return project_id in self.get_allowed_projects()

    def is_dataset_allowed(self, project_id: str, dataset_id: str) -> bool:
        """Check if dataset is allowed for the given project."""
        project = self.get_project(project_id)
        if not project:
            return False
        return project.is_dataset_allowed(dataset_id)

    def validate(self) -> None:
        """Validate configuration completeness."""
        errors = []

        if not self.billing_project:
            errors.append("Missing billing_project in configuration")

        if not self.projects:
            errors.append("No projects configured")

        for i, project in enumerate(self.projects):
            if not project.project_id:
                errors.append(f"Project {i} missing project_id")
            if not project.datasets:
                errors.append(f"Project {project.project_id} has no dataset patterns")

        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")


# Singleton instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create configuration instance."""
    global _config
    if _config is None:
        try:
            _config = Config(config_path)
            _config.validate()
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            logger.error("Please use command-line arguments instead.")
            logger.error("Example: python src/server.py sandbox-dev:dev_* sandbox-main:main_*")
            raise
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Force reload configuration from file."""
    global _config
    _config = Config(config_path)
    _config.validate()
    return _config
