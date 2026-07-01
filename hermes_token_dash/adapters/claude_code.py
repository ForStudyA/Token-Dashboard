"""Claude Code config adapter.

Claude Code reads API gateway settings from ``~/.claude/settings.json`` under
the ``env`` object.  We only touch ``ANTHROPIC_BASE_URL`` and persist its
original value so shutdown restore can put the user's config back.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_token_dash.adapters.base import AgentAdapter

CLAUDE_HOME = Path.home() / ".claude"
SETTINGS_PATH = CLAUDE_HOME / "settings.json"
ORIGINALS_PATH = Path.home() / ".token-dashboard" / "claude_code_proxy_originals.json"
BASE_URL_KEY = "ANTHROPIC_BASE_URL"


class ClaudeCodeAdapter(AgentAdapter):
    def __init__(self) -> None:
        self._originals: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "claude_code"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    @property
    def config_path(self) -> Path:
        return SETTINGS_PATH

    def is_installed(self) -> bool:
        return SETTINGS_PATH.exists() or CLAUDE_HOME.exists()

    def get_current_base_url(self) -> str | None:
        cfg = self._read_settings()
        env = cfg.get("env")
        if isinstance(env, dict):
            value = env.get(BASE_URL_KEY)
            return str(value) if value else None
        return None

    def set_proxy_url(self, proxy_url: str) -> bool:
        try:
            self._save_original()
            cfg = self._read_settings()
            env = cfg.get("env")
            if not isinstance(env, dict):
                env = {}
            env[BASE_URL_KEY] = self._anthropic_base_url(proxy_url)
            cfg["env"] = env
            self._write_settings(cfg)
            return True
        except Exception:
            return False

    def restore_original(self) -> bool:
        try:
            if not self._originals and ORIGINALS_PATH.exists():
                self._originals = json.loads(ORIGINALS_PATH.read_text(encoding="utf-8"))
            original_exists = bool(self._originals.get("exists"))
            original_value = self._originals.get("value")
            cfg = self._read_settings()
            env = cfg.get("env")
            if not isinstance(env, dict):
                env = {}
            if original_exists:
                env[BASE_URL_KEY] = original_value
            else:
                env.pop(BASE_URL_KEY, None)
            cfg["env"] = env
            self._write_settings(cfg)
            self._originals.clear()
            if ORIGINALS_PATH.exists():
                ORIGINALS_PATH.unlink()
            return True
        except Exception:
            return False

    def _save_original(self) -> None:
        if ORIGINALS_PATH.exists():
            try:
                loaded = json.loads(ORIGINALS_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self._originals = loaded
                    return
            except Exception:
                pass
        cfg = self._read_settings()
        env = cfg.get("env") if isinstance(cfg.get("env"), dict) else {}
        self._originals = {
            "exists": BASE_URL_KEY in env,
            "value": env.get(BASE_URL_KEY),
        }
        ORIGINALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ORIGINALS_PATH.write_text(json.dumps(self._originals, indent=2), encoding="utf-8")

    def _read_settings(self) -> dict[str, Any]:
        if not SETTINGS_PATH.exists():
            return {}
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8") or "{}")

    def _write_settings(self, cfg: dict[str, Any]) -> None:
        CLAUDE_HOME.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _anthropic_base_url(self, proxy_url: str) -> str:
        base = proxy_url.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        return base
