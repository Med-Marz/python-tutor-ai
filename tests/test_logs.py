import logging

from tutor_ai.logs import setup_logging


def test_lines_are_written_to_the_file(tmp_path):
    log_file = tmp_path / "nested" / "app.log"
    setup_logging(str(log_file))
    logging.getLogger("tutor_ai.demo").info("hello log")
    text = log_file.read_text(encoding="utf-8")
    assert "hello log" in text
    assert "INFO" in text
    assert "tutor_ai.demo" in text


def test_calling_setup_twice_does_not_duplicate_lines(tmp_path):
    log_file = tmp_path / "app.log"
    setup_logging(str(log_file))
    setup_logging(str(log_file))
    logging.getLogger("tutor_ai.demo").info("only once")
    assert log_file.read_text(encoding="utf-8").count("only once") == 1
