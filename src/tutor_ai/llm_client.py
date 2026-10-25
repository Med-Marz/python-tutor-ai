import time
from dataclasses import dataclass

import httpx

from tutor_ai.config import Settings, load_settings


class LLMError(Exception):
    """Base class for every error raised by this client."""


class LLMUnavailableError(LLMError):
    """Ollama cannot be reached."""


class LLMTimeoutError(LLMError):
    """The model took too long to answer."""


class ModelNotFoundError(LLMError):
    """The requested model is not installed in Ollama."""


class LLMHTTPError(LLMError):
    """Ollama answered with an unexpected HTTP status."""


class InvalidResponseError(LLMError):
    """The reply could not be understood or was empty."""


@dataclass
class Reply:
    text: str
    seconds: float
    eval_count: int
    eval_seconds: float


def ask(
    question: str,
    system_prompt: str | None = None,
    settings: Settings | None = None,
) -> Reply:
    settings = settings or load_settings()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    payload = {
        "model": settings.model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 100},
    }
    url = f"{settings.base_url}/api/chat"
    timeout = httpx.Timeout(settings.read_timeout, connect=settings.connect_timeout)

    start = time.perf_counter()
    try:
        response = httpx.post(url, json=payload, timeout=timeout)
    except httpx.ConnectTimeout as exc:
        raise LLMUnavailableError("Cannot reach Ollama: the connection timed out.") from exc
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError("The model took too long to answer.") from exc
    except httpx.TransportError as exc:
        raise LLMUnavailableError("Cannot reach Ollama. Is it running?") from exc
    seconds = time.perf_counter() - start

    if response.status_code == 404:
        raise ModelNotFoundError(
            f"Model '{settings.model}' not found. Try: ollama pull {settings.model}"
        )
    if response.status_code != 200:
        raise LLMHTTPError(f"Ollama returned HTTP {response.status_code}.")

    try:
        data = response.json()
        text = data["message"]["content"]
        eval_count = data["eval_count"]
        eval_seconds = data["eval_duration"] / 1_000_000_000
    except (ValueError, KeyError, TypeError) as exc:
        raise InvalidResponseError("Ollama sent an unexpected response.") from exc
    if not isinstance(text, str) or not text.strip():
        raise InvalidResponseError("The model returned an empty answer.")

    return Reply(text=text, seconds=seconds, eval_count=eval_count, eval_seconds=eval_seconds)
