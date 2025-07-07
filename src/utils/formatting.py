"""Response formatting utilities for standard and compact modes."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

from config import get_config


class ResponseFormatter:
    """Formats responses for optimal LLM consumption."""

    def __init__(self, config=None):
        """Initialize formatter with configuration."""
        self.config = config or get_config()

    @property
    def compact_mode(self) -> bool:
        """Check if compact mode is enabled."""
        return self.config.formatting.compact_format

    def format_schema(self, schema: List[Dict[str, Any]]) -> Any:
        """
        Format table schema based on compact setting.

        Args:
            schema: List of field dictionaries with name, type, description

        Returns:
            Formatted schema (dict for compact, list for standard)
        """
        if self.compact_mode:
            # Compact: {"column": "TYPE - Description"}
            result = {}
            for field in schema:
                name = field["name"]
                field_type = field["type"]
                desc = field.get("description", "No description")

                # Abbreviate common terms if configured
                if self.config.formatting.abbreviate_common_terms:
                    field_type = self._abbreviate_type(field_type)

                # Include description only if configured
                if self.config.formatting.include_schema_descriptions and desc != "No description":
                    result[name] = f"{field_type} - {desc}"
                else:
                    result[name] = field_type

            return result
        else:
            # Standard: List of column objects
            formatted = []
            for field in schema:
                formatted_field = {"name": field["name"], "type": field["type"]}

                # Include description if configured
                if self.config.formatting.include_schema_descriptions:
                    formatted_field["description"] = field.get("description", "No description")

                # Include mode if present
                if "mode" in field:
                    formatted_field["mode"] = field["mode"]

                formatted.append(formatted_field)

            return formatted

    def format_query_results(
        self, rows: List[Dict[str, Any]], format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Format query results.

        Args:
            rows: List of row dictionaries
            format_type: Output format ('json' or 'csv')

        Returns:
            Formatted results with metadata
        """
        # Convert special types to JSON-serializable format
        formatted_rows = []
        for row in rows:
            formatted_row = {}
            for key, value in row.items():
                formatted_row[key] = self._format_value(value)
            formatted_rows.append(formatted_row)

        response = {"row_count": len(formatted_rows), "results": formatted_rows}

        # Add CSV format if requested
        if format_type == "csv" and formatted_rows:
            response["csv_data"] = self._to_csv(formatted_rows)

        return response

    def format_error(self, error: Exception) -> Dict[str, Any]:
        """
        Format error response.

        Args:
            error: Exception to format

        Returns:
            Error response dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Make error messages more user-friendly
        if "Not found" in error_message:
            error_message = self._improve_not_found_message(error_message)

        return {"status": "error", "error_type": error_type, "error": error_message}

    def format_table_info(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format table information for response.

        Args:
            table_info: Raw table information

        Returns:
            Formatted table info
        """
        if self.compact_mode:
            # Compact mode: essential fields only
            return {
                "table": f"{table_info['project_id']}.{table_info['dataset_id']}.{table_info['table_id']}",
                "type": table_info["table_type"],
                "rows": table_info.get("num_rows", 0),
                "size_mb": round(table_info.get("size_bytes", 0) / (1024 * 1024), 2),
                "created": table_info.get("created"),
            }
        else:
            # Standard mode: full information
            return table_info

    def format_column_analysis(self, analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format column analysis results.

        Args:
            analysis: Raw analysis results by column

        Returns:
            Formatted analysis
        """
        if self.compact_mode:
            # Compact: essential metrics only
            compact = {}
            for col, metrics in analysis.items():
                compact[col] = {
                    "nulls": f"{metrics.get('null_pct', 0):.1f}%",
                    "distinct": metrics.get("distinct_count", 0),
                    "type": metrics.get("classification", "unknown"),
                }
            return compact
        else:
            # Standard: full metrics
            return analysis

    def _format_value(self, value: Any) -> Any:
        """Convert BigQuery values to JSON-serializable format."""
        if value is None:
            return None
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return str(value)
        elif isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        elif hasattr(value, "__dict__"):
            # Handle nested objects
            return {k: self._format_value(v) for k, v in value.__dict__.items()}
        else:
            return value

    def _to_csv(self, rows: List[Dict[str, Any]]) -> str:
        """Convert rows to CSV format."""
        if not rows:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

        return output.getvalue()

    def _abbreviate_type(self, field_type: str) -> str:
        """Abbreviate common BigQuery types."""
        abbreviations = {
            "STRING": "STR",
            "INTEGER": "INT",
            "FLOAT64": "FLOAT",
            "NUMERIC": "NUM",
            "BOOLEAN": "BOOL",
            "TIMESTAMP": "TS",
            "DATETIME": "DT",
            "RECORD": "REC",
            "REPEATED": "REP",
        }
        return abbreviations.get(field_type, field_type)

    def _improve_not_found_message(self, message: str) -> str:
        """Make 'not found' errors more helpful."""
        # Extract what was not found
        if "Table" in message:
            return message + ". Please check the table path and ensure you have access."
        elif "Dataset" in message:
            return message + ". Please verify the dataset exists and you have access."
        else:
            return message
