from types import SimpleNamespace

import pytest

from fabric_rti_mcp.server import build_transport_security_settings


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
