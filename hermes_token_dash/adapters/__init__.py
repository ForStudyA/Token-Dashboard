from hermes_token_dash.adapters.base import AgentAdapter
from hermes_token_dash.adapters.claude_code import ClaudeCodeAdapter
from hermes_token_dash.adapters.hermes import HermesAdapter

ADAPTERS: dict[str, type[AgentAdapter]] = {
    "claude_code": ClaudeCodeAdapter,
    "hermes": HermesAdapter,
}

def get_adapter(name: str) -> AgentAdapter:
    cls = ADAPTERS.get(name)
    if not cls:
        raise ValueError(f"Unknown adapter: {name}")
    return cls()
