from unittest.mock import MagicMock, patch

import pytest

from fabric_rti_mcp.services.kusto.kusto_service import kusto_get_shots

CLUSTER_URI = "https://help.kusto.windows.net"
SHOTS_TABLE = "Shots"


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_uses_aoai_by_default(mock_execute: MagicMock) -> None:
    endpoint = "https://example.openai.azure.com/embeddings;impersonate"

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
        embedding_endpoint=endpoint,
    )

    query = mock_execute.call_args.args[0]
    assert "ai_embeddings" in query
    assert endpoint in query
    assert "slm_embeddings_fl" not in query
    assert "series_cosine_similarity(embedded_term, EmbeddingVector, 1.0, 1.0)" in query


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_uses_configured_slm_defaults(mock_execute: MagicMock, mock_config: MagicMock) -> None:
    mock_config.shots_table = None
    mock_config.shots_embedding_method = "slm"
    mock_config.shots_slm_model = "harrier-v1-270m"

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
    )

    query = mock_execute.call_args.args[0]
    assert "slm_embeddings_fl" in query
    assert "model_name='harrier-v1-270m'" in query
    assert "ai_embeddings" not in query
    assert "series_cosine_similarity(embedded_term, EmbeddingVector, 1.0, 1.0)" in query
    assert mock_execute.call_args.kwargs["readonly_override"] is True


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_uses_and_escapes_custom_slm_model(mock_execute: MagicMock) -> None:
    kusto_get_shots(
        "Find the user's storms",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
        embedding_method="slm",
        slm_model_name="custom'model",
    )

    query = mock_execute.call_args.args[0]
    assert "Find the user''s storms" in query
    assert "model_name='custom''model'" in query


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_rejects_explicit_empty_slm_model(mock_execute: MagicMock) -> None:
    with pytest.raises(ValueError, match="slm_model_name must not be empty"):
        kusto_get_shots(
            "Find storms in Texas",
            CLUSTER_URI,
            shots_table_name=SHOTS_TABLE,
            embedding_method="slm",
            slm_model_name="",
        )

    mock_execute.assert_not_called()


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_uses_aoai_when_explicitly_selected(mock_execute: MagicMock) -> None:
    endpoint = "https://example.openai.azure.com/embeddings;impersonate"

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
        embedding_method="aoai",
        embedding_endpoint=endpoint,
    )

    query = mock_execute.call_args.args[0]
    assert "ai_embeddings" in query
    assert endpoint in query
    assert "slm_embeddings_fl" not in query
    assert mock_execute.call_args.kwargs["readonly_override"] is False


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_aoai_uses_configured_endpoint(mock_execute: MagicMock, mock_config: MagicMock) -> None:
    mock_config.shots_table = None
    mock_config.open_ai_embedding_endpoint = "https://configured.openai.azure.com/embeddings;impersonate"

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
        embedding_method="aoai",
    )

    query = mock_execute.call_args.args[0]
    assert mock_config.open_ai_embedding_endpoint in query


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_aoai_requires_endpoint(mock_execute: MagicMock, mock_config: MagicMock) -> None:
    mock_config.shots_table = None
    mock_config.shots_embedding_method = "aoai"
    mock_config.open_ai_embedding_endpoint = None

    with pytest.raises(ValueError, match="embedding_endpoint must be provided"):
        kusto_get_shots(
            "Find storms in Texas",
            CLUSTER_URI,
            shots_table_name=SHOTS_TABLE,
        )

    mock_execute.assert_not_called()


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_slm_ignores_embedding_endpoint(mock_execute: MagicMock) -> None:
    endpoint = "https://example.openai.azure.com/embeddings"

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
        embedding_endpoint=endpoint,
        embedding_method="slm",
    )

    query = mock_execute.call_args.args[0]
    assert "slm_embeddings_fl" in query
    assert "ai_embeddings" not in query
    assert endpoint not in query


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_rejects_unknown_embedding_method(mock_execute: MagicMock) -> None:
    with pytest.raises(ValueError, match="embedding_method must be either"):
        kusto_get_shots(
            "Find storms in Texas",
            CLUSTER_URI,
            shots_table_name=SHOTS_TABLE,
            embedding_method="unsupported",  # type: ignore[arg-type]
        )

    mock_execute.assert_not_called()


@patch("fabric_rti_mcp.services.kusto.kusto_service.CONFIG")
@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_requires_shots_table(mock_execute: MagicMock, mock_config: MagicMock) -> None:
    mock_config.shots_table = None

    with pytest.raises(ValueError, match="shots_table_name must be provided"):
        kusto_get_shots("Find storms in Texas", CLUSTER_URI)

    mock_execute.assert_not_called()


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_forwards_execution_arguments(mock_execute: MagicMock) -> None:
    request_properties = {"query_results_cache_max_age": "00:05:00"}

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        shots_table_name=SHOTS_TABLE,
        database="Samples",
        embedding_method="slm",
        client_request_properties=request_properties,
    )

    mock_execute.assert_called_once()
    assert mock_execute.call_args.args[1] == CLUSTER_URI
    assert mock_execute.call_args.kwargs == {
        "readonly_override": True,
        "database": "Samples",
        "client_request_properties": request_properties,
    }


@patch("fabric_rti_mcp.services.kusto.kusto_service._execute")
def test_get_shots_preserves_client_request_properties_positional_argument(mock_execute: MagicMock) -> None:
    request_properties = {"query_results_cache_max_age": "00:05:00"}
    endpoint = "https://example.openai.azure.com/embeddings;impersonate"

    kusto_get_shots(
        "Find storms in Texas",
        CLUSTER_URI,
        SHOTS_TABLE,
        3,
        "Samples",
        endpoint,
        request_properties,
    )

    assert mock_execute.call_args.kwargs["client_request_properties"] is request_properties
