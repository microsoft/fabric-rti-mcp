from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from fabric_rti_mcp.services.instructions import instructions_service


def test_list_and_load_from_file_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a = tmp_path / "a.md"
    a.write_text(
        "---\nabstract: Alpha instructions\n---\n\n# A\n\nHello\n",
        encoding="utf-8",
    )
    b = tmp_path / "b.md"
    b.write_text(
        "---\nsummary: Beta summary\n---\n\n# B\n\nWorld\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        instructions_service,
        "global_config",
        replace(
            instructions_service.global_config,
            instructions_uri=tmp_path.as_uri(),
            instructions_description='{"method":"metadata","params":{}}',
        ),
    )

    items = instructions_service.common_instructions_list()
    assert ("a.md", "Alpha instructions") in items
    assert ("b.md", "Beta summary") in items

    loaded = instructions_service.common_instructions_load("a.md")
    assert "# A" in loaded
    assert "Alpha instructions" in loaded


def test_description_head_strips_frontmatter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text(
        "---\nabstract: Hidden\n---\n\n# Title\n\nHello world, this is the body.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        instructions_service,
        "global_config",
        replace(
            instructions_service.global_config,
            instructions_uri=tmp_path.as_uri(),
            instructions_description='{"method":"head","params":{"n":12}}',
        ),
    )

    items = dict(instructions_service.common_instructions_list())
    assert items["doc.md"].startswith("# Title")
