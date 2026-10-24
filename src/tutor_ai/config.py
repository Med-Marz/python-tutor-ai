import os
from dataclasses import dataclass

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_CONNECT_TIMEOUT = 3.0
DEFAULT_READ_TIMEOUT = 120.0


class ConfigError(Exception):
    """A setting has an invalid value."""


@dataclass(frozen=True)
class Settings:
    base_url: str = DEFAULT_URL
    model: str = DEFAULT_MODEL
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT
    read_timeout: float = DEFAULT_READ_TIMEOUT


def _number(env, name, default):
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a number, got {raw!r}.") from None
    if not value > 0:
        raise ConfigError(f"{name} must be greater than 0, got {raw!r}.")
    return value


def load_settings(env=None) -> Settings:
    env = os.environ if env is None else env
    base_url = env.get("TUTOR_OLLAMA_URL", "").strip() or DEFAULT_URL
    model = env.get("TUTOR_MODEL", "").strip() or DEFAULT_MODEL
    return Settings(
        base_url=base_url.rstrip("/"),
        model=model,
        connect_timeout=_number(env, "TUTOR_CONNECT_TIMEOUT", DEFAULT_CONNECT_TIMEOUT),
        read_timeout=_number(env, "TUTOR_READ_TIMEOUT", DEFAULT_READ_TIMEOUT),
    )
