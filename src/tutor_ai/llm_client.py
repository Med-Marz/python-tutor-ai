import time
from dataclasses import dataclass

import httpx

URL = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.2:3b"
SYSTEM_PROMPT = "You are a Python tutor. Answer in at most 3 short sentences."


@dataclass
class Reply:
    text: str
    seconds: float
    eval_count: int
    eval_seconds: float


def ask(question: str) -> Reply:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 100},
    }
    start = time.perf_counter()
    response = httpx.post(URL, json=payload, timeout=120)
    seconds = time.perf_counter() - start
    data = response.json()
    return Reply(
        text=data["message"]["content"],
        seconds=seconds,
        eval_count=data["eval_count"],
        eval_seconds=data["eval_duration"] / 1_000_000_000,
    )


def main():
    reply = ask("What is a tuple?")
    print(reply.text)
    print(f"({reply.seconds:.1f} s total, {reply.eval_count} tokens in {reply.eval_seconds:.1f} s)")


if __name__ == "__main__":
    main()