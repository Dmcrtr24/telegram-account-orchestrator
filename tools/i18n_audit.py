#!/usr/bin/env python3
"""Аудит локализации: какие китайские строки исходников НЕ покрыты словарём.

Читает tam/web/i18n.data.js (собранный словарь) и проверяет каждую китайскую
строку из app.js / index.src.html так же, как это делает рантайм:
точное совпадение -> шаблон с %s (длинные первыми) -> ничего.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "tam" / "web"
CJK = re.compile(r"[\u4e00-\u9fff]")


def load_dict() -> tuple[dict, list]:
    s = (WEB / "i18n.data.js").read_text(encoding="utf-8")
    payload = json.loads(s[s.index("{"):s.rindex("}") + 1])
    exact = payload["ru"]
    pats = payload["pat"]["ru"]
    compiled = []
    for src, dst in sorted(pats, key=lambda p: -len(p[0])):
        rx = "^" + "(.+?)".join(re.escape(chunk) for chunk in src.split("%s")) + "$"
        compiled.append((re.compile(rx, re.S), dst))
    return exact, compiled


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def covered(s: str, exact: dict, pats: list) -> bool:
    s = norm(s)
    if not s:
        return True
    if s in exact or norm(s) in exact:
        return True
    return any(rx.match(s) for rx, _ in pats)


def scan_js(src: str):
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if c in "'\"`":
            q, i = c, i + 1
            buf = []
            while i < n:
                if src[i] == "\\":
                    buf.append(src[i:i + 2]); i += 2; continue
                if src[i] == q:
                    break
                buf.append(src[i]); i += 1
            yield "".join(buf)
            i += 1
            continue
        i += 1


def main() -> int:
    exact, pats = load_dict()
    missing: dict[str, int] = {}

    CODE = re.compile(r"(=>|\bfunction\b|\bconst\b|\breturn\b|\bawait\b|document\.|querySelector|\bvar\b|===|\.length|\{\$|\}\s*$|^[)\]}])")

    def add(s: str):
        s = norm(s)
        if not s or not CJK.search(s) or len(s) > 200:
            return
        if CODE.search(s):
            return
        # доля китайских символов: отсекаем обрывки кода с парой иероглифов
        if len(CJK.findall(s)) / max(len(s), 1) < 0.3:
            return
        if covered(s, exact, pats):
            return
        missing[s] = missing.get(s, 0) + 1

    js = (WEB / "app.js").read_text(encoding="utf-8")
    for lit in scan_js(js):
        lit = re.sub(r"\$\{[^}]*\}", "%s", lit)
        if "<" in lit and ">" in lit:
            # HTML-шаблон: проверяем только текстовые куски между тегами
            for seg in re.split(r"<[^>]*>", lit):
                add(seg)
            for m in re.finditer(r'(?:placeholder|title|alt|aria-label|value)="([^"]*)"', lit):
                add(m.group(1))
        else:
            add(lit)

    html = (WEB / "index.src.html").read_text(encoding="utf-8")
    for m in re.finditer(r">([^<>]+)<", html):
        add(m.group(1))
    for m in re.finditer(r'(?:placeholder|title|alt|aria-label|value)="([^"]*)"', html):
        add(m.group(1))

    out = sorted(missing, key=lambda s: (-missing[s], s))
    dest = ROOT / "tools" / "i18n_missing.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"не покрыто: {len(out)} -> {dest.relative_to(ROOT)}")
    for s in out[:40]:
        print("  ", s[:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
