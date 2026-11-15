"""Шаблоны сообщений для веб-консоли.

Простое JSON-хранилище рядом с базой: одно пользовательское место, без миграций
схемы. Каждая запись — {id, title, text, created, updated}.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from threading import Lock

MAX_TEMPLATES = 200
MAX_TEXT = 8000
MAX_TITLE = 120


class TemplateStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = Lock()

    # ------------------------------------------------------------------ disk
    def _read(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
            if isinstance(data, dict) and isinstance(data.get("templates"), list):
                return [x for x in data["templates"] if isinstance(x, dict)]
        except Exception:  # noqa: BLE001
            pass
        return []

    def _write(self, items: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    @staticmethod
    def _clean_title(value: str) -> str:
        return " ".join(str(value or "").replace("\n", " ").split())[:MAX_TITLE]

    # ------------------------------------------------------------------- api
    def list(self) -> list[dict]:
        with self._lock:
            return self._read()

    def add(self, title: str, text: str) -> dict:
        body = str(text or "").strip()[:MAX_TEXT]
        if not body:
            raise ValueError("текст шаблона пустой")
        now = time.time()
        item = {
            "id": uuid.uuid4().hex[:10],
            "title": self._clean_title(title) or body.replace("\n", " ")[:48],
            "text": body,
            "created": now,
            "updated": now,
        }
        with self._lock:
            items = self._read()
            items.insert(0, item)
            self._write(items[:MAX_TEMPLATES])
        return item

    def update(self, tid: str, title: str | None, text: str | None) -> dict | None:
        with self._lock:
            items = self._read()
            for item in items:
                if item.get("id") != tid:
                    continue
                if text is not None:
                    body = str(text).strip()[:MAX_TEXT]
                    if not body:
                        raise ValueError("текст шаблона пустой")
                    item["text"] = body
                if title is not None:
                    item["title"] = self._clean_title(title) or (item.get("title") or "")
                item["updated"] = time.time()
                self._write(items)
                return item
        return None

    def delete(self, tid: str) -> bool:
        with self._lock:
            items = self._read()
            left = [x for x in items if x.get("id") != tid]
            if len(left) == len(items):
                return False
            self._write(left)
            return True
