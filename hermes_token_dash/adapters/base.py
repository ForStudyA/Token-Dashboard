"""Base adapter interface for AI agent config file manipulation.

Each agent (Hermes, Claude Code, Codex, etc.) implements this interface
to read/write/restore its API endpoint configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class AgentAdapter(ABC):
    """Abstract base class for agent config adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier (e.g. 'hermes', 'claude_code', 'codex')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI display."""

    @property
    @abstractmethod
    def config_path(self) -> Path:
        """Path to the agent's config file."""

    @abstractmethod
    def is_installed(self) -> bool:
        """Return True if the agent's config file exists."""

    @abstractmethod
    def get_current_base_url(self) -> str | None:
        """Read the current API base URL from the agent's config.

        Returns None if no base URL is configured.
        """

    @abstractmethod
    def set_proxy_url(self, proxy_url: str) -> bool:
        """Modify the agent's config to route API traffic through proxy_url.

        Returns True if the config was modified successfully.
        The original URL should be saved internally for later restore.
        """

    @abstractmethod
    def restore_original(self) -> bool:
        """Restore the agent's config to its original base URL.

        Returns True if the config was restored successfully.
        """

    def get_status(self) -> dict[str, Any]:
        """Return current adapter status for API responses."""
        installed = self.is_installed()
        current_url = self.get_current_base_url() if installed else None
        return {
            "name": self.name,
            "display_name": self.display_name,
            "installed": installed,
            "config_path": str(self.config_path),
            "current_base_url": current_url,
        }
