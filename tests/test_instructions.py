"""Tests for server instructions functionality."""

from mcp.server.fastmcp import FastMCP

from fabric_rti_mcp.instructions import SERVER_INSTRUCTIONS


def test_server_instructions_exist() -> None:
    """Test that server instructions are defined and non-empty."""
    assert SERVER_INSTRUCTIONS is not None
    assert len(SERVER_INSTRUCTIONS) > 0
    assert "Microsoft Fabric Real-Time Intelligence" in SERVER_INSTRUCTIONS


def test_server_instructions_content() -> None:
    """Test that server instructions contain expected sections."""
    # Check for key sections
    assert "Available Services" in SERVER_INSTRUCTIONS
    assert "Kusto/Eventhouse Service" in SERVER_INSTRUCTIONS
    assert "Eventstream Service" in SERVER_INSTRUCTIONS
    assert "Common Workflows" in SERVER_INSTRUCTIONS
    assert "Example Usage Patterns" in SERVER_INSTRUCTIONS
    assert "Important Considerations" in SERVER_INSTRUCTIONS

    # Check for tool mentions
    assert "kusto_query" in SERVER_INSTRUCTIONS
    assert "eventstream_list" in SERVER_INSTRUCTIONS

    # Check for best practices
    assert "Best Practices" in SERVER_INSTRUCTIONS
    assert "Security" in SERVER_INSTRUCTIONS


def test_fastmcp_with_instructions() -> None:
    """Test that FastMCP correctly accepts and stores instructions."""
    mcp = FastMCP("test-server", instructions=SERVER_INSTRUCTIONS)

    assert mcp.instructions is not None
    assert mcp.instructions == SERVER_INSTRUCTIONS
    assert len(mcp.instructions) > 0


def test_fastmcp_without_instructions() -> None:
    """Test that FastMCP works without instructions (baseline)."""
    mcp = FastMCP("test-server")

    assert mcp.instructions is None


def test_instructions_format() -> None:
    """Test that instructions are properly formatted."""
    lines = SERVER_INSTRUCTIONS.split("\n")

    # Should not be just one long line
    assert len(lines) > 10

    # Should not have excessively long lines (for readability)
    max_line_length = max(len(line) for line in lines)
    assert max_line_length < 200  # Reasonable line length limit
