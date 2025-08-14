import logging
import os
import sys
from typing import Optional

logger = logging.getLogger("fabric-rti-mcp")


handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger.addHandler(handler)


class Config:
    """Global configuration for fabric-rti-mcp."""

    def __init__(self) -> None:
        self._kusto_timeout_seconds: Optional[int] = None
        self._load_kusto_timeout()

    def _load_kusto_timeout(self) -> None:
        """Load Kusto timeout from environment variable."""
        timeout_env = os.getenv("FABRIC_RTI_KUSTO_TIMEOUT")
        if timeout_env:
            try:
                self._kusto_timeout_seconds = int(timeout_env)
            except ValueError:
                # Ignore invalid timeout values
                pass

    @property
    def kusto_timeout_seconds(self) -> Optional[int]:
        """Get the global Kusto timeout in seconds."""
        return self._kusto_timeout_seconds

    @kusto_timeout_seconds.setter
    def kusto_timeout_seconds(self, value: Optional[int]) -> None:
        """Set the global Kusto timeout in seconds."""
        self._kusto_timeout_seconds = value

    @kusto_timeout_seconds.deleter
    def kusto_timeout_seconds(self) -> None:
        """Delete the global Kusto timeout."""
        self._kusto_timeout_seconds = None


# Global configuration instance
config = Config()
