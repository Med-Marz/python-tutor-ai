import pytest

from tutor_ai.config import ConfigError, load_settings


def test_defaults():
    s = load_settings({})
    assert s.base_url == "http://127.0.0.1:11434"
    assert s.model == "llama3.2:3b"
    assert s.connect_timeout == 3.0
    assert s.read_timeout == 120.0


def test_environment_values_override_defaults():
    s = load_settings(
        {
            "TUTOR_OLLAMA_URL": "http://example:1234",
            "TUTOR_MODEL": "gemma3:4b",
            "TUTOR_CONNECT_TIMEOUT": "1.5",
            "TUTOR_READ_TIMEOUT": "300",
        }
    )
    assert s.base_url == "http://example:1234"
    assert s.model == "gemma3:4b"
    assert s.connect_timeout == 1.5
    assert s.read_timeout == 300.0


def test_trailing_slash_is_removed():
    assert load_settings({"TUTOR_OLLAMA_URL": "http://example:1234/"}).base_url == (
        "http://example:1234"
    )


def test_blank_values_use_defaults():
    s = load_settings({"TUTOR_MODEL": "  ", "TUTOR_READ_TIMEOUT": ""})
    assert s.model == "llama3.2:3b"
    assert s.read_timeout == 120.0


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("TUTOR_READ_TIMEOUT", "abc"),
        ("TUTOR_CONNECT_TIMEOUT", "0"),
        ("TUTOR_READ_TIMEOUT", "-5"),
        ("TUTOR_CONNECT_TIMEOUT", "nan"),
    ],
)
def test_invalid_numbers_are_rejected(name, value):
    with pytest.raises(ConfigError, match=name):
        load_settings({name: value})


def test_reads_the_real_environment_by_default(monkeypatch):
    monkeypatch.setenv("TUTOR_MODEL", "gemma3:4b")
    assert load_settings().model == "gemma3:4b"
