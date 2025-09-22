import csv
import io
import json
from dataclasses import dataclass
from typing import Any, cast

from azure.kusto.data.response import KustoResponseDataSet


@dataclass(slots=True, frozen=True)
class KustoResponseFormat:
    format: str
    data: Any


class KustoFormatter:
    """Formatter for Kusto query results in various compact formats"""

    @staticmethod
    def to_json(result_set: KustoResponseDataSet | None) -> KustoResponseFormat:
        if not result_set or not getattr(result_set, "primary_results", None):
            return KustoResponseFormat(format="json", data=[])

        first_result = result_set.primary_results[0]
        column_names = [col.column_name for col in first_result.columns]

        return KustoResponseFormat(format="json", data=[dict(zip(column_names, row)) for row in first_result.rows])

    @staticmethod
    def to_csv(result_set: KustoResponseDataSet | None) -> KustoResponseFormat:
        if not result_set or not getattr(result_set, "primary_results", None):
            return KustoResponseFormat(format="csv", data="")

        first_result = result_set.primary_results[0]
        output = io.StringIO()

        # Create CSV writer with standard settings
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Write header
        header = [col.column_name for col in first_result.columns]
        writer.writerow(header)

        # Write data rows
        for row in first_result.rows:
            # Convert None to empty string, keep other types
            formatted_row = ["" if v is None else v for v in row]
            writer.writerow(formatted_row)

        return KustoResponseFormat(format="csv", data=output.getvalue())

    @staticmethod
    def to_tsv(result_set: KustoResponseDataSet | None) -> KustoResponseFormat:
        result = KustoResponseFormat(format="tsv", data="")
        if not result_set or not getattr(result_set, "primary_results", None):
            return result

        first_result = result_set.primary_results[0]
        lines: list[str] = []

        # Header row
        header = "\t".join(col.column_name for col in first_result.columns)
        lines.append(header)

        # Data rows
        for row in first_result.rows:
            formatted_row: list[str] = []
            for value in row:
                if value is None:
                    formatted_row.append("")
                else:
                    # Escape tabs, newlines, and backslashes
                    str_value = str(value)
                    str_value = str_value.replace("\\", "\\\\")  # Escape backslashes first
                    str_value = str_value.replace("\t", "\\t")
                    str_value = str_value.replace("\n", "\\n")
                    str_value = str_value.replace("\r", "\\r")
                    formatted_row.append(str_value)

            lines.append("\t".join(formatted_row))

        return KustoResponseFormat(format="tsv", data="\n".join(lines))

    @staticmethod
    def to_columnar(result_set: KustoResponseDataSet | None) -> KustoResponseFormat:
        if not result_set or not getattr(result_set, "primary_results", None):
            return KustoResponseFormat(format="columnar", data={})

        first_result = result_set.primary_results[0]

        # Build columnar structure
        columnar_data: dict[str, list[Any]] = {}

        # Initialize columns
        for i, col in enumerate(first_result.columns):
            columnar_data[col.column_name] = []

        # Populate columns
        for row in first_result.rows:
            for i, col in enumerate(first_result.columns):
                columnar_data[col.column_name].append(row[i])  # type: ignore

        # Compact JSON (no spaces)
        return KustoResponseFormat(format="columnar", data=columnar_data)

    @staticmethod
    def to_header_arrays(result_set: KustoResponseDataSet | None) -> KustoResponseFormat:
        if not result_set or not getattr(result_set, "primary_results", None):
            return KustoResponseFormat(format="header_arrays", data=[])

        first_result = result_set.primary_results[0]
        lines: list[str] = []

        # Header as JSON array
        columns = [col.column_name for col in first_result.columns]
        lines.append(json.dumps(columns, separators=(",", ":")))

        # Each row as JSON array
        for row in first_result.rows:
            row_list = list(row)
            lines.append(json.dumps(row_list, separators=(",", ":")))

        return KustoResponseFormat(format="header_arrays", data="\n".join(lines))

    @staticmethod
    def parse(response: KustoResponseFormat | dict[str, Any]) -> list[dict[str, Any]] | None:
        """
        Parse any KustoResponseFormat back to canonical JSON array format.

        Args:
            response: Either a KustoResponseFormat object or a dict with 'format' and 'data' keys

        Returns:
            List of dictionaries where each dict represents a row with column names as keys
        """
        if response is None:  # type: ignore
            return None  # type: ignore

        if isinstance(response, dict):
            format_type = response.get("format", "")
            data = response.get("data")
        elif isinstance(response, KustoResponseFormat):  # type: ignore
            format_type = response.format
            data = response.data
        else:
            raise ValueError("Invalid KustoResponseFormat")

        # Handle None data early
        if data is None:
            return None

        if format_type == "json":
            return KustoFormatter._parse_json(data)
        elif format_type == "csv":
            return KustoFormatter._parse_csv(data)
        elif format_type == "tsv":
            return KustoFormatter._parse_tsv(data)
        elif format_type == "columnar":
            return KustoFormatter._parse_columnar(data)
        elif format_type == "header_arrays":
            return KustoFormatter._parse_header_arrays(data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @staticmethod
    def _parse_json(data: Any) -> list[dict[str, Any]]:
        """Parse JSON format data (already in canonical format)"""
        if data is None or (not isinstance(data, list) and not isinstance(data, dict)):  # type: ignore
            raise ValueError("Invalid JSON format")
        return data  # type: ignore

    @staticmethod
    def _parse_csv(data: str) -> list[dict[str, Any]]:
        """Parse CSV format data back to canonical JSON"""
        if data == "":
            return []
        if data is None:  # type: ignore
            return None  # type: ignore
        if not isinstance(data, str):  # type: ignore
            raise ValueError("Invalid CSV format")

        lines = data.strip().split("\n")
        if len(lines) < 1:
            raise ValueError("Invalid CSV format")

        # Parse CSV using csv.reader to handle escaping properly
        csv_reader = csv.reader(io.StringIO(data))
        rows = list(csv_reader)

        if len(rows) < 1:
            return []

        headers = rows[0]
        result: list[dict[str, Any]] = []

        for row in rows[1:]:
            # Pad row with empty strings if shorter than headers
            padded_row = row + [""] * (len(headers) - len(row))
            row_dict: dict[str, Any] = {}
            for i, header in enumerate(headers):
                value = padded_row[i] if i < len(padded_row) else ""
                # Convert empty strings back to None if needed
                row_dict[header] = None if value == "" else value
            result.append(row_dict)

        return result

    @staticmethod
    def _parse_tsv(data: str) -> list[dict[str, Any]]:
        """Parse TSV format data back to canonical JSON"""
        if data == "":
            return []
        if not isinstance(data, str):  # type: ignore
            raise ValueError("Invalid TSV format")

        lines = data.strip().split("\n")
        if len(lines) < 1:
            raise ValueError("Invalid TSV format")

        # Parse header
        headers = lines[0].split("\t")
        result: list[dict[str, Any]] = []

        # Parse data rows
        for line in lines[1:]:
            values = line.split("\t")
            row_dict: dict[str, Any] = {}

            for i, header in enumerate(headers):
                value = values[i] if i < len(values) else ""

                # Unescape TSV special characters
                if value:
                    value = value.replace("\\t", "\t")
                    value = value.replace("\\n", "\n")
                    value = value.replace("\\r", "\r")
                    value = value.replace("\\\\", "\\")  # Unescape backslashes last

                # Convert empty strings back to None
                row_dict[header] = None if value == "" else value

            result.append(row_dict)

        return result

    @staticmethod
    def _parse_columnar(data: Any) -> list[dict[str, Any]]:
        """Parse columnar format data back to canonical JSON"""
        if data is None or not isinstance(data, dict):
            raise ValueError("Invalid columnar format")
        data = cast(dict[str, list[Any]], data)

        # Get column names and determine row count
        columns: list[str] = list(data.keys())  # type: ignore
        if not columns:
            return []

        # All columns should have the same length
        row_count = len(data[columns[0]]) if columns[0] in data else 0

        result: list[dict[str, Any]] = []
        for row_idx in range(row_count):
            row_dict: dict[str, Any] = {}
            for col_name in columns:
                col_values = data.get(col_name, [])
                row_dict[col_name] = col_values[row_idx] if row_idx < len(col_values) else None
            result.append(row_dict)

        return result

    @staticmethod
    def _parse_header_arrays(data: str) -> list[dict[str, Any]]:
        """Parse header_arrays format data back to canonical JSON"""
        if data is None or not isinstance(data, str):  # type: ignore
            raise ValueError("Invalid header_arrays format")

        lines = data.strip().split("\n")
        if len(lines) < 1:
            return []

        try:
            # Parse header (first line)
            headers: list[str] = json.loads(lines[0])
            if not isinstance(headers, list):  # type: ignore
                return []  # type: ignore

            result: list[dict[str, Any]] = []

            # Parse data rows (remaining lines)
            for line in lines[1:]:
                row_values: list[Any] = json.loads(line)
                if not isinstance(row_values, list):  # type: ignore
                    continue  # type: ignore

                row_dict: dict[str, Any] = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row_values[i] if i < len(row_values) else None
                result.append(row_dict)

            return result

        except json.JSONDecodeError:
            return []
