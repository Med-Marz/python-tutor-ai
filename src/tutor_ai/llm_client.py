import logging
import time
from dataclasses import dataclass

import httpx

from tutor_ai.config import Settings, load_settings

logger = logging.getLogger(__name__)


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


def _call_model(question: str, system_prompt: str | None, settings: Settings) -> Reply:
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


def ask(
    question: str,
    system_prompt: str | None = None,
    settings: Settings | None = None,
) -> Reply:
    settings = settings or load_settings()
    start = time.perf_counter()
    try:
        reply = _call_model(question, system_prompt, settings)
    except LLMError as exc:
        logger.warning(
            "request failed model=%s error=%s seconds=%.2f question_chars=%d",
            settings.model,
            type(exc).__name__,
            time.perf_counter() - start,
            len(question),
        )
        raise
    tokens_per_s = reply.eval_count / reply.eval_seconds if reply.eval_seconds > 0 else 0.0
    logger.info(
        "request ok model=%s seconds=%.2f eval_count=%d eval_seconds=%.2f "
        "tokens_per_s=%.2f question_chars=%d",
        settings.model,
        reply.seconds,
        reply.eval_count,
        reply.eval_seconds,
        tokens_per_s,
        len(question),
    )
    return reply
