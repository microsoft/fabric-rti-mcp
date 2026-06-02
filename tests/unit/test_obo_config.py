import pytest

from fabric_rti_mcp.config.obo import (
    FabricRtiMcpOBOFlowAuthConfig,
    FabricRtiMcpOBOFlowEnvVarNames,
    normalize_obo_audience,
    parse_obo_audiences,
)


def test_normalize_obo_audience_accepts_resource_or_default_scope() -> None:
    assert normalize_obo_audience(" https://api.fabric.microsoft.com/.default ") == "https://api.fabric.microsoft.com"
    assert normalize_obo_audience("https://api.fabric.microsoft.com/") == "https://api.fabric.microsoft.com"


def test_parse_obo_audiences_dedupes_and_normalizes() -> None:
    assert parse_obo_audiences(
        "https://kusto.kusto.windows.net/.default, https://api.fabric.microsoft.com/,https://api.fabric.microsoft.com"
    ) == ("https://kusto.kusto.windows.net", "https://api.fabric.microsoft.com")


def test_default_allowed_obo_audiences_are_kusto_and_fabric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(FabricRtiMcpOBOFlowEnvVarNames.kusto_audience, raising=False)
    monkeypatch.delenv(FabricRtiMcpOBOFlowEnvVarNames.fabric_audience, raising=False)
    monkeypatch.delenv(FabricRtiMcpOBOFlowEnvVarNames.allowed_obo_audiences, raising=False)

    config = FabricRtiMcpOBOFlowAuthConfig.from_env()

    assert config.allowed_obo_audiences == ("https://kusto.kusto.windows.net", "https://api.fabric.microsoft.com")


def test_allowed_obo_audiences_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        FabricRtiMcpOBOFlowEnvVarNames.allowed_obo_audiences,
        "https://custom.example/.default,https://other.example/",
    )

    config = FabricRtiMcpOBOFlowAuthConfig.from_env()

    assert config.allowed_obo_audiences == ("https://custom.example", "https://other.example")
    assert config.require_allowed_audience("https://custom.example/.default") == "https://custom.example"


def test_require_allowed_audience_rejects_unlisted_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FabricRtiMcpOBOFlowEnvVarNames.allowed_obo_audiences, "https://allowed.example")
    config = FabricRtiMcpOBOFlowAuthConfig.from_env()

    with pytest.raises(ValueError, match="not in the allowed audience list"):
        config.require_allowed_audience("https://blocked.example")
