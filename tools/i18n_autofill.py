#!/usr/bin/env python3
"""Дозаполняет tools/i18n_extra.json машинным переводом недостающих строк.

Что делает: берёт строки из tools/i18n_src.json, отбрасывает разметку и код,
проверяет, есть ли строка в собранном словаре, и для отсутствующих просит
перевод у бесплатных сервисов (tam/i18n_remote.py, кэш data/i18n_cache.json).
Результат — только новые ключи; существующие переводы не перезаписываются.

Запуск: .venv/bin/python tools/i18n_autofill.py [--limit N] [--lang ru|en]
Дальше: python3 tools/i18n_build.py && cd tam/web && python3 build.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tam import i18n_remote  # noqa: E402

SRC = ROOT / "tools" / "i18n_src.json"
EXTRA = ROOT / "tools" / "i18n_extra.json"
DATA = ROOT / "tam" / "web" / "i18n.data.js"
CACHE = ROOT / "data" / "i18n_cache.json"
CJK = re.compile(r"[\u4e00-\u9fff]")
MARKUP = re.compile(r"[<>{}]|=>|data-on|\bclass=\"|\bdef\b|\breturn\b|\bimport\b", re.IGNORECASE)


def missing_strings(limit_markup: bool = True) -> list[str]:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    dict_text = DATA.read_text(encoding="utf-8") if DATA.exists() else ""
    seen: set[str] = set()
    out: list[str] = []
    for kind in ("frontend", "patterns", "backend"):
        for raw in src.get(kind, []):
            s = (raw or "").strip()
            if not s or s in seen or len(s) > 300:
                continue
            if not CJK.search(s):
                continue
            if limit_markup and MARKUP.search(s):
                continue
            seen.add(s)
            if json.dumps(s, ensure_ascii=False) in dict_text:
                continue
            out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="сколько строк переводить за прогон (по умолчанию все)")
    ap.add_argument("--lang", choices=["ru", "en", "both"], default="both")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    todo = missing_strings()
    print(f"строк без перевода: {len(todo)}")
    if not todo or args.dry_run:
        for s in todo[:40]:
            print("  ·", s[:120])
        return 0

    langs = ["ru", "en"] if args.lang == "both" else [args.lang]
    extra = json.loads(EXTRA.read_text(encoding="utf-8"))
    added = 0

    # 1) то, что уже выучил рантайм (data/i18n_cache.json) — бесплатно, без сети
    if CACHE.exists():
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        for lang in langs:
            for zh, val in (cached.get(lang) or {}).items():
                if not zh or not val:
                    continue
                slot = extra.setdefault(zh, {})
                if not slot.get(lang):
                    slot[lang] = val
                    added += 1

    # 2) остальное спрашиваем у провайдеров
    for lang in langs:
        got = i18n_remote.translate_many(todo, lang, limit=args.limit)
        print(f"{lang}: переведено {len(got)}")
        for zh, val in got.items():
            slot = extra.setdefault(zh, {})
            if not slot.get(lang):
                slot[lang] = val
                added += 1
    if added and not args.dry_run:
        EXTRA.write_text(json.dumps(extra, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"добавлено переводов: {added}; дальше: tools/i18n_build.py + build.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
