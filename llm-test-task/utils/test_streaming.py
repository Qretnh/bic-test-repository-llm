import json

import requests

# Файл для теста стриминга. запускать при запущенном бэкенде


def test_stream_debug():
    url = "http://127.0.0.1:8000/generate?stream=true"
    payload = {
        "prompt": "Дай пошаговое решение 1+1, стримом",
        "model": "moonshotai/kimi-k2:free",
        "max_tokens": 150,
    }

    print("Testing stream endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")

    try:
        response = requests.post(url, json=payload, stream=True, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code != 200:
            print(f"Error: {response.text}")
            return

        print("Stream started. Reading lines...")

        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                print(f"RAW: {line_str}")

                if line_str.startswith("data: "):
                    data = line_str[6:].strip()
                    if data == "[DONE]":
                        print("Stream completed")
                        break
                    try:
                        json_data = json.loads(data)
                        print(f"JSON: {json_data}")
                        if "content" in json_data:
                            print(f"CONTENT: {json_data['content']}")
                    except json.JSONDecodeError:
                        print(f"INVALID JSON: {data}")

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    test_stream_debug()
