import httpx

URL = "http://127.0.0.1:11434/api/chat"

payload = {
    "model": "llama3.2:3b",
    "messages": [
        {"role": "system", "content": "You are a Python tutor. Answer in at most 3 short sentences."},
        {"role": "user", "content": "What is a tuple?"},
    ],
    "stream": False,
    "options": {"temperature": 0, "num_predict": 100},
}


def main():
    response = httpx.post(URL, json=payload, timeout=120)
    data = response.json()
    print(data["message"]["content"])


if __name__ == "__main__":
    main()