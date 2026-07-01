from __future__ import annotations

import json

from hermes_token_dash.adapters.claude_code import ClaudeCodeAdapter


def _patch_paths(monkeypatch, tmp_path):
    from hermes_token_dash.adapters import claude_code as mod

    home = tmp_path / ".claude"
    settings = home / "settings.json"
    originals = tmp_path / "claude_code_proxy_originals.json"
    monkeypatch.setattr(mod, "CLAUDE_HOME", home)
    monkeypatch.setattr(mod, "SETTINGS_PATH", settings)
    monkeypatch.setattr(mod, "ORIGINALS_PATH", originals)
    return settings, originals


def test_set_proxy_url_updates_anthropic_base_url(monkeypatch, tmp_path):
    settings, originals = _patch_paths(monkeypatch, tmp_path)
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"theme": "dark", "env": {"OTHER": "value", "ANTHROPIC_BASE_URL": "https://api.example"}}),
        encoding="utf-8",
    )

    adapter = ClaudeCodeAdapter()

    assert adapter.set_proxy_url("http://127.0.0.1:8765/v1") is True

    cfg = json.loads(settings.read_text(encoding="utf-8"))
    assert cfg["theme"] == "dark"
    assert cfg["env"]["OTHER"] == "value"
    assert cfg["env"]["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:8765"
    assert json.loads(originals.read_text(encoding="utf-8")) == {
        "exists": True,
        "value": "https://api.example",
    }


def test_restore_original_restores_existing_value(monkeypatch, tmp_path):
    settings, originals = _patch_paths(monkeypatch, tmp_path)
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8765", "OTHER": "value"}}),
        encoding="utf-8",
    )
    originals.write_text(json.dumps({"exists": True, "value": "https://api.example"}), encoding="utf-8")

    adapter = ClaudeCodeAdapter()

    assert adapter.restore_original() is True

    cfg = json.loads(settings.read_text(encoding="utf-8"))
    assert cfg["env"]["ANTHROPIC_BASE_URL"] == "https://api.example"
    assert cfg["env"]["OTHER"] == "value"
    assert not originals.exists()


def test_restore_original_removes_value_when_absent_before_proxy(monkeypatch, tmp_path):
    settings, originals = _patch_paths(monkeypatch, tmp_path)
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8765", "OTHER": "value"}}),
        encoding="utf-8",
    )
    originals.write_text(json.dumps({"exists": False, "value": None}), encoding="utf-8")

    adapter = ClaudeCodeAdapter()

    assert adapter.restore_original() is True

    cfg = json.loads(settings.read_text(encoding="utf-8"))
    assert "ANTHROPIC_BASE_URL" not in cfg["env"]
    assert cfg["env"]["OTHER"] == "value"


def test_get_current_base_url(monkeypatch, tmp_path):
    settings, _originals = _patch_paths(monkeypatch, tmp_path)
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://api.example"}}), encoding="utf-8")

    adapter = ClaudeCodeAdapter()

    assert adapter.is_installed() is True
    assert adapter.get_current_base_url() == "https://api.example"
