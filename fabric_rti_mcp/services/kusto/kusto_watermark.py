from __future__ import annotations

import json
import os
import re

from fabric_rti_mcp import __version__  # type: ignore
from fabric_rti_mcp.config import logger


def _sanitize_value(value: str) -> str:
    """Remove newlines and carriage returns from a watermark value to prevent query injection."""
    return re.sub(r"[\r\n]+", " ", value).strip()


def _resolve_custom_watermark(custom_watermark_json: str) -> dict[str, str]:
    """Resolve custom watermark entries from a JSON mapping.

    Values can be either:
    - A literal string (used as-is), e.g. ``"my-team"``
    - An ``env:`` prefixed string to resolve from an environment variable, e.g. ``"env:MY_APP_ID"``

    :param custom_watermark_json: JSON string, e.g.
        ``'{"team": "my-team", "app_id": "env:MY_APP_ID"}'``.
    :return: Resolved dict mapping custom keys to their final values.
    """
    try:
        mapping = json.loads(custom_watermark_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse custom watermark JSON: {e}. Skipping custom watermark.")
        return {}

    if not isinstance(mapping, dict):
        logger.error("Custom watermark must be a JSON object mapping keys to values.")
        return {}

    resolved: dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(value, str):
            logger.warning(f"Custom watermark value for '{key}' is not a string, skipping.")
            continue
        resolved_value = os.getenv(value[4:], "") if value.startswith("env:") else value
        sanitized = _sanitize_value(resolved_value)
        if sanitized:
            resolved[key] = sanitized
    return resolved


CUSTOM_WATERMARK_ENV_VAR = "FABRIC_RTI_KUSTO_CUSTOM_WATERMARK"


def build_watermark() -> str:
    """Build a KQL comment watermark to prepend to queries.

    The watermark is a single-line KQL comment containing a JSON object with:
    - ``fabric_rti_mcp_version``: the current package version
    - ``user``: the OS-level username (best effort)
    - any custom key-value pairs resolved from the ``FABRIC_RTI_KUSTO_CUSTOM_WATERMARK`` env var

    :return: A KQL comment string ending with a newline, e.g.
        ``// {"fabric_rti_mcp_version": "0.1.0", "user": "alice"}\\n``
    """
    watermark_data: dict[str, str] = {
        "fabric_rti_mcp_version": __version__,
    }

    # Best-effort user detection
    user = os.getenv("USER") or os.getenv("USERNAME") or ""
    if user:
        watermark_data["user"] = _sanitize_value(user)

    # Resolve custom watermark entries
    custom_watermark_json = os.getenv(CUSTOM_WATERMARK_ENV_VAR)
    if custom_watermark_json:
        custom_entries = _resolve_custom_watermark(custom_watermark_json)
        watermark_data.update(sorted(custom_entries.items()))

    return f"// {json.dumps(watermark_data)}\n"


def add_watermark(query: str) -> str:
    """Prepend a watermark comment to a KQL query.

    Watermarking is opt-in: the query is returned unchanged unless the
    ``FABRIC_RTI_KUSTO_CUSTOM_WATERMARK`` environment variable is set (set it
    to ``{}`` to enable watermarking without any custom entries). Control
    commands (starting with '.') cannot have comments prepended, so they are
    also returned unchanged.
    """
    if query.lstrip().startswith("."):
        return query
    if os.getenv(CUSTOM_WATERMARK_ENV_VAR) is None:
        return query
    return build_watermark() + query
