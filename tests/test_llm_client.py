import json
import socket

import pytest

import tutor_ai.llm_client as client
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
    assert sent["model"] == client.MODEL
    assert sent["messages"][-1] == {"role": "user", "content": "What is a list?"}
    assert sent["stream"] is False


def test_server_down(monkeypatch):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    monkeypatch.setattr(client, "URL", f"http://127.0.0.1:{port}/api/chat")
    with pytest.raises(LLMUnavailableError):
        ask("hi")


def test_timeout(fake_ollama, monkeypatch):
    fake_ollama.delay = 1
    monkeypatch.setattr(client, "TIMEOUT", 0.3)
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


def test_ask_sends_system_prompt(fake_ollama):
    ask("hi", "Be brief.")
    assert fake_ollama.last_request["messages"][0] == {"role": "system", "content": "Be brief."}
