# path: text-cleaner-api/test_api.py
import requests

BASE = "http://localhost:8000"


def test_health():
    r = requests.get(f"{BASE}/health")
    print("health:", r.status_code, r.json())


def test_clean_basic():
    payload = {
        "text": "<h1>Hello 👋</h1> Visit https://example.com now!!! *Bold* __text__ 123",
        "case": "lower",
        "remove_html": True,
        "decode_html_entities": True,
        "strip_markdown": True,
        "remove_urls": True,
        "remove_emojis": True,
        "remove_punctuation": False,
        "remove_numbers": False,
        "normalize_whitespace": True,
        "remove_non_ascii": False,
        "max_length": None,
        "return_tokens": True,
        "detect_language": True,
    }
    r = requests.post(f"{BASE}/clean", json=payload)
    print("clean_basic:", r.status_code)
    print(r.json())


def test_clean_get():
    params = {
        "text": "<p>Привет мир!!! 👋</p> Заходи на https://example.com!!!",
        "case": "lower",
        "remove_html": True,
        "decode_html_entities": True,
        "strip_markdown_flag": True,
        "remove_urls": True,
        "remove_emojis": True,
        "remove_punctuation": True,
        "remove_numbers": True,
        "normalize_whitespace_flag": True,
        "remove_non_ascii": False,
        "max_length": 100,
        "return_tokens": True,
        "detect_language": True,
    }
    r = requests.get(f"{BASE}/clean", params=params)
    print("clean_get:", r.status_code)
    print(r.json())


if __name__ == "__main__":
    test_health()
    test_clean_basic()
    test_clean_get()
