import sys
from unittest.mock import patch

from fabric_rti_mcp.config import GlobalFabricRTIConfig


class TestFromEnvBooleanParsing:
    @patch.dict("os.environ", {"USE_OBO_FLOW": "true"}, clear=False)
    def test_obo_flow_true_string(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_obo_flow is True

    @patch.dict("os.environ", {"USE_OBO_FLOW": "True"}, clear=False)
    def test_obo_flow_true_capitalized(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_obo_flow is True

    @patch.dict("os.environ", {"USE_OBO_FLOW": "1"}, clear=False)
    def test_obo_flow_one(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_obo_flow is True

    @patch.dict("os.environ", {"USE_OBO_FLOW": "false"}, clear=False)
    def test_obo_flow_false_string(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_obo_flow is False

    @patch.dict("os.environ", {"USE_OBO_FLOW": "0"}, clear=False)
    def test_obo_flow_zero(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_obo_flow is False

    @patch.dict("os.environ", {}, clear=False)
    def test_obo_flow_unset_defaults_false(self) -> None:
        import os

        os.environ.pop("USE_OBO_FLOW", None)
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_obo_flow is False

    @patch.dict("os.environ", {"FABRIC_RTI_STATELESS_HTTP": "true"}, clear=False)
    def test_stateless_http_true(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.stateless_http is True

    @patch.dict("os.environ", {"FABRIC_RTI_STATELESS_HTTP": "false"}, clear=False)
    def test_stateless_http_false(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.stateless_http is False

    @patch.dict("os.environ", {"FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA": "true"}, clear=False)
    def test_ai_foundry_compat_true(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_ai_foundry_compat is True

    @patch.dict("os.environ", {"FABRIC_RTI_AI_FOUNDRY_COMPATIBILITY_SCHEMA": "false"}, clear=False)
    def test_ai_foundry_compat_false(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.use_ai_foundry_compat is False

    @patch.dict("os.environ", {}, clear=False)
    def test_cors_allowed_origins_defaults_to_wildcard(self) -> None:
        import os

        os.environ.pop("FABRIC_RTI_CORS_ORIGINS", None)
        config = GlobalFabricRTIConfig.from_env()
        assert config.cors_allowed_origins == "*"

    @patch.dict("os.environ", {"FABRIC_RTI_CORS_ORIGINS": "https://example.com,https://other.com"}, clear=False)
    def test_cors_allowed_origins_custom_value(self) -> None:
        config = GlobalFabricRTIConfig.from_env()
        assert config.cors_allowed_origins == "https://example.com,https://other.com"
        origins = [o.strip() for o in config.cors_allowed_origins.split(",")]
        assert origins == ["https://example.com", "https://other.com"]


class TestWithArgsCLIOverride:
    @patch.dict("os.environ", {"USE_OBO_FLOW": "true"}, clear=False)
    def test_env_obo_respected_without_cli_flag(self) -> None:
        original_argv = sys.argv
        try:
            sys.argv = ["prog"]
            config = GlobalFabricRTIConfig.with_args()
            assert config.use_obo_flow is True
        finally:
            sys.argv = original_argv

    @patch.dict("os.environ", {"USE_OBO_FLOW": "true"}, clear=False)
    def test_cli_flag_overrides_env(self) -> None:
        original_argv = sys.argv
        try:
            sys.argv = ["prog", "--use-obo-flow"]
            config = GlobalFabricRTIConfig.with_args()
            assert config.use_obo_flow is True
        finally:
            sys.argv = original_argv

    @patch.dict("os.environ", {}, clear=False)
    def test_no_env_no_cli_defaults_false(self) -> None:
        import os

        os.environ.pop("USE_OBO_FLOW", None)
        original_argv = sys.argv
        try:
            sys.argv = ["prog"]
            config = GlobalFabricRTIConfig.with_args()
            assert config.use_obo_flow is False
        finally:
            sys.argv = original_argv

    @patch.dict("os.environ", {"FABRIC_RTI_STATELESS_HTTP": "true"}, clear=False)
    def test_env_stateless_http_respected_without_cli_flag(self) -> None:
        original_argv = sys.argv
        try:
            sys.argv = ["prog"]
            config = GlobalFabricRTIConfig.with_args()
            assert config.stateless_http is True
        finally:
            sys.argv = original_argv
