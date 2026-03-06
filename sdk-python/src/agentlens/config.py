"""SDK configuration. All settings can be overridden via environment variables."""

import os


class SDKConfig:
    """Configuration for the AgentLens Python SDK."""

    def __init__(
        self,
        server_url: str | None = None,
        http_url: str | None = None,
        agent_name: str | None = None,
        flush_interval: float = 1.0,
        max_buffer_size: int = 20,
        redact_sensitive: bool = True,
    ):
        self.server_url = server_url or os.getenv("AGENTLENS_WS_URL", "ws://localhost:8766/ws")
        self.http_url = http_url or os.getenv("AGENTLENS_HTTP_URL", "http://localhost:8766")
        self.agent_name = agent_name or os.getenv("AGENTLENS_AGENT_NAME", "python-agent")
        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size
        self.redact_sensitive = redact_sensitive


# Sensitive field names to redact from input/output data
SENSITIVE_KEYS = {"api_key", "token", "password", "secret", "authorization", "auth", "bearer"}

# Global config instance (replaced by init())
_global_config: SDKConfig | None = None


def get_config() -> SDKConfig:
    global _global_config
    if _global_config is None:
        _global_config = SDKConfig()
    return _global_config


def set_config(config: SDKConfig) -> None:
    global _global_config
    _global_config = config
