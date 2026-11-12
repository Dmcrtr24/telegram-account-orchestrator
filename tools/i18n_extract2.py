#!/usr/bin/env python3
"""Round-2 extraction: what the first pass missed.

Fixes two gaps:
  1. Python sources were scanned with a JS scanner that desyncs on docstrings —
     now every str constant comes from `ast`.
  2. Strings living inside HTML-producing template literals in app.js
     (`<div>还没有账号</div>`) were skipped entirely — now their text nodes and
     placeholder/title attributes are extracted (with ${...} -> %s patterns).

Output: tools/i18n_round2.json  {exact:[...], patterns:[...]}
Only strings that are NOT already in tam/web/i18n.data.js are emitted.
"""
from __future__ import annotations
import ast, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "tam" / "web"
CJK = re.compile(r"[\u4e00-\u9fff]")
PY_FILES = [
    "tam/api.py", "tam/toolbox.py", "tam/tools.py", "tam/manager.py",
    "tam/config.py", "tam/settings_spec.py", "tam/ai_panel.py", "tam/doctor.py",
    "tam/tdata_native.py", "tam/tasks.py", "tam/leads.py", "tam/autokick.py",
    "tam/codefetch.py", "tam/warmup.py", "tam/healthcheck.py", "tam/run.py",
]
ATTR_RE = re.compile(r'(?:placeholder|title|alt|aria-label|value)="([^"]*)"')


def scan_js_templates(src: str):
    """Yield raw template-literal bodies."""
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
        if c == "'" or c == '"':
            q, i = c, i + 1
            start = i
            while i < n and src[i] != q:
                i += 2 if src[i] == "\\" else 1
            yield src[start:i]
            i += 1
            continue
        if c == "`":
            i += 1
            buf = []
            while i < n:
                if src[i] == "\\":
                    buf.append(src[i:i + 2]); i += 2; continue
                if src[i] == "`":
                    break
                buf.append(src[i]); i += 1
            yield "".join(buf)
            i += 1
            continue
        i += 1


def _mask_interp(tpl: str) -> str:
    """Replace every ${...} (with nesting) by @@."""
    out, i, n = [], 0, len(tpl)
    while i < n:
        if tpl.startswith("${", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if tpl[j] == "{":
                    depth += 1
                elif tpl[j] == "}":
                    depth -= 1
                elif tpl[j] in "'\"`":
                    q, j = tpl[j], j + 1
                    while j < n and tpl[j] != q:
                        j += 2 if tpl[j] == "\\" else 1
                j += 1
            out.append("@@")
            i = j
            continue
        out.append(tpl[i]); i += 1
    return "".join(out)


def clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s.replace("\\n", " ").replace("\\t", " "))
    return s.strip()


def main() -> int:
    exact: dict[str, str] = {}
    patterns: dict[str, str] = {}

    JUNK = re.compile(r"(?:'\s*\+|\+\s*'|=>|\bfunction\b|\bawait\b|\bconst\b|\breturn\b|;)")

    def add(zh: str, src: str):
        zh = clean(zh)
        if not zh or not CJK.search(zh) or len(zh) > 300:
            return
        if JUNK.search(zh):
            return
        if "%s" in zh:
            patterns.setdefault(zh, src)
        else:
            exact.setdefault(zh, src)

    # ---- 1. Python string constants (ast) ----
    for rel in PY_FILES:
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        doc_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                        and isinstance(body[0].value.value, str):
                    doc_nodes.add(id(body[0].value))
        for node in ast.walk(tree):
            if id(node) in doc_nodes:
                continue
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                if not CJK.search(s) or len(s) > 300:
                    continue
                # f-strings arrive as JoinedStr; plain constants only here
                add(s, rel)

    # ---- 2. HTML inside JS template literals ----
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for tpl in scan_js_templates(js):
        if "<" not in tpl:
            continue
        body = _mask_interp(tpl)
        for m in ATTR_RE.finditer(body):
            val = m.group(1).strip()
            if val and CJK.search(val):
                add(val.replace("@@", "%s"), "app.js:attr")
        for seg in re.split(r"<[^>]*>", body):
            seg = seg.strip()
            if seg and CJK.search(seg):
                add(seg.replace("@@", "%s"), "app.js:html")

    # ---- 3. drop what is already translated ----
    data_file = WEB / "i18n.data.js"
    known = set()
    if data_file.exists():
        txt = data_file.read_text(encoding="utf-8")
        payload = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        known = set(payload.get("ru", {})) | set(payload.get("en", {}))
        known |= {p[0] for p in payload.get("pat", {}).get("ru", [])}

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip()

    known_n = {norm(k) for k in known}
    out = {
        "exact": sorted(k for k in exact if norm(k) not in known_n),
        "patterns": sorted(k for k in patterns if norm(k) not in known_n),
    }
    (ROOT / "tools" / "i18n_round2.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"new exact={len(out['exact'])} new patterns={len(out['patterns'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
