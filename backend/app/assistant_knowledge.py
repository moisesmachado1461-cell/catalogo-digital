from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

_KNOWLEDGE_PATH = Path(__file__).with_name("assistant_knowledge.json")
_LOCK = Lock()
_CACHE_MTIME_NS: int | None = None
_CACHE: dict[str, Any] | None = None

_STOP_WORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na",
    "nos", "nas", "para", "por", "com", "como", "que", "um", "uma", "eu", "me", "meu",
    "minha", "seu", "sua", "isso", "isto", "essa", "esse", "ao", "aos",
}


@dataclass(frozen=True)
class KnowledgeMatch:
    item: dict[str, Any]
    score: int


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value or "")
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", without_marks).lower()
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokens(value: str) -> list[str]:
    return [token for token in _normalize(value).split() if len(token) > 1 and token not in _STOP_WORDS]


def load_knowledge() -> dict[str, Any]:
    """Carrega a base oficial e recarrega automaticamente quando o arquivo mudar."""
    global _CACHE, _CACHE_MTIME_NS

    try:
        mtime_ns = _KNOWLEDGE_PATH.stat().st_mtime_ns
    except OSError as exc:
        raise RuntimeError("assistant_knowledge_missing") from exc

    if _CACHE is not None and _CACHE_MTIME_NS == mtime_ns:
        return _CACHE

    with _LOCK:
        if _CACHE is not None and _CACHE_MTIME_NS == mtime_ns:
            return _CACHE
        try:
            data = json.loads(_KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("assistant_knowledge_invalid") from exc

        if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
            raise RuntimeError("assistant_knowledge_invalid")

        _CACHE = data
        _CACHE_MTIME_NS = mtime_ns
        return data


def knowledge_metadata() -> dict[str, Any]:
    data = load_knowledge()
    return {
        "version": str(data.get("version") or "unknown"),
        "entries": len(data.get("entries") or []),
    }


def rank_knowledge(question: str, area: str, section: str) -> list[KnowledgeMatch]:
    data = load_knowledge()
    normalized_query = _normalize(question)
    query_tokens = _tokens(question)
    ranked: list[KnowledgeMatch] = []

    for item in data.get("entries", []):
        if not isinstance(item, dict):
            continue
        areas = item.get("areas") or []
        sections = item.get("sections") or []
        keywords = item.get("keywords") or []
        steps = item.get("steps") or []
        title = str(item.get("title") or "")
        answer = str(item.get("answer") or "")
        searchable = _normalize(" ".join([title, answer, *map(str, keywords), *map(str, steps)]))

        score = 0
        if area in areas:
            score += 5
        if section in sections:
            score += 7
        if "home" in sections:
            score += 1
        for keyword in keywords:
            key = _normalize(str(keyword))
            if key and key in normalized_query:
                score += 8 if " " in key else 5
        for token in query_tokens:
            if token in searchable:
                score += 2
        if _normalize(title) == normalized_query:
            score += 10

        if score > 0:
            ranked.append(KnowledgeMatch(item=item, score=score))

    ranked.sort(key=lambda match: match.score, reverse=True)
    return ranked


def relevant_knowledge(question: str, area: str, section: str, limit: int = 6) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        item_id = str(item.get("id") or item.get("title") or "")
        if not item_id or item_id in seen:
            return
        seen.add(item_id)
        selected.append(item)

    for match in rank_knowledge(question, area, section):
        if match.score < 3:
            continue
        add(match.item)
        if len(selected) >= limit:
            break

    if len(selected) < limit:
        data = load_knowledge()
        for item in data.get("entries", []):
            if not isinstance(item, dict):
                continue
            areas = item.get("areas") or []
            sections = item.get("sections") or []
            if area in areas and section in sections:
                add(item)
            if len(selected) >= limit:
                break

    return selected[:limit]
