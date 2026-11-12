#!/usr/bin/env python3
"""Validate translation batches: id coverage, placeholders, leftover CJK, empties."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCHES = ROOT / "tools" / "i18n_batches"
OUT = ROOT / "tools" / "i18n_out"
CJK = re.compile(r"[\u4e00-\u9fff]")


def main() -> int:
    problems = 0
    total_ids = total_done = 0
    for p in sorted(BATCHES.glob("batch*.json")):
        items = {it["id"]: it for it in json.loads(p.read_text(encoding="utf-8"))}
        total_ids += len(items)
        outp = OUT / p.name
        if not outp.exists():
            print(f"{p.name}: not translated yet ({len(items)} ids)")
            continue
        try:
            data = json.loads(outp.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"{p.name}: INVALID JSON: {exc}")
            problems += 1
            continue
        missing = [i for i in items if i not in data]
        extra = [i for i in data if i not in items]
        bad_ph, bad_cjk, bad_empty = [], [], []
        for iid, it in items.items():
            tr = data.get(iid) or {}
            for lang in ("ru", "en"):
                val = (tr.get(lang) or "").strip()
                if not val:
                    bad_empty.append((iid, lang))
                    continue
                if CJK.search(val):
                    bad_cjk.append((iid, lang, val[:40]))
                src_n = it["zh"].count("%s")
                if src_n and val.count("%s") != src_n:
                    bad_ph.append((iid, lang, src_n, val.count("%s")))
        total_done += len(items) - len(missing)
        status = "OK" if not (missing or extra or bad_ph or bad_cjk or bad_empty) else "ISSUES"
        print(f"{p.name}: {status} ids={len(data)}/{len(items)} "
              f"missing={len(missing)} extra={len(extra)} empty={len(bad_empty)} "
              f"placeholders={len(bad_ph)} cjk_left={len(bad_cjk)}")
        for label, rows in (("missing", missing), ("extra", extra),
                            ("empty", bad_empty), ("ph", bad_ph), ("cjk", bad_cjk)):
            if rows:
                problems += 1
                print(f"   {label}: {rows[:5]}")
    print(f"\ntotal: {total_done}/{total_ids} strings translated")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
