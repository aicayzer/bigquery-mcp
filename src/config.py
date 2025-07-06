"""Configuration management for BigQuery MCP Server."""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

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
    default_row_limit: int = 20
    max_query_timeout: int = 60
    max_row_limit: int = 10000
    max_bytes_processed: int = 1073741824  # 1GB


@dataclass
class FormattingConfig:
    """Response formatting configuration."""
    compact_format: bool = False
    include_schema_descriptions: bool = True
    abbreviate_common_terms: bool = False


class Config:
    """Main configuration manager for BigQuery MCP Server."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file and environment."""
        if config_path is None:
            config_path = self._find_config_file()
        
        self.config_path = config_path
        self._raw_config = self._load_yaml(config_path)
        self._parse_config()
        self._apply_env_overrides()
        
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
            Path("config/config.yaml.example")
        ]
        
        for path in example_paths:
            if path.exists():
                logger.warning(f"Using example config from {path}")
                return str(path)
        
        raise FileNotFoundError(f"No configuration file found. Searched in: {[str(p) for p in search_paths]}")
    
    def _load_yaml(self, config_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config or {}
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def _parse_config(self) -> None:
        """Parse raw configuration into typed objects."""
        # Server info
        server_config = self._raw_config.get('server', {})
        self.server_name = server_config.get('name', 'BigQuery MCP Server')
        self.server_version = server_config.get('version', '0.1.0')
        
        # BigQuery settings
        bq_config = self._raw_config.get('bigquery', {})
        self.billing_project = bq_config.get('billing_project', '')
        self.service_account_path = bq_config.get('service_account_path', '')
        self.location = bq_config.get('location', 'EU')  # Default to EU
        
        # Projects
        self.projects = []
        for proj in self._raw_config.get('projects', []):
            self.projects.append(ProjectConfig(
                project_id=proj['project_id'],
                project_name=proj.get('project_name', proj['project_id']),
                description=proj.get('description', ''),
                datasets=proj.get('datasets', [])
            ))
        
        # Security
        security_dict = self._raw_config.get('security', {})
        self.security = SecurityConfig(
            banned_sql_keywords=security_dict.get('banned_sql_keywords', [
                "CREATE", "DELETE", "DROP", "TRUNCATE", "INSERT", 
                "UPDATE", "ALTER", "GRANT", "REVOKE", "MERGE"
            ]),
            select_only=security_dict.get('select_only', True),
            require_explicit_limits=security_dict.get('require_explicit_limits', False)
        )
        
        # Limits
        limits_dict = self._raw_config.get('limits', {})
        self.limits = LimitsConfig(
            default_row_limit=limits_dict.get('default_row_limit', 20),
            max_query_timeout=limits_dict.get('max_query_timeout', 60),
            max_row_limit=limits_dict.get('max_row_limit', 10000),
            max_bytes_processed=limits_dict.get('max_bytes_processed', 1073741824)
        )
        
        # Formatting
        formatting_dict = self._raw_config.get('formatting', {})
        self.formatting = FormattingConfig(
            compact_format=formatting_dict.get('compact_format', False),
            include_schema_descriptions=formatting_dict.get('include_schema_descriptions', True),
            abbreviate_common_terms=formatting_dict.get('abbreviate_common_terms', False)
        )
        
        # Logging
        logging_dict = self._raw_config.get('logging', {})
        self.log_queries = logging_dict.get('log_queries', True)
        self.log_results = logging_dict.get('log_results', False)
        self.max_query_log_length = logging_dict.get('max_query_log_length', 1000)
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Billing project
        if env_billing := os.getenv('BIGQUERY_BILLING_PROJECT'):
            self.billing_project = env_billing
            logger.info(f"Overriding billing project from env: {env_billing}")
        
        # Service account
        if env_creds := os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            self.service_account_path = env_creds
            logger.info("Using service account from GOOGLE_APPLICATION_CREDENTIALS")
        
        # Location
        if env_location := os.getenv('BIGQUERY_LOCATION'):
            self.location = env_location
            logger.info(f"Overriding location from env: {env_location}")
        
        # Compact format
        if env_compact := os.getenv('COMPACT_FORMAT'):
            self.formatting.compact_format = env_compact.lower() == 'true'
            logger.info(f"Overriding compact format from env: {self.formatting.compact_format}")
        
        # Log level is handled by logging setup, not here
    
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
        _config = Config(config_path)
        _config.validate()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Force reload configuration from file."""
    global _config
    _config = Config(config_path)
    _config.validate()
    return _config
