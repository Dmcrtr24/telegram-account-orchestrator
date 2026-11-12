#!/usr/bin/env python3
"""Extract translatable CJK strings from the web frontend + UI-facing backend specs.

Output: tools/i18n_src.json  {frontend:[...], patterns:[...], backend:[...]}
Exact keys are the literal text itself; patterns are templates with ${...} -> %s.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "tam" / "web"
CJK = re.compile(r"[\u4e00-\u9fff]")

# backend modules whose strings surface in the web UI (specs, descriptions, errors)
BACKEND_FILES = [
    "tam/api.py", "tam/toolbox.py", "tam/tools.py", "tam/manager.py",
    "tam/config.py", "tam/settings_spec.py", "tam/ai_panel.py", "tam/doctor.py",
    "tam/tdata_native.py", "tam/tasks.py", "tam/leads.py", "tam/autokick.py",
    "tam/codefetch.py", "tam/warmup.py", "tam/healthcheck.py",
]
CODEY = re.compile(r"(?:=>|\bdef\b|\breturn\b|\bimport\b|\bself\b|==|\{\}|\[\]|;\s*$|^\s*#)")


def scan_js(src: str):
    i, n, line = 0, len(src), 1
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                if src[i] == "\n":
                    line += 1
                i += 1
            i += 2; continue
        if c in "'\"":
            q = c; i += 1; buf = []
            while i < n:
                ch = src[i]
                if ch == "\\":
                    buf.append(src[i:i + 2]); i += 2; continue
                if ch == q or ch == "\n":
                    break
                buf.append(ch); i += 1
            yield ("str", "".join(buf), line); i += 1; continue
        if c == "`":
            i += 1; buf = []
            while i < n:
                ch = src[i]
                if ch == "\\":
                    buf.append(src[i:i + 2]); i += 2; continue
                if ch == "`":
                    break
                buf.append(ch); i += 1
            yield ("tpl", "".join(buf), line); i += 1; continue
        i += 1


def tpl_to_pattern(t: str) -> str:
    return re.sub(r"\$\{[^}]*\}", "%s", t)


def clean(s: str) -> str:
    s = s.replace("\\n", " ").replace("\\t", " ").replace('\\"', '"').replace("\\'", "'")
    return re.sub(r"\s+", " ", s).strip()


def plausible(s: str) -> bool:
    if not s or not CJK.search(s):
        return False
    if len(s) > 300 or CODEY.search(s):
        return False
    return True


def main() -> int:
    frontend, patterns = set(), set()

    js = (WEB / "app.js").read_text(encoding="utf-8")
    for kind, raw, line in scan_js(js):
        s = clean(raw)
        if not plausible(s):
            continue
        if kind == "tpl" and "${" in raw:
            pat = clean(tpl_to_pattern(raw))
            if plausible(pat) and len(pat) <= 300:
                patterns.add(pat)
        elif "${" not in s:
            frontend.add(s)

    html = (WEB / "index.src.html").read_text(encoding="utf-8")
    for m in re.finditer(r">([^<>]+)<", html):
        s = clean(m.group(1))
        if plausible(s):
            frontend.add(s)
    for m in re.finditer(r'(?:placeholder|title|alt|aria-label|value)="([^"]*)"', html):
        s = clean(m.group(1))
        if plausible(s):
            frontend.add(s)

    backend = set()
    for rel in BACKEND_FILES:
        p = ROOT / rel
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        for kind, raw, line in scan_js(src):
            s = clean(raw)
            if plausible(s) and len(s) <= 220:
                backend.add(s)

    # strings already covered by the frontend set need no separate backend entry
    backend -= frontend
    out = {
        "frontend": sorted(frontend),
        "patterns": sorted(p for p in patterns if CJK.search(p)),
        "backend": sorted(backend),
    }
    dest = ROOT / "tools" / "i18n_src.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"frontend={len(out['frontend'])} patterns={len(out['patterns'])} backend={len(out['backend'])}")
    print("chars:", sum(len(s) for v in out.values() for s in v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
