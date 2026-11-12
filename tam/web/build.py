#!/usr/bin/env python3
"""构建脚本:合并 index.src.html + styles.css + i18n.data.js + i18n.js + app.js → index.html (单文件部署)。

开发时编辑源文件 index.src.html / styles.css / i18n.js / app.js，构建后生成单文件 index.html。
i18n.data.js 由 tools/i18n_build.py 从翻译批次生成；缺失时用空词典（界面回退中文）。
用法: python build.py
"""
from pathlib import Path

def build():
    base = Path(__file__).parent
    src_html = (base / "index.src.html").read_text(encoding="utf-8")
    css = (base / "styles.css").read_text(encoding="utf-8")
    js = (base / "app.js").read_text(encoding="utf-8")
    i18n_core = (base / "i18n.js").read_text(encoding="utf-8")
    data_file = base / "i18n.data.js"
    i18n_data = (data_file.read_text(encoding="utf-8") if data_file.exists()
                 else "window.__TAM_I18N__ = {ru:{},en:{},pat:{ru:[],en:[]}};\n")

    # 替换占位符
    result = src_html.replace("  /* CSS_PLACEHOLDER */\n", css)
    result = result.replace("/* JS_PLACEHOLDER */\n", i18n_data + "\n" + i18n_core + "\n" + js)

    if "PLACEHOLDER" in result:
        raise RuntimeError("web source contains an unresolved build placeholder")

    out = base / "index.html"
    out.write_text(result, encoding="utf-8")
    print(f"Build complete: {out} ({len(result):,} chars)")

if __name__ == "__main__":
    build()
