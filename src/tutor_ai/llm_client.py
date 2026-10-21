import httpx

URL = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.2:3b"
SYSTEM_PROMPT = "You are a Python tutor. Answer in at most 3 short sentences."


def ask(question: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 100},
    }
    response = httpx.post(URL, json=payload, timeout=120)
    data = response.json()
    return data["message"]["content"]


def main():
    print(ask("What is a tuple?"))


if __name__ == "__main__":
    main()