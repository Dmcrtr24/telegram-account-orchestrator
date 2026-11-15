"""Машинный перевод строк интерфейса (zh -> ru/en) через бесплатные сервисы.

Зачем: словарь `tam/web/i18n.data.js` собирается из исходников, но часть строк
появляется только в рантайме (склейки, тексты из бэкенда, новые правки). Такие
строки уходят сюда: результат кладётся в `data/i18n_cache.json`, поэтому каждая
строка переводится один раз и дальше берётся с диска.

Провайдеры бесплатные и без ключей: MyMemory (основной), Google gtx (если доступен).
Ошибки/лимиты не считаются фатальными — возвращаем то, что удалось получить.
"""
from __future__ import annotations

import html
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Iterable

DEFAULT_CACHE = Path(__file__).resolve().parent.parent / "data" / "i18n_cache.json"
LANGS = ("ru", "en")
MAX_CHARS_ONCE = 500          # больше MyMemory за один запрос не любит
MIN_INTERVAL = 0.12           # общая пауза между запросами (3 потока ~ 8-10 rps)

_LOCK = Lock()
_last_call = 0.0
_quota_hit: set[str] = set()


def _load(cache_path: Path) -> dict[str, dict[str, str]]:
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {lang: dict(data.get(lang) or {}) for lang in LANGS}
    except Exception:  # noqa: BLE001
        pass
    return {lang: {} for lang in LANGS}


def _save(cache_path: Path, cache: dict[str, dict[str, str]]) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, cache_path)
    except Exception:  # noqa: BLE001
        pass


def _get_json(url: str, timeout: float) -> dict | None:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) TAO-i18n/1.0",
        "Accept": "application/json,text/plain,*/*",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


def _from_mymemory(text: str, target: str, timeout: float) -> str | None:
    url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode({
        "q": text,
        "langpair": "zh-CN|" + target,
    })
    data = _get_json(url, timeout)
    if not data:
        return None
    status = data.get("responseStatus")
    out = (data.get("responseData") or {}).get("translatedText")
    out = html.unescape(str(out or "")).strip()
    if "MYMEMORY WARNING" in out.upper() or "ALL AVAILABLE FREE TRANSLATIONS" in out.upper():
        _quota_hit.add("mymemory")
        return None
    if status not in (200, "200") or not out:
        return None
    return out


def _from_gtx(text: str, target: str, timeout: float) -> str | None:
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode({
        "client": "gtx", "sl": "zh-CN", "tl": target, "dt": "t", "q": text,
    })
    data = _get_json(url, timeout)
    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        return None
    parts = [seg[0] for seg in data[0] if isinstance(seg, list) and seg and seg[0]]
    out = html.unescape("".join(parts)).strip()
    return out or None


PROVIDERS = (_from_mymemory, _from_gtx)


def translate_one(text: str, target: str, timeout: float = 8.0) -> str | None:
    """Перевод одной строки. None — провайдеры не ответили (сеть/лимит)."""
    global _last_call
    text = (text or "").strip()
    if not text or target not in LANGS:
        return None
    if text.isascii():
        return None
    for provider in PROVIDERS:
        if provider.__name__ == "_from_mymemory" and "mymemory" in _quota_hit:
            continue
        wait = MIN_INTERVAL - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        out = provider(text, target, timeout)
        if out and out != text:
            return out
    return None


def translate_many(texts: Iterable[str], target: str, *,
                   cache_path: Path | str | None = None,
                   timeout: float = 8.0,
                   limit: int | None = None) -> dict[str, str]:
    """Перевод пачки строк с кэшем на диске. Возвращает {исходник: перевод}.

    Строки переводятся в 3 потока: провайдеры медленные (~1 c на строку), а
    очередь с фронтенда может быть в десятки строк. Дубли между потоками
    исключаются порядком `dict.fromkeys`.
    """
    if target not in LANGS:
        return {}
    path = Path(cache_path) if cache_path else DEFAULT_CACHE
    with _LOCK:
        cache = _load(path)
        bag = cache.setdefault(target, {})
        out: dict[str, str] = {}
        todo: list[str] = []
        for raw in texts:
            text = (raw or "").strip()
            if not text or len(text) > MAX_CHARS_ONCE or text.isascii():
                continue
            hit = bag.get(text)
            if hit:
                out[text] = hit
                continue
            if text not in todo:
                todo.append(text)
        if limit is not None:
            todo = todo[: max(0, int(limit))]
        if todo:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=3) as pool:
                results = list(pool.map(lambda s: (s, translate_one(s, target, timeout)), todo))
            for text, got in results:
                if got:
                    bag[text] = got
                    out[text] = got
            _save(path, cache)
        return out
