from tutor_ai.main import main


def feed(monkeypatch, lines):
    it = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)


def test_exit_ends_the_session(monkeypatch, capsys):
    feed(monkeypatch, ["exit"])
    assert main() == 0
    assert "Bye." in capsys.readouterr().out


def test_answer_and_time_are_printed(monkeypatch, capsys, fake_ollama):
    feed(monkeypatch, ["What is a tuple?", "exit"])
    assert main() == 0
    out = capsys.readouterr().out
    assert "A tuple is immutable." in out
    assert " s)" in out


def test_empty_question_shows_error_and_session_continues(monkeypatch, capsys, fake_ollama):
    feed(monkeypatch, ["", "exit"])
    assert main() == 0
    out = capsys.readouterr().out
    assert "Error: Please type a question." in out
    assert "Thinking..." not in out
    assert "Bye." in out
    assert fake_ollama.last_request is None


def test_model_error_does_not_end_the_session(monkeypatch, capsys, fake_ollama):
    fake_ollama.status = 500
    feed(monkeypatch, ["hi", "exit"])
    assert main() == 0
    out = capsys.readouterr().out
    assert "Error: Ollama returned HTTP 500." in out
    assert "Bye." in out


def test_ctrl_d_ends_the_session(monkeypatch, capsys):
    feed(monkeypatch, [])
    assert main() == 0
    assert "Bye." in capsys.readouterr().out


def test_ctrl_c_ends_the_session(monkeypatch, capsys):
    def interrupt(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupt)
    assert main() == 0
    assert "Bye." in capsys.readouterr().out


def test_invalid_setting_stops_startup(monkeypatch, capsys):
    monkeypatch.setenv("TUTOR_READ_TIMEOUT", "abc")
    assert main() == 1
    assert "TUTOR_READ_TIMEOUT" in capsys.readouterr().out
