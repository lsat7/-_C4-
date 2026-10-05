#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slide-forge / build_slides.py
==============================
把一份 Markdown 大纲「锻造」成可直接放映的 HTML 幻灯片（单文件、零依赖）。

Markdown 大纲约定（见 examples/sample-outline.md）：
    # 演示总标题                -> 封面页
    ## 第 N 页标题               -> 一页幻灯片
    - 要点一                    -> 项目符号
        - 子要点                -> 二级缩进项目符号
    > 演讲词：……                -> 演讲者备注（放映时按 S 键显示）
    ```python ... ```           -> 代码块（自动高亮为等宽字体）
    ![说明](图片地址)            -> 图片

用法：
    python build_slides.py outline.md
    python build_slides.py outline.md -o slides.html --title "我的演示"
    python build_slides.py outline.md --theme dark

仅依赖 Python 标准库（re / html / pathlib / argparse / json）。
"""

from __future__ import annotations

import argparse
import html as _html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #

@dataclass
class Slide:
    title: str
    bullets: List[str] = field(default_factory=list)   # 已渲染的 HTML 片段
    notes: List[str] = field(default_factory=list)     # 演讲词（纯文本）
    image: Optional[str] = None                         # 图片地址
    code: Optional[str] = None                          # 代码块内容
    code_lang: Optional[str] = None


# --------------------------------------------------------------------------- #
# Markdown 解析
# --------------------------------------------------------------------------- #

INLINE_PATTERNS = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),                # 行内代码
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),      # 加粗
    (re.compile(r"__([^_]+)__"), r"<strong>\1</strong>"),
    (re.compile(r"\*([^*]+)\*"), r"<em>\1</em>"),                  # 斜体
    (re.compile(r"_([^_]+)_"), r"<em>\1</em>"),
]


def _inline(text: str) -> str:
    """把行内 Markdown（代码/加粗/斜体）转成 HTML，并做转义。"""
    text = _html.escape(text, quote=False)
    for pattern, repl in INLINE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def _render_bullet(level: int, text: str) -> str:
    """按缩进层级渲染一条项目符号。"""
    indent = "    " * level
    mark = "•" if level == 0 else "–"
    return f'{indent}<li class="lvl{level}"><span class="dot">{mark}</span>{_inline(text)}</li>'


def _render_bullets(bullets: List[str]) -> str:
    """把若干已按 level 分组渲染的 bullet 合并成一个列表。"""
    if not bullets:
        return ""
    # bullets 里存的是「缩进后的行」格式：(level, text)
    groups = []
    return "<ul>" + "".join(bullets) + "</ul>"


def parse_outline(md_text: str) -> tuple[str, List[Slide]]:
    """解析大纲，返回 (演示标题, 幻灯片列表)。"""
    title = "演示文稿"
    slides: List[Slide] = []
    current: Optional[Slide] = None
    bullets: List[str] = []
    in_code = False
    code_buf: List[str] = []
    code_lang = ""
    image: Optional[str] = None

    def flush_code():
        nonlocal in_code, code_buf, code_lang
        if current is not None and code_buf:
            current.code = "\n".join(code_buf)
            current.code_lang = code_lang or None
        in_code = False
        code_buf = []
        code_lang = ""

    def flush_slide():
        nonlocal current, bullets, image
        if current is not None:
            current.bullets = list(bullets)
            if image:
                current.image = image
            slides.append(current)
        current = None
        bullets = []
        image = None

    for raw in md_text.splitlines():
        line = raw.rstrip()

        # 代码块边界
        fence = re.match(r"^```(\w*)", line)
        if fence:
            if not in_code:
                flush_code()
                in_code = True
                code_lang = fence.group(1)
            else:
                flush_code()
            continue
        if in_code:
            code_buf.append(raw)
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1:
                # 演示总标题（封面）
                if not title or title == "演示文稿" or not any(
                    s.bullets or s.title != "演示文稿" for s in slides
                ):
                    title = text
                continue
            elif level == 2:
                flush_slide()
                current = Slide(title=text)
                continue
            elif level == 3 and current is not None and not current.bullets:
                # 允许用 ### 作为页面标题（兼容）
                current.title = text
                continue

        if current is None:
            continue

        # 图片
        mimg = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if mimg:
            image = mimg.group(2)
            continue

        # 演讲词
        mnote = re.match(r"^\s*>\s?(.*)$", line)
        if mnote:
            current.notes.append(mnote.group(1))
            continue

        # 项目符号（支持缩进层级）
        mbul = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if mbul:
            level = len(mbul.group(1)) // 2
            level = max(0, min(level, 2))
            bullets.append(_render_bullet(level, mbul.group(2)))
            continue

        # 普通段落
        if line.strip():
            bullets.append(f'<li class="lvl0"><span class="dot">•</span>{_inline(line.strip())}</li>')

    flush_code()
    flush_slide()
    return title, slides


# --------------------------------------------------------------------------- #
# 主题
# --------------------------------------------------------------------------- #

THEMES = {
    "light": {
        "bg": "#f6f7fb",
        "card": "#ffffff",
        "ink": "#1f2430",
        "muted": "#6b7280",
        "accent": "#3b5bdb",
        "accent2": "#e8590c",
        "code_bg": "#f1f3f9",
        "cover_bg": "linear-gradient(135deg,#1d2b53 0%,#3b5bdb 100%)",
        "cover_ink": "#ffffff",
    },
    "dark": {
        "bg": "#10131c",
        "card": "#1a1f2e",
        "ink": "#e7ebf3",
        "muted": "#9aa3b5",
        "accent": "#6c8cff",
        "accent2": "#ff9f43",
        "code_bg": "#0c0f17",
        "cover_bg": "linear-gradient(135deg,#0d1220 0%,#3b5bdb 100%)",
        "cover_ink": "#ffffff",
    },
}


# --------------------------------------------------------------------------- #
# HTML 生成
# --------------------------------------------------------------------------- #

def _escape_attr(s: str) -> str:
    return _html.escape(s, quote=True)


def build_html(title: str, slides: List[Slide], theme: dict) -> str:
    esc_title = _escape_attr(title)

    # 封面
    cover = f"""
    <section class="slide cover">
      <div class="cover-box">
        <div class="cover-tag">SLIDE · FORGE</div>
        <h1 class="cover-title">{_inline(title)}</h1>
        <div class="cover-sub">输入主题或大纲 · 锻造出可直接放映的幻灯片</div>
        <div class="cover-hint">按 → 或 空格键 开始放映 · 按 S 查看演讲词 · 按 F 全屏</div>
      </div>
    </section>"""

    body = []
    for i, s in enumerate(slides, 1):
        bullets_html = _render_bullets(s.bullets) if s.bullets else ""
        image_html = (
            f'<figure class="slide-img"><img src="{_escape_attr(s.image)}" alt=""></figure>'
            if s.image
            else ""
        )
        code_html = ""
        if s.code:
            lang_label = _escape_attr(s.code_lang or "code")
            code_html = (
                f'<div class="code-block"><div class="code-lang">{lang_label}</div>'
                f"<pre><code>{_html.escape(s.code)}</code></pre></div>"
            )
        notes_html = ""
        if s.notes:
            joined = "<br>".join(_html.escape(n) for n in s.notes)
            notes_html = (
                f'<div class="notes"><div class="notes-head">演讲词</div>'
                f'<div class="notes-body">{joined}</div></div>'
            )

        # 有图片或代码时用左右分栏，否则单列
        split = bool(s.image or s.code)
        left = f'<div class="col-left">{bullets_html}</div>'
        right = f'<div class="col-right">{image_html}{code_html}</div>'
        content = (
            f'<div class="split">{left}{right}</div>' if split else bullets_html
        )

        body.append(
            f"""
    <section class="slide" data-index="{i}">
      <header class="slide-head">
        <span class="slide-kicker">{esc_title}</span>
        <span class="slide-num">{i:02d} / {len(slides):02d}</span>
      </header>
      <h2 class="slide-title">{_inline(s.title)}</h2>
      <div class="slide-body">{content}</div>
      {notes_html}
    </section>"""
        )

    slides_html = "".join(body)
    total = len(slides) + 1  # +封面

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc_title}</title>
<style>
:root {{
  --bg: {theme['bg']};
  --card: {theme['card']};
  --ink: {theme['ink']};
  --muted: {theme['muted']};
  --accent: {theme['accent']};
  --accent2: {theme['accent2']};
  --code-bg: {theme['code_bg']};
  --cover-bg: {theme['cover_bg']};
  --cover-ink: {theme['cover_ink']};
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
  overflow: hidden;
}}
.slide {{
  display: none;
  position: absolute; inset: 0;
  padding: 6vh 7vw;
  flex-direction: column;
  justify-content: flex-start;
  animation: fadein .35s ease;
}}
.slide.active {{ display: flex; }}
@keyframes fadein {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}

/* 封面 */
.cover {{ background: var(--cover-bg); color: var(--cover-ink); justify-content: center; align-items: flex-start; }}
.cover-box {{ max-width: 880px; }}
.cover-tag {{ font-size: 14px; letter-spacing: .35em; opacity: .8; margin-bottom: 2.5vh; }}
.cover-title {{ font-size: clamp(40px, 7vw, 76px); line-height: 1.15; font-weight: 800; margin-bottom: 3vh; }}
.cover-sub {{ font-size: clamp(16px, 2.2vw, 22px); opacity: .9; margin-bottom: 6vh; }}
.cover-hint {{ font-size: 13px; opacity: .55; }}

/* 页头 */
.slide-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 3vh; }}
.slide-kicker {{ font-size: 12px; letter-spacing: .12em; color: var(--muted); text-transform: uppercase; }}
.slide-num {{ font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.slide-title {{ font-size: clamp(24px, 3.6vw, 40px); font-weight: 700; margin-bottom: 3vh; position: relative; padding-left: 18px; }}
.slide-title::before {{ content: ""; position: absolute; left: 0; top: .15em; bottom: .15em; width: 6px; border-radius: 3px; background: linear-gradient(var(--accent), var(--accent2)); }}

.slide-body {{ flex: 1; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }}
ul {{ list-style: none; }}
li {{ display: flex; align-items: flex-start; font-size: clamp(16px, 2.4vw, 24px); line-height: 1.5; margin-bottom: 1.6vh; color: var(--ink); }}
li .dot {{ color: var(--accent); font-weight: 700; margin-right: 12px; min-width: 14px; }}
li.lvl1 {{ font-size: clamp(14px, 2vw, 20px); margin-left: 28px; color: var(--muted); }}
li.lvl2 {{ font-size: clamp(13px, 1.8vw, 18px); margin-left: 56px; color: var(--muted); }}
li code {{ background: var(--code-bg); padding: 1px 7px; border-radius: 5px; font-family: "Cascadia Code", Consolas, monospace; font-size: .9em; }}

.split {{ display: flex; gap: 4vw; align-items: center; height: 100%; }}
.col-left {{ flex: 1; }}
.col-right {{ flex: 1; display: flex; flex-direction: column; gap: 2.5vh; justify-content: center; }}
.slide-img img {{ max-width: 100%; max-height: 46vh; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.18); display: block; margin: 0 auto; }}

.code-block {{ background: var(--code-bg); border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,.14); }}
.code-lang {{ font-size: 11px; letter-spacing: .1em; color: var(--muted); padding: 8px 16px; border-bottom: 1px solid rgba(128,128,128,.2); text-transform: uppercase; }}
.code-block pre {{ padding: 16px 18px; overflow: auto; }}
.code-block code {{ font-family: "Cascadia Code", Consolas, monospace; font-size: clamp(12px, 1.5vw, 15px); line-height: 1.6; color: var(--ink); }}

/* 演讲词 */
.notes {{ display: none; position: absolute; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.85); color: #fff; padding: 22px 6vw 26px; border-top: 3px solid var(--accent2); }}
.notes-head {{ font-size: 12px; letter-spacing: .2em; color: var(--accent2); margin-bottom: 8px; }}
.notes-body {{ font-size: 16px; line-height: 1.6; }}
body.show-notes .notes {{ display: block; }}

/* 进度条 + 控制器 */
#progress {{ position: fixed; left: 0; bottom: 0; height: 4px; background: var(--accent); transition: width .25s ease; z-index: 99; }}
#counter {{ position: fixed; right: 18px; bottom: 10px; font-size: 12px; color: var(--muted); z-index: 99; font-variant-numeric: tabular-nums; }}
#hint {{ position: fixed; left: 18px; bottom: 10px; font-size: 12px; color: var(--muted); z-index: 99; opacity: .8; }}

@media print {{
  body {{ overflow: visible; background: #fff; }}
  .slide {{ position: relative; display: block !important; page-break-after: always; padding: 40px; min-height: 100vh; }}
  #progress, #counter, #hint {{ display: none; }}
}}
</style>
</head>
<body>

{cover}
{slides_html}

<div id="progress"></div>
<div id="counter"></div>
<div id="hint">← → / 空格翻页 · S 演讲词 · F 全屏 · Home 回封面</div>

<script>
(function () {{
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var total = slides.length;
  var idx = 0;
  var progress = document.getElementById('progress');
  var counter = document.getElementById('counter');

  function show(n) {{
    idx = (n + total) % total;
    slides.forEach(function (s, i) {{ s.classList.toggle('active', i === idx); }});
    progress.style.width = ((idx + 1) / total * 100) + '%';
    counter.textContent = (idx + 1) + ' / ' + total;
  }}

  document.addEventListener('keydown', function (e) {{
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{ e.preventDefault(); show(idx + 1); }}
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ e.preventDefault(); show(idx - 1); }}
    else if (e.key === 'Home') {{ show(0); }}
    else if (e.key.toLowerCase() === 's') {{ document.body.classList.toggle('show-notes'); }}
    else if (e.key.toLowerCase() === 'f') {{
      if (!document.fullscreenElement) {{ document.documentElement.requestFullscreen(); }}
      else {{ document.exitFullscreen(); }}
    }}
  }});

  document.addEventListener('click', function (e) {{
    if (e.target.closest('a, button, input, textarea, pre, code')) return;
    if (e.clientX > window.innerWidth / 2) show(idx + 1);
    else show(idx - 1);
  }});

  show(0);
}})();
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="slide-forge：把 Markdown 大纲锻造成可直接放映的 HTML 幻灯片。"
    )
    parser.add_argument("outline", help="Markdown 大纲文件路径")
    parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件路径（默认与大纲同名 .html）")
    parser.add_argument("--title", default=None, help="覆盖演示标题")
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="配色主题（默认 light）")
    args = parser.parse_args(argv)

    src = Path(args.outline).expanduser()
    if not src.is_file():
        print(f"ERROR: 找不到大纲文件 '{src}'", file=sys.stderr)
        return 1

    md_text = src.read_text(encoding="utf-8", errors="replace")
    title, slides = parse_outline(md_text)

    if args.title:
        title = args.title

    if not slides:
        print("WARNING: 大纲中没有解析出任何页面（请使用 '## 页标题' 定义每一页）。", file=sys.stderr)

    out = Path(args.output) if args.output else src.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)

    html_doc = build_html(title, slides, THEMES[args.theme])
    out.write_text(html_doc, encoding="utf-8")

    print(f"✓ 已生成幻灯片：{out}")
    print(f"  共 {len(slides) + 1} 页（含封面）｜主题：{args.theme}｜演示标题：{title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
