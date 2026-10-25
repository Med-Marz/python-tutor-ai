import json
import logging
import socket

import httpx
import pytest

from tutor_ai.llm_client import (
    InvalidResponseError,
    LLMHTTPError,
    LLMTimeoutError,
    LLMUnavailableError,
    ModelNotFoundError,
    ask,
)


def test_ask_returns_reply(fake_ollama):
    reply = ask("What is a tuple?")
    assert reply.text == "A tuple is immutable."
    assert reply.eval_count == 60
    assert reply.eval_seconds == 10.0
    assert reply.seconds >= 0


def test_ask_sends_model_and_question(fake_ollama):
    ask("What is a list?")
    sent = fake_ollama.last_request
    assert sent["model"] == "llama3.2:3b"
    assert sent["messages"][-1] == {"role": "user", "content": "What is a list?"}
    assert sent["stream"] is False


def test_ask_uses_model_from_settings(fake_ollama, monkeypatch):
    monkeypatch.setenv("TUTOR_MODEL", "gemma3:4b")
    ask("hi")
    assert fake_ollama.last_request["model"] == "gemma3:4b"


def test_ask_sends_system_prompt(fake_ollama):
    ask("hi", "Be brief.")
    assert fake_ollama.last_request["messages"][0] == {"role": "system", "content": "Be brief."}


def test_server_down(monkeypatch):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    monkeypatch.setenv("TUTOR_OLLAMA_URL", f"http://127.0.0.1:{port}")
    with pytest.raises(LLMUnavailableError):
        ask("hi")


def test_connect_timeout_means_unavailable(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ConnectTimeout("too slow")

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(LLMUnavailableError, match="timed out"):
        ask("hi")


def test_timeout(fake_ollama, monkeypatch):
    fake_ollama.delay = 1
    monkeypatch.setenv("TUTOR_READ_TIMEOUT", "0.3")
    with pytest.raises(LLMTimeoutError):
        ask("hi")


def test_model_not_found(fake_ollama):
    fake_ollama.status = 404
    fake_ollama.body = json.dumps({"error": "model 'llama3.2:3b' not found"}).encode()
    with pytest.raises(ModelNotFoundError, match="ollama pull"):
        ask("hi")


def test_other_http_error(fake_ollama):
    fake_ollama.status = 500
    fake_ollama.body = b'{"error": "boom"}'
    with pytest.raises(LLMHTTPError, match="500"):
        ask("hi")


EMPTY_ANSWER = json.dumps(
    {"message": {"content": "   "}, "eval_count": 1, "eval_duration": 1}
).encode()


@pytest.mark.parametrize(
    "body",
    [b"this is not json", b'{"done": true}', EMPTY_ANSWER],
    ids=["not-json", "missing-fields", "empty-answer"],
)
def test_invalid_response(fake_ollama, body):
    fake_ollama.body = body
    with pytest.raises(InvalidResponseError):
        ask("hi")


def test_success_is_logged_without_the_question_text(fake_ollama, caplog):
    caplog.set_level(logging.INFO, logger="tutor_ai")
    ask("What is a tuple?")
    assert "request ok" in caplog.text
    assert "eval_count=60" in caplog.text
    assert "tokens_per_s=6.00" in caplog.text
    assert "question_chars=16" in caplog.text
    assert "What is a tuple?" not in caplog.text


def test_failure_is_logged_without_the_question_text(fake_ollama, caplog):
    fake_ollama.status = 500
    caplog.set_level(logging.WARNING, logger="tutor_ai")
    with pytest.raises(LLMHTTPError):
        ask("my secret question")
    assert "request failed" in caplog.text
    assert "error=LLMHTTPError" in caplog.text
    assert "my secret question" not in caplog.text
