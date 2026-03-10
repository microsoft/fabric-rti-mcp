import csv
import io
import json
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlparse

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
        for col in first_result.columns:
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
    def extract_statistics(result_set: KustoResponseDataSet | None) -> dict[str, Any] | None:
        if not result_set or not getattr(result_set, "tables", None):
            return None

        for table in result_set.tables:
            table_kind = getattr(getattr(table, "table_kind", None), "value", getattr(table, "table_kind", None))
            if table_kind != "QueryCompletionInformation":
                continue

            parsed_stats = KustoFormatter._extract_statistics_payload(table)
            if parsed_stats is None:
                continue

            return KustoFormatter._normalize_statistics(parsed_stats)

        return None

    @staticmethod
    def _extract_statistics_payload(table: Any) -> dict[str, Any] | None:
        columns = [getattr(column, "column_name", None) for column in getattr(table, "columns", [])]
        if not columns:
            return None

        raw_rows = getattr(table, "raw_rows", None)
        if raw_rows is None:
            raw_rows = [list(row) for row in getattr(table, "rows", [])]

        for row in raw_rows:
            row_values = list(row)
            row_data = {col_name: row_values[i] if i < len(row_values) else None for i, col_name in enumerate(columns)}

            severity_name = row_data.get("SeverityName")
            if isinstance(severity_name, str) and severity_name.lower() == "stats":
                severity_payload = KustoFormatter._parse_json_object(row_data.get("StatusDescription"))
                if severity_payload is not None:
                    return severity_payload

            payload = KustoFormatter._parse_json_object(row_data.get("Payload"))
            if payload is None:
                continue

            event_type = row_data.get("EventTypeName")
            if not isinstance(event_type, str):
                return payload

            if event_type.lower() in {"stats", "queryresourceconsumption", "querycompletioninformation"}:
                return payload

        return None

    @staticmethod
    def _normalize_statistics(source: dict[str, Any]) -> dict[str, Any] | None:
        result: dict[str, Any] = {}

        execution_time = KustoFormatter._to_float(source.get("ExecutionTime"))
        if execution_time is not None:
            result["execution_time_sec"] = execution_time

        resource_usage = source.get("resource_usage")
        if isinstance(resource_usage, dict):
            cpu = resource_usage.get("cpu")
            if isinstance(cpu, dict):
                cpu_result: dict[str, Any] = {}
                total_cpu = cpu.get("total cpu")
                if isinstance(total_cpu, str) and total_cpu:
                    cpu_result["total"] = total_cpu

                breakdown = cpu.get("breakdown")
                if isinstance(breakdown, dict):
                    query_execution = breakdown.get("query execution")
                    if isinstance(query_execution, str) and query_execution:
                        cpu_result["query_execution"] = query_execution

                    query_planning = breakdown.get("query planning")
                    if isinstance(query_planning, str) and query_planning:
                        cpu_result["query_planning"] = query_planning

                if cpu_result:
                    result["cpu"] = cpu_result

            memory = resource_usage.get("memory")
            if isinstance(memory, dict):
                peak_per_node_bytes = KustoFormatter._to_float(memory.get("peak_per_node"))
                if peak_per_node_bytes is not None:
                    result["memory_peak_per_node_mb"] = KustoFormatter._bytes_to_megabytes(peak_per_node_bytes)

            cache = resource_usage.get("cache")
            if isinstance(cache, dict):
                shards = cache.get("shards")
                if isinstance(shards, dict):
                    hot = shards.get("hot")
                    if isinstance(hot, dict):
                        cache_result: dict[str, Any] = {}
                        hit_bytes = KustoFormatter._to_float(hot.get("hitbytes"))
                        if hit_bytes is not None:
                            cache_result["hot_hit_mb"] = KustoFormatter._bytes_to_megabytes(hit_bytes)

                        miss_bytes = KustoFormatter._to_float(hot.get("missbytes"))
                        if miss_bytes is not None:
                            cache_result["hot_miss_mb"] = KustoFormatter._bytes_to_megabytes(miss_bytes)

                        if cache_result:
                            result["cache"] = cache_result

            network = resource_usage.get("network")
            if isinstance(network, dict):
                network_result: dict[str, Any] = {}
                cross_cluster_total_bytes = KustoFormatter._to_float(network.get("cross_cluster_total_bytes"))
                if cross_cluster_total_bytes is not None:
                    network_result["cross_cluster_mb"] = KustoFormatter._bytes_to_megabytes(cross_cluster_total_bytes)

                inter_cluster_total_bytes = KustoFormatter._to_float(network.get("inter_cluster_total_bytes"))
                if inter_cluster_total_bytes is not None:
                    network_result["inter_cluster_mb"] = KustoFormatter._bytes_to_megabytes(inter_cluster_total_bytes)

                if network_result:
                    result["network"] = network_result

        input_dataset_statistics = source.get("input_dataset_statistics")
        if isinstance(input_dataset_statistics, dict):
            extents = input_dataset_statistics.get("extents")
            if isinstance(extents, dict):
                extents_result: dict[str, Any] = {}
                scanned_extents = KustoFormatter._to_int(extents.get("scanned"))
                if scanned_extents is not None:
                    extents_result["scanned"] = scanned_extents

                total_extents = KustoFormatter._to_int(extents.get("total"))
                if total_extents is not None:
                    extents_result["total"] = total_extents

                if extents_result:
                    result["extents"] = extents_result

            rows = input_dataset_statistics.get("rows")
            if isinstance(rows, dict):
                rows_result: dict[str, Any] = {}
                scanned_rows = KustoFormatter._to_int(rows.get("scanned"))
                if scanned_rows is not None:
                    rows_result["scanned"] = scanned_rows

                total_rows = KustoFormatter._to_int(rows.get("total"))
                if total_rows is not None:
                    rows_result["total"] = total_rows

                if rows_result:
                    result["rows"] = rows_result

        dataset_statistics = source.get("dataset_statistics")
        if isinstance(dataset_statistics, list) and dataset_statistics:
            first_dataset = dataset_statistics[0]
            if isinstance(first_dataset, dict):
                result_dataset: dict[str, Any] = {}
                table_row_count = KustoFormatter._to_int(first_dataset.get("table_row_count"))
                if table_row_count is not None:
                    result_dataset["row_count"] = table_row_count

                table_size_bytes = KustoFormatter._to_float(first_dataset.get("table_size"))
                if table_size_bytes is not None:
                    result_dataset["size_kb"] = KustoFormatter._bytes_to_kilobytes(table_size_bytes)

                if result_dataset:
                    result["result"] = result_dataset

        cross_cluster_resource_usage = source.get("cross_cluster_resource_usage")
        if isinstance(cross_cluster_resource_usage, dict):
            cross_cluster_result: dict[str, Any] = {}
            for cluster_identifier, cluster_usage in cross_cluster_resource_usage.items():
                if not isinstance(cluster_usage, dict):
                    continue

                cluster_result: dict[str, Any] = {}
                cpu = cluster_usage.get("cpu")
                if isinstance(cpu, dict):
                    total_cpu = cpu.get("total cpu")
                    if isinstance(total_cpu, str) and total_cpu:
                        cluster_result["cpu_total"] = total_cpu

                memory = cluster_usage.get("memory")
                if isinstance(memory, dict):
                    peak_per_node_bytes = KustoFormatter._to_float(memory.get("peak_per_node"))
                    if peak_per_node_bytes is not None:
                        cluster_result["memory_peak_mb"] = KustoFormatter._bytes_to_megabytes(peak_per_node_bytes)

                cache = cluster_usage.get("cache")
                if isinstance(cache, dict):
                    shards = cache.get("shards")
                    if isinstance(shards, dict):
                        hot = shards.get("hot")
                        if isinstance(hot, dict):
                            hit_bytes = KustoFormatter._to_float(hot.get("hitbytes"))
                            if hit_bytes is not None:
                                cluster_result["cache_hit_mb"] = KustoFormatter._bytes_to_megabytes(hit_bytes)

                            miss_bytes = KustoFormatter._to_float(hot.get("missbytes"))
                            if miss_bytes is not None:
                                cluster_result["cache_miss_mb"] = KustoFormatter._bytes_to_megabytes(miss_bytes)

                if not cluster_result:
                    continue

                cluster_name = KustoFormatter._normalize_cluster_name(str(cluster_identifier))
                if cluster_name:
                    cross_cluster_result[cluster_name] = cluster_result

            if cross_cluster_result:
                result["cross_cluster_breakdown"] = cross_cluster_result

        return result or None

    @staticmethod
    def _parse_json_object(raw_value: Any) -> dict[str, Any] | None:
        if isinstance(raw_value, dict):
            return raw_value

        if not isinstance(raw_value, str) or not raw_value.strip():
            return None

        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None

        return None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return None

        return None

    @staticmethod
    def _bytes_to_megabytes(value: float) -> float:
        return round(value / 1048576, 2)

    @staticmethod
    def _bytes_to_kilobytes(value: float) -> float:
        return round(value / 1024, 2)

    @staticmethod
    def _normalize_cluster_name(cluster_identifier: str) -> str:
        parsed_uri = urlparse(cluster_identifier)
        if parsed_uri.netloc:
            return parsed_uri.netloc

        normalized = cluster_identifier.strip().rstrip("/")
        if normalized.lower().startswith("https://"):
            return normalized[8:]
        if normalized.lower().startswith("http://"):
            return normalized[7:]
        return normalized

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
