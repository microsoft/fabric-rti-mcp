from __future__ import annotations

import abc
import csv
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from fabric_rti_mcp.services.kusto.kusto_formatter import KustoFormatter

ADAPTIVE_RESULTS_TOKEN_THRESHOLD = 1000


@dataclass(slots=True, frozen=True)
class KustoFileResponseFormat:
    format: str  # always "file"
    path: str
    file_format: str
    row_count: int


class FileWriter(abc.ABC):
    @property
    @abc.abstractmethod
    def extension(self) -> str: ...

    @abc.abstractmethod
    def write(self, rows: list[dict[str, Any]], path: str) -> None: ...


class CsvFileWriter(FileWriter):
    @property
    def extension(self) -> str:
        return "csv"

    def write(self, rows: list[dict[str, Any]], path: str) -> None:
        if not rows:
            with open(path, "w", newline="") as f:
                f.write("")
            return

        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)


class JsonlFileWriter(FileWriter):
    @property
    def extension(self) -> str:
        return "jsonl"

    def write(self, rows: list[dict[str, Any]], path: str) -> None:
        with open(path, "w") as f:
            for row in rows:
                f.write(json.dumps(row, default=str) + "\n")


_WRITERS: dict[str, FileWriter] = {
    "csv": CsvFileWriter(),
    "jsonl": JsonlFileWriter(),
}


def get_file_writer(file_format: str) -> FileWriter:
    writer = _WRITERS.get(file_format)
    if writer is None:
        raise ValueError(f"Unsupported file format: {file_format}. Supported: {', '.join(_WRITERS)}")
    return writer


def estimate_token_count(response: dict[str, Any]) -> int:
    serialized = json.dumps(response, default=str, separators=(",", ":"))
    return len(serialized) // 4


def maybe_write_to_file(
    response: dict[str, Any],
    output_dir: str | None = None,
    file_format: str = "jsonl",
    threshold: int = ADAPTIVE_RESULTS_TOKEN_THRESHOLD,
) -> dict[str, Any]:
    token_count = estimate_token_count(response)
    if token_count <= threshold:
        return response

    rows = KustoFormatter.parse(response)
    if rows is None or len(rows) == 0:
        return response

    writer = get_file_writer(file_format)
    target_dir = output_dir or tempfile.gettempdir()
    os.makedirs(target_dir, exist_ok=True)

    filename = f"kusto_result_{uuid.uuid4().hex[:12]}.{writer.extension}"
    filepath = os.path.join(target_dir, filename)

    writer.write(rows, filepath)

    return asdict(
        KustoFileResponseFormat(
            format="file",
            path=filepath,
            file_format=writer.extension,
            row_count=len(rows),
        )
    )
