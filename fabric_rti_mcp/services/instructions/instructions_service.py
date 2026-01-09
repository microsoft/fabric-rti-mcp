from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlparse

from fabric_rti_mcp.config import global_config, logger

_INSTRUCTIONS_URI_ENV = "RTI_INSTRUCTIONS_URI"
_INSTRUCTIONS_DESCRIPTION_ENV = "RTI_INSTRUCTIONS_DESCRIPTION"


@dataclass(frozen=True, slots=True)
class _DescriptionConfig:
    method: str
    params: dict[str, Any]


def common_instructions_list() -> list[tuple[str, str]]:
    """List available instruction markdown files.

    Returns:
        A list of (file_name, description) tuples.

    Notes:
        - This tool is expected to be registered only when RTI_INSTRUCTIONS_URI is set.
        - The description is controlled by RTI_INSTRUCTIONS_DESCRIPTION.
          Supported methods:
            - "head": returns the first N characters from the markdown body.
            - "metadata": returns abstract/summary/description from YAML frontmatter.
    """

    base_dir = _instructions_dir()
    config = _get_description_config()

    results: list[tuple[str, str]] = []
    for file_path in sorted(base_dir.glob("*.md")):
        if not file_path.is_file():
            continue
        content = file_path.read_text(encoding="utf-8")
        description = _describe(content, config)
        results.append((file_path.name, description))

    return results


def common_instructions_load(name: str) -> str:
    """Load an instruction markdown file by name.

    Args:
        name: A file name as returned by common_instructions_list (e.g., "kusto.md").

    Returns:
        Full markdown content.
    """

    safe_name = name.strip()
    if not safe_name:
        raise ValueError("name must be non-empty")

    base_dir = _instructions_dir()

    # Only allow loading files that exist in the directory listing.
    candidates = {p.name: p for p in base_dir.glob("*.md") if p.is_file()}
    if safe_name not in candidates:
        available = ", ".join(sorted(candidates.keys()))
        raise ValueError(f"Unknown instruction '{safe_name}'. Available: {available}")

    return candidates[safe_name].read_text(encoding="utf-8")


def _instructions_dir() -> Path:
    uri = (global_config.instructions_uri or "").strip()
    if not uri:
        raise ValueError(f"{_INSTRUCTIONS_URI_ENV} must be set to a non-empty value")

    parsed = urlparse(uri)
    scheme = (parsed.scheme or "").lower()

    if scheme in ("", "file"):
        path = _file_uri_to_path(uri, parsed)
        if not path.exists():
            raise ValueError(f"Instructions path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Instructions path must be a directory: {path}")
        return path

    raise ValueError(f"Unsupported instructions URI scheme '{parsed.scheme}'. Supported: file")


def _file_uri_to_path(uri: str, parsed: Any) -> Path:
    # Allow plain paths like C:\dir or C:/dir (scheme == "").
    if (parsed.scheme or "").lower() != "file":
        return Path(uri)

    # file:///C:/path or file://server/share/path
    raw_path = unquote(parsed.path or "")

    # UNC path: file://server/share/folder
    if parsed.netloc:
        unc = f"\\\\{parsed.netloc}{raw_path}"
        return Path(unc)

    # Windows drive letter paths from file:///C:/...
    if re.match(r"^/[A-Za-z]:/", raw_path):
        raw_path = raw_path[1:]

    if not raw_path:
        raise ValueError("Invalid file URI: missing path")

    return Path(raw_path)


def _get_description_config() -> _DescriptionConfig:
    """Parse RTI_INSTRUCTIONS_DESCRIPTION.

    Expected JSON:
        {"method":"head","params":{"n":200}}

    Notes:
        - If env var is missing/empty, defaults to method "metadata".
        - To ease manual authoring, also accepts Python-literal dict syntax
          (single quotes) via ast.literal_eval.
    """

    raw = (global_config.instructions_description or "").strip()
    if not raw:
        return _DescriptionConfig(method="metadata", params={})

    parsed: Any
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = ast.literal_eval(raw)

    if not isinstance(parsed, dict):
        raise ValueError(f"{_INSTRUCTIONS_DESCRIPTION_ENV} must be a JSON object")

    parsed_obj = cast(dict[str, Any], parsed)

    method_any = parsed_obj.get("method", "metadata")
    params_any = parsed_obj.get("params", {})

    if not isinstance(method_any, str) or not method_any.strip():
        raise ValueError(f"{_INSTRUCTIONS_DESCRIPTION_ENV}.method must be a non-empty string")
    if not isinstance(params_any, dict):
        raise ValueError(f"{_INSTRUCTIONS_DESCRIPTION_ENV}.params must be an object")

    method = method_any.strip().lower()
    params = cast(dict[str, Any], params_any)
    if method not in {"head", "metadata"}:
        raise ValueError(f"Unsupported {_INSTRUCTIONS_DESCRIPTION_ENV}.method '{method}'. Supported: head, metadata")

    return _DescriptionConfig(method=method, params=params)


def _describe(markdown: str, config: _DescriptionConfig) -> str:
    if config.method == "head":
        return _describe_head(markdown, config.params)
    if config.method == "metadata":
        return _describe_metadata(markdown)

    # Should not happen due to validation, but keep it safe.
    logger.warning(f"Unknown description method: {config.method}")
    return ""


def _describe_head(markdown: str, params: dict[str, Any]) -> str:
    n = params.get("n", 200)
    try:
        n_int = int(n)
    except Exception:
        n_int = 200

    if n_int <= 0:
        return ""

    body = _strip_frontmatter(markdown.lstrip("\ufeff"))
    compact = re.sub(r"\s+", " ", body).strip()
    return compact[:n_int]


def _describe_metadata(markdown: str) -> str:
    # "metadata" is explicitly YAML frontmatter only.
    frontmatter = _parse_frontmatter(markdown.lstrip("\ufeff"))
    if not frontmatter:
        return ""

    for key in ("abstract", "summary", "description"):
        value = frontmatter.get(key, "").strip()
        if value:
            return value

    # fallback: compact key/value lines
    compact = "\n".join(f"{k}: {v}" for k, v in frontmatter.items() if v.strip()).strip()
    return compact


def _strip_frontmatter(markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return markdown

    end_index: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break

    if end_index is None:
        return markdown

    return "\n".join(lines[end_index + 1 :]).lstrip()


def _parse_frontmatter(markdown: str) -> dict[str, str]:
    """Very small YAML-frontmatter parser.

    Supports simple scalar key/value lines:
        ---
        abstract: some text
        ---

    This is intentionally minimal to avoid introducing YAML dependencies.
    """

    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end_index: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break

    if end_index is None:
        return {}

    result: dict[str, str] = {}
    for line in lines[1:end_index]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        result[key.strip().lower()] = value.strip().strip('"').strip("'")

    return result
