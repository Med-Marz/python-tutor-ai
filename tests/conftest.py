import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging.handlers import RotatingFileHandler

import pytest

GOOD_BODY = json.dumps(
    {
        "message": {"role": "assistant", "content": "A tuple is immutable."},
        "done": True,
        "eval_count": 60,
        "eval_duration": 10_000_000_000,
    }
).encode()


class FakeOllama:
    def __init__(self):
        self.status = 200
        self.body = GOOD_BODY
        self.delay = 0
        self.last_request = None


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        fake = self.server.fake
        length = int(self.headers.get("Content-Length", 0))
        fake.last_request = json.loads(self.rfile.read(length))
        time.sleep(fake.delay)
        try:
            self.send_response(fake.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(fake.body)))
            self.end_headers()
            self.wfile.write(fake.body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch, tmp_path):
    for name in (
        "TUTOR_OLLAMA_URL",
        "TUTOR_MODEL",
        "TUTOR_CONNECT_TIMEOUT",
        "TUTOR_READ_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TUTOR_LOG_FILE", str(tmp_path / "test.log"))
    yield
    logger = logging.getLogger("tutor_ai")
    for handler in list(logger.handlers):
        if isinstance(handler, RotatingFileHandler):
            logger.removeHandler(handler)
            handler.close()


@pytest.fixture
def fake_ollama(monkeypatch):
    fake = FakeOllama()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    server.fake = fake
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("TUTOR_OLLAMA_URL", f"http://127.0.0.1:{server.server_port}")
    yield fake
    server.shutdown()
    server.server_close()
