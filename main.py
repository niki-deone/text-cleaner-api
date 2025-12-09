# path: text-cleaner-api/main.py
from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
import re
import html

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

app = FastAPI(
    title="Advanced Text Cleaner API",
    version="1.2.0",
    description="Clean, normalize and preprocess text for NLP, SEO and data pipelines."
)


class CleanRequest(BaseModel):
    text: str

    # casing
    case: Literal["lower", "upper", "title", "none"] = "lower"

    # cleaning flags (по умолчанию делаем более агрессивную чистку)
    remove_html: bool = True
    decode_html_entities: bool = True
    strip_markdown: bool = True
    remove_urls: bool = True
    remove_emojis: bool = True
    remove_punctuation: bool = True      # было False
    remove_numbers: bool = True          # было False
    normalize_whitespace: bool = True
    remove_non_ascii: bool = False

    # extra features
    max_length: Optional[int] = None
    return_tokens: bool = False
    detect_language: bool = False


# --------------- regex helpers ---------------

URL_REGEX = re.compile(r"(https?://\S+|www\.\S+)", flags=re.IGNORECASE)
PUNCTUATION_REGEX = re.compile(r"[^\w\s]", flags=re.UNICODE)
NUMBER_REGEX = re.compile(r"\d+", flags=re.UNICODE)

EMOJI_PATTERN = re.compile(
    r"["
    r"\U0001F300-\U0001F5FF"
    r"\U0001F600-\U0001F64F"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002702-\U000027B0"
    r"\U000024C2-\U0001F251"
    r"]+",
    flags=re.UNICODE,
)


# --------------- pure functions ---------------

def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def decode_entities(text: str) -> str:
    return html.unescape(text)


def strip_urls(text: str) -> str:
    return URL_REGEX.sub(" ", text)


def strip_emojis(text: str) -> str:
    return EMOJI_PATTERN.sub("", text)


def strip_punctuation(text: str) -> str:
    return PUNCTUATION_REGEX.sub(" ", text)


def strip_numbers(text: str) -> str:
    return NUMBER_REGEX.sub(" ", text)


def strip_markdown(text: str) -> str:
    # [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    # **text**, *text*, __text__, _text_
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    # заголовки #, ## ...
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # списки -, *, +
    text = re.sub(r"^[\-\*\+]\s+", "", text, flags=re.MULTILINE)
    # разделители --- / ***
    text = re.sub(r"^[-*_]{3,}\s*$", " ", text, flags=re.MULTILINE)
    return text


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def remove_non_ascii_chars(text: str) -> str:
    return "".join(ch for ch in text if ord(ch) < 128)


def apply_case(text: str, case: str) -> str:
    if case == "lower":
        return text.lower()
    if case == "upper":
        return text.upper()
    if case == "title":
        return text.title()
    return text


def tokenize(text: str):
    return [t for t in text.split(" ") if t]


def try_detect_language(text: str) -> Dict[str, Any]:
    if not LANGDETECT_AVAILABLE:
        return {"enabled": False, "language": None, "error": "langdetect not installed"}

    cut = text[:2000]
    try:
        if not cut or cut.isspace():
            return {"enabled": True, "language": None, "error": "text too short"}
        lang = detect(cut)
        return {"enabled": True, "language": lang, "error": None}
    except LangDetectException as e:
        return {"enabled": True, "language": None, "error": str(e)}


# --------------- FastAPI endpoints ---------------

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.2.0"}


@app.post("/clean")
def clean_post(body: CleanRequest = Body(...)):
    return _clean_logic(body)


@app.get("/clean")
def clean_get(
    text: str = Query(..., min_length=1),
    case: Literal["lower", "upper", "title", "none"] = "lower",
    remove_html: bool = True,
    decode_html_entities: bool = True,
    strip_markdown_flag: bool = True,
    remove_urls: bool = True,
    remove_emojis: bool = True,
    remove_punctuation: bool = True,
    remove_numbers: bool = True,
    normalize_whitespace_flag: bool = True,
    remove_non_ascii: bool = False,
    max_length: Optional[int] = None,
    return_tokens: bool = False,
    detect_language: bool = False,
):
    req = CleanRequest(
        text=text,
        case=case,
        remove_html=remove_html,
        decode_html_entities=decode_html_entities,
        strip_markdown=strip_markdown_flag,
        remove_urls=remove_urls,
        remove_emojis=remove_emojis,
        remove_punctuation=remove_punctuation,
        remove_numbers=remove_numbers,
        normalize_whitespace=normalize_whitespace_flag,
        remove_non_ascii=remove_non_ascii,
        max_length=max_length,
        return_tokens=return_tokens,
        detect_language=detect_language,
    )
    return _clean_logic(req)


def _clean_logic(body: CleanRequest):
    original_text = body.text

    if len(original_text) > 50000:
        raise HTTPException(
            status_code=413,
            detail="Text is too long. Max 50000 characters allowed.",
        )

    text = original_text

    if body.decode_html_entities:
        text = decode_entities(text)

    if body.remove_html:
        text = strip_html(text)

    if body.strip_markdown:
        text = strip_markdown(text)

    if body.remove_urls:
        text = strip_urls(text)

    if body.remove_emojis:
        text = strip_emojis(text)

    if body.remove_punctuation:
        text = strip_punctuation(text)

    if body.remove_numbers:
        text = strip_numbers(text)

    if body.remove_non_ascii:
        text = remove_non_ascii_chars(text)

    # убираем подчёркивания, чтобы не было "ограниченное_предложение"
    text = text.replace("_", " ")

    if body.normalize_whitespace:
        text = normalize_whitespace(text)

    text = apply_case(text, body.case)

    if body.max_length is not None and body.max_length > 0:
        text = text[: body.max_length]

    tokens = tokenize(text) if body.return_tokens else None
    lang_info = try_detect_language(text) if body.detect_language else None

    response: Dict[str, Any] = {
        "ok": True,
        "original_length": len(original_text),
        "clean_length": len(text),
        "clean_text": text,
        "params": {
            "case": body.case,
            "remove_html": body.remove_html,
            "decode_html_entities": body.decode_html_entities,
            "strip_markdown": body.strip_markdown,
            "remove_urls": body.remove_urls,
            "remove_emojis": body.remove_emojis,
            "remove_punctuation": body.remove_punctuation,
            "remove_numbers": body.remove_numbers,
            "normalize_whitespace": body.normalize_whitespace,
            "remove_non_ascii": body.remove_non_ascii,
            "max_length": body.max_length,
            "return_tokens": body.return_tokens,
            "detect_language": body.detect_language,
        },
    }

    if tokens is not None:
        response["tokens"] = tokens

    if lang_info is not None:
        response["language"] = lang_info

    return response
