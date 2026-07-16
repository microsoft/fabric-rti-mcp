import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.compat.ms_foundry import SchemaCompatibleMCP
from fabric_rti_mcp.server import add_allowed_tools, build_transport_security_settings, register_tools
from fabric_rti_mcp.services import AddTool
from fabric_rti_mcp.services.activator import activator_tools
from fabric_rti_mcp.services.eventstream import eventstream_tools
from fabric_rti_mcp.services.kusto import kusto_tools
from fabric_rti_mcp.services.kusto.kusto_config import KustoConfig


def _tool_names(mcp: FastMCP) -> set[str]:
    return {tool.name for tool in asyncio.run(mcp.list_tools())}


def test_add_allowed_tools_skips_services_and_filters_tools() -> None:
    visited_services: list[str] = []
    registered_tools: list[str] = []

    def kusto_query() -> None:
        pass

    def map_get() -> None:
        pass

    def map_list() -> None:
        pass

    def eventstream_list() -> None:
        pass

    def service(name: str, *tools: Any) -> SimpleNamespace:
        def register_service_tools(add_tool: AddTool) -> None:
            visited_services.append(name)
            for tool in tools:
                add_tool(tool)

        return SimpleNamespace(
            __name__=f"fabric_rti_mcp.services.{name}.{name}_tools",
            register_tools=register_service_tools,
        )

    services = (
        service("kusto", kusto_query),
        service("eventstream", eventstream_list),
        service("map", map_get, map_list),
    )

    add_allowed_tools(
        services,
        {"kusto", "map_get"},
        lambda tool, **kwargs: registered_tools.append(tool.__name__),
    )

    assert visited_services == ["kusto", "map"]
    assert registered_tools == ["kusto_query", "map_get"]


@pytest.mark.parametrize("mcp_class", [FastMCP, SchemaCompatibleMCP])
def test_register_tools_allows_services_and_full_tool_names(
    monkeypatch: pytest.MonkeyPatch, mcp_class: type[FastMCP]
) -> None:
    monkeypatch.setenv("FABRIC_RTI_ALLOWED_TOOLS", "kusto,map_get")
    monkeypatch.setattr(kusto_tools.kusto_service, "CONFIG", KustoConfig())
    monkeypatch.setattr(
        eventstream_tools,
        "register_tools",
        lambda add_tool: pytest.fail("Excluded eventstream service should not be visited"),
    )
    monkeypatch.setattr(
        activator_tools,
        "register_tools",
        lambda add_tool: pytest.fail("Excluded activator service should not be visited"),
    )
    mcp = mcp_class("test")

    register_tools(mcp)
    tool_names = _tool_names(mcp)

    assert "kusto_query" in tool_names
    assert "map_get" in tool_names
    assert "map_list" not in tool_names
    assert all(name.startswith("kusto_") or name == "map_get" for name in tool_names)


def test_register_tools_rejects_unknown_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FABRIC_RTI_ALLOWED_TOOLS", "maps")
    mcp = FastMCP("test")

    with pytest.raises(ValueError, match="Unknown entries in FABRIC_RTI_ALLOWED_TOOLS: maps"):
        register_tools(mcp)


def test_get_shots_is_hidden_without_configured_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FABRIC_RTI_ALLOWED_TOOLS", raising=False)
    monkeypatch.setattr(kusto_tools.kusto_service, "CONFIG", KustoConfig())
    mcp = FastMCP("test")

    register_tools(mcp)

    assert "kusto_get_shots" not in _tool_names(mcp)


def test_get_shots_registration_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FABRIC_RTI_ALLOWED_TOOLS", raising=False)
    monkeypatch.setattr(kusto_tools.kusto_service, "CONFIG", KustoConfig(shots_table="Shots"))
    mcp = FastMCP("test")

    register_tools(mcp)
    get_shots = next(tool for tool in asyncio.run(mcp.list_tools()) if tool.name == "kusto_get_shots")

    assert get_shots.description is not None
    assert get_shots.description.strip().splitlines()[0] == "Find similar saved KQL queries."
    assert get_shots.annotations is not None
    assert get_shots.annotations.readOnlyHint is True


def test_transport_security_uses_explicit_allowlists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "fabric_rti_mcp.server.config",
        SimpleNamespace(
            http_host="0.0.0.0",
            http_allowed_hosts="mcp.example.com:*,127.0.0.1:*",
            http_allowed_origins="https://mcp.example.com",
        ),
    )

    settings = build_transport_security_settings()

    assert settings is not None
    assert settings.allowed_hosts == ["mcp.example.com:*", "127.0.0.1:*"]
    assert settings.allowed_origins == ["https://mcp.example.com"]


def test_transport_security_requires_hosts_when_origins_are_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "fabric_rti_mcp.server.config",
        SimpleNamespace(
            http_host="0.0.0.0",
            http_allowed_hosts="",
            http_allowed_origins="https://mcp.example.com",
        ),
    )

    with pytest.raises(ValueError, match="FABRIC_RTI_HTTP_ALLOWED_HOSTS"):
        build_transport_security_settings()


def test_non_loopback_without_allowlist_fails_closed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "fabric_rti_mcp.server.config",
        SimpleNamespace(
            http_host="0.0.0.0",
            http_allowed_hosts="",
            http_allowed_origins="",
            http_debug_mode=False,
        ),
    )

    with pytest.raises(ValueError, match="HTTP host is non-loopback"):
        build_transport_security_settings()


def test_non_loopback_without_allowlist_is_allowed_only_in_debug_mode(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(
        "fabric_rti_mcp.server.config",
        SimpleNamespace(
            http_host="0.0.0.0",
            http_allowed_hosts="",
            http_allowed_origins="",
            http_debug_mode=True,
        ),
    )

    with caplog.at_level("WARNING", logger="fabric-rti-mcp"):
        settings = build_transport_security_settings()

    assert settings is None
    assert "FABRIC_RTI_HTTP_DEBUG_MODE=true" in caplog.text
