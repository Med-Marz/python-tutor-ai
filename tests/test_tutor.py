import pytest

from tutor_ai.tutor import (
    MAX_QUESTION_CHARS,
    SYSTEM_PROMPT,
    InvalidQuestionError,
    answer,
    clean_question,
)


def test_clean_question_strips_spaces():
    assert clean_question("  What is a list?\n") == "What is a list?"


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_question_is_rejected(text):
    with pytest.raises(InvalidQuestionError, match="type a question"):
        clean_question(text)


def test_too_long_question_is_rejected():
    with pytest.raises(InvalidQuestionError, match="too long"):
        clean_question("x" * (MAX_QUESTION_CHARS + 1))


def test_question_at_the_limit_is_accepted():
    assert len(clean_question("x" * MAX_QUESTION_CHARS)) == MAX_QUESTION_CHARS


def test_answer_sends_system_prompt_and_cleaned_question(fake_ollama):
    reply = answer("  What is a tuple? ")
    sent = fake_ollama.last_request["messages"]
    assert sent[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert sent[1] == {"role": "user", "content": "What is a tuple?"}
    assert reply.text == "A tuple is immutable."


def test_invalid_question_never_reaches_the_model(fake_ollama):
    with pytest.raises(InvalidQuestionError):
        answer("   ")
    assert fake_ollama.last_request is None