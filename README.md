# Python Tutor AI

![CI](https://github.com/Med-Marz/python-tutor-ai/actions/workflows/ci.yml/badge.svg)

A small terminal app that answers beginner Python questions and explains error
messages, using a language model that runs on your own computer through
[Ollama](https://ollama.com). No paid API and no account: your questions stay on your machine.

This is a learning project. **The answers can be wrong**, so check them (see
[Limitations](#limitations)).

## Example

```
$ tutor-ai
Python Tutor AI (llama3.2:3b).
Type your question, or 'exit' to quit.
> What is a dictionary?
Thinking...
A dictionary is a data structure in Python that stores a collection of key-value pairs. You can think of it like a phonebook, where each name (key) is associated with a phone number (value). Dictionaries are mutable, meaning you can add or change values later.
(11.8 s)
> exit
Bye.
```

## Requirements

- Linux (developed and tested on Ubuntu 24.04)
- Python 3.10 or newer (tested with 3.12)
- [Ollama](https://ollama.com), running locally
- The model `llama3.2:3b` (a 2.0 GB download)

## Setup

1. Install Ollama by following the instructions on https://ollama.com, then check that it runs:

   ```
   ollama --version
   systemctl status ollama
   ```

2. Download the model:

   ```
   ollama pull llama3.2:3b
   ```

3. Get the code and install it in a virtual environment:

   ```
   git clone https://github.com/Med-Marz/python-tutor-ai.git
   cd python-tutor-ai
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

   (`pip install -e .` is enough if you only want to run the app and not the tests.)

## Usage

```
tutor-ai
```

`python -m tutor_ai` does the same. Type a question and press Enter. To quit, type
`exit`, or press Ctrl+D or Ctrl+C.

Good questions are short and specific: a concept ("What is a list comprehension?") or an error
message ("Explain this error: TypeError: 'int' object is not subscriptable"). Empty questions
and questions longer than 2000 characters are rejected before the model is called.

## Settings

Settings are environment variables. They are all optional.

| Variable | Default | Meaning |
|---|---|---|
| `TUTOR_MODEL` | `llama3.2:3b` | model used for answers |
| `TUTOR_OLLAMA_URL` | `http://127.0.0.1:11434` | where Ollama listens |
| `TUTOR_CONNECT_TIMEOUT` | `3` | seconds to wait to reach Ollama |
| `TUTOR_READ_TIMEOUT` | `120` | seconds to wait for an answer |
| `TUTOR_LOG_FILE` | `~/.local/state/tutor-ai/tutor-ai.log` | where the log is written |

Set one for a single run like this:

```
TUTOR_READ_TIMEOUT=300 tutor-ai
```

An invalid value (for example `TUTOR_READ_TIMEOUT=abc`) stops the app at startup with a
clear message and exit code 1.

## Log

Each request adds one line to the log file, with the model, total time, number of generated
tokens, tokens per second, and the length of the question. Failed requests are logged with
the error type. **The text of your questions is never logged.** The file rotates at about
1 MB and keeps 3 old copies. If the log file cannot be written, the app prints a warning
and keeps working.

```
2026-10-28 22:14:16,578 INFO tutor_ai.llm_client request ok model=llama3.2:3b seconds=6.98 eval_count=35 eval_seconds=5.54 tokens_per_s=6.31 question_chars=19
```

## Development

Before pushing, run the same three checks as the CI:

```
ruff check .
ruff format --check .
pytest
```

The tests never call the real model. They run against a small fake Ollama server, so they
are fast and work without Ollama installed. GitHub Actions runs the same checks on every pull
request, and `main` only accepts changes through a pull request with a green check.

```
src/tutor_ai/
  main.py        the interactive loop
  tutor.py       the system prompt and input validation
  llm_client.py  talks to Ollama; timing, errors and request logging
  config.py      settings from environment variables
  logs.py        log file setup
tests/           pytest tests with a fake Ollama server
```

## Model choice and speed

Measured on an Intel i5-1235U with 23 GiB RAM and no GPU (CPU only), with Ollama 0.40.6:

| Model | Speed | Typical answer time |
|---|---|---|
| `llama3.2:3b` (2.0 GB) | about 6 tokens/s (5.6 to 8.5 across runs) | 7 to 21 s with this app's short answers |
| `gemma3:4b` | about 3 tokens/s | 4 to 7 minutes for long, unlimited answers |

`llama3.2:3b` is the default because `gemma3:4b` was too slow on this hardware. The first
question after a pause can take noticeably longer than the following ones. Speed varies from
run to run, so treat these numbers as rough.

## Limitations

- **Answers can be wrong.** In testing, the model gave a correct explanation of
  `TypeError: 'int' object is not subscriptable` but suggested a wrong fix. Do not rely on
  it for security-sensitive, production or assessment-related code.
- **Each question is independent.** The tutor does not remember earlier questions, so a
  follow-up such as "Isn't it a library?" loses its context.
- **Short answers by design.** The prompt asks for at most 3 short sentences, and generation is
  capped at 100 tokens, so a long answer can end abruptly.
- **No streaming.** You see the answer only when it is complete.
- Only `llama3.2:3b` has been tested in the app itself.

## Troubleshooting

| Message | What to do |
|---|---|
| `Cannot reach Ollama. Is it running?` | Check `systemctl status ollama`, and start it with `sudo systemctl start ollama`. If Ollama is on another address, set `TUTOR_OLLAMA_URL`. |
| `Cannot reach Ollama: the connection timed out.` | The address is probably wrong or unreachable. Check `TUTOR_OLLAMA_URL`. |
| `Model '...' not found. Try: ollama pull ...` | Run the `ollama pull` command shown, or set `TUTOR_MODEL` to a model you have (`ollama list`). |
| `The model took too long to answer.` | Raise `TUTOR_READ_TIMEOUT`, or ask a shorter question. A slow CPU can need a minute or more. |
| `Ollama returned HTTP ...` | Check the Ollama service logs with `journalctl -u ollama`. |
| `Ollama sent an unexpected response.` or `The model returned an empty answer.` | Ask again. If it keeps happening, check the Ollama version and logs. |
| `Please type a question.` or `The question is too long ...` | Type a non-empty question of at most 2000 characters. |
| `Warning: cannot write the log file ...` | The app still works. Set `TUTOR_LOG_FILE` to a path you can write to. |
