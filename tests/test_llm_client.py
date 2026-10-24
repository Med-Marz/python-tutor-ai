import tutor_ai.llm_client as client
from tutor_ai.llm_client import ask


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