"""
wiki.py — Web-accessible documentation server for Buffotte.

Serves rendered Markdown documentation as a beautiful HTML page at /wiki.
Renders all .md files from the docs/ directory with a sidebar navigation.

Mount into FastAPI:
    from wiki import mount_wiki
    mount_wiki(app)
"""

import os
import importlib
import logging

logger = logging.getLogger(__name__)

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

# Display name mapping: filename -> Chinese title
DOC_TITLES = {
    "getting-started": "快速开始",
    "architecture": "系统架构",
    "api": "API 接口",
    "database": "数据库设计",
    "crawler": "爬虫系统",
    "llm": "AI 分析",
    "deployment": "部署指南",
    "roadmap": "开发路线图",
}

# Ordered navigation
DOC_ORDER = [
    "getting-started",
    "architecture",
    "api",
    "database",
    "crawler",
    "llm",
    "deployment",
    "roadmap",
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - Buffotte Wiki</title>
<style>
  :root {{
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-tertiary: #1a2332;
    --bg-sidebar: #0d1321;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent: #22d3ee;
    --accent-dim: #0891b2;
    --accent-glow: rgba(34, 211, 238, 0.15);
    --border: #1e293b;
    --border-accent: #22d3ee33;
    --code-bg: #0f172a;
    --success: #10b981;
    --warning: #f59e0b;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    display: flex;
    min-height: 100vh;
    line-height: 1.7;
  }}

  /* Sidebar */
  .sidebar {{
    width: 260px;
    min-width: 260px;
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
    padding: 24px 0;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    overflow-y: auto;
    z-index: 100;
  }}

  .sidebar-header {{
    padding: 0 20px 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
  }}

  .sidebar-header h1 {{
    font-size: 20px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 1px;
  }}

  .sidebar-header .subtitle {{
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
  }}

  .nav-list {{
    list-style: none;
  }}

  .nav-item {{
    display: block;
    padding: 10px 20px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    transition: all 0.2s;
    border-left: 3px solid transparent;
  }}

  .nav-item:hover {{
    background: var(--accent-glow);
    color: var(--text-primary);
    border-left-color: var(--accent-dim);
  }}

  .nav-item.active {{
    background: var(--accent-glow);
    color: var(--accent);
    border-left-color: var(--accent);
    font-weight: 600;
  }}

  .nav-icon {{
    margin-right: 8px;
    font-size: 13px;
    opacity: 0.7;
  }}

  /* Main content */
  .main {{
    margin-left: 260px;
    flex: 1;
    padding: 40px 48px;
    max-width: 960px;
  }}

  .main h1 {{
    font-size: 32px;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 8px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }}

  .main h2 {{
    font-size: 22px;
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 40px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}

  .main h3 {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 28px;
    margin-bottom: 12px;
  }}

  .main p {{
    margin-bottom: 14px;
    color: var(--text-secondary);
  }}

  .main strong {{
    color: var(--text-primary);
    font-weight: 600;
  }}

  .main a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px dashed var(--accent-dim);
  }}

  .main a:hover {{
    border-bottom-style: solid;
  }}

  .main ul, .main ol {{
    margin: 12px 0;
    padding-left: 24px;
    color: var(--text-secondary);
  }}

  .main li {{
    margin-bottom: 6px;
  }}

  /* Code blocks */
  .main pre {{
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.6;
  }}

  .main code {{
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  }}

  .main :not(pre) > code {{
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 13px;
    color: var(--accent);
  }}

  /* Tables */
  .main table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 14px;
  }}

  .main thead {{
    background: var(--bg-tertiary);
  }}

  .main th {{
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 2px solid var(--accent-dim);
  }}

  .main td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
  }}

  .main tbody tr:hover {{
    background: var(--accent-glow);
  }}

  /* Blockquotes */
  .main blockquote {{
    border-left: 4px solid var(--accent);
    background: var(--accent-glow);
    padding: 12px 20px;
    margin: 16px 0;
    border-radius: 0 8px 8px 0;
  }}

  .main blockquote p {{
    color: var(--text-primary);
    margin: 0;
  }}

  /* Horizontal rule */
  .main hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 32px 0;
  }}

  /* Badge-like spans */
  .main .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    margin: 0 4px;
  }}

  /* Mobile responsive */
  @media (max-width: 768px) {{
    .sidebar {{
      width: 100%;
      position: relative;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }}
    .main {{
      margin-left: 0;
      padding: 24px 16px;
    }}
    body {{ flex-direction: column; }}
  }}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-header">
    <h1>BUFFOTTE</h1>
    <div class="subtitle">CS2 饰品市场智能分析平台</div>
  </div>
  <ul class="nav-list">
    {nav_items}
  </ul>
</aside>

<main class="main">
  {content}
</main>

</body>
</html>"""


def _render_markdown(text: str) -> str:
    """Render markdown text to HTML using the markdown library."""
    try:
        md = importlib.import_module("markdown")
    except ImportError:
        # Fallback: basic rendering without the library
        return _simple_render(text)

    return md.markdown(
        text,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": True},
        },
    )


def _simple_render(text: str) -> str:
    """Minimal fallback renderer if markdown library is not installed."""
    import html as html_module

    lines = text.split("\n")
    output = []
    in_code = False
    code_buf = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                output.append("<pre><code>" + "\n".join(code_buf) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(html_module.escape(line))
            continue
        if stripped.startswith("# "):
            output.append(f"<h1>{html_module.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            output.append(f"<h2>{html_module.escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            output.append(f"<h3>{html_module.escape(stripped[4:])}</h3>")
        elif stripped.startswith("---"):
            output.append("<hr>")
        elif stripped:
            output.append(f"<p>{html_module.escape(stripped)}</p>")

    return "\n".join(output)


def _read_doc(filename: str) -> str:
    """Read a markdown file from docs/ directory."""
    filepath = os.path.join(DOCS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return f"# 文件未找到\n\n无法加载 `{filename}`。"


def _build_nav(active_doc: str) -> str:
    """Build sidebar navigation HTML."""
    icons = {
        "getting-started": "&#9654;",
        "architecture": "&#9670;",
        "api": "&#8674;",
        "database": "&#9681;",
        "crawler": "&#9881;",
        "llm": "&#9733;",
        "deployment": "&#9650;",
        "roadmap": "&#9998;",
    }
    items = []
    for doc_id in DOC_ORDER:
        title = DOC_TITLES.get(doc_id, doc_id)
        icon = icons.get(doc_id, "&#8226;")
        active = ' active' if doc_id == active_doc else ''
        items.append(
            f'<li><a href="/wiki/{doc_id}" class="nav-item{active}">'
            f'<span class="nav-icon">{icon}</span>{title}</a></li>'
        )
    return "\n".join(items)


def _render_page(doc_id: str) -> str:
    """Render a full documentation page."""
    filename = f"{doc_id}.md"
    md_text = _read_doc(filename)
    html_content = _render_markdown(md_text)
    nav_items = _build_nav(doc_id)
    title = DOC_TITLES.get(doc_id, "Buffotte Wiki")
    return HTML_TEMPLATE.format(title=title, nav_items=nav_items, content=html_content)


def _render_index() -> str:
    """Render the wiki index page."""
    intro_md = """# Buffotte Wiki

欢迎使用 **Buffotte** 项目文档。这是一个 CS2 饰品市场智能分析平台，集成了实时数据采集、AI 智能分析和价格预测等功能。

## 文档导航

| 文档 | 说明 |
|------|------|
| [快速开始](/wiki/getting-started) | 环境搭建与本地开发指南 |
| [系统架构](/wiki/architecture) | 整体架构设计与数据流 |
| [API 接口](/wiki/api) | REST API 接口完整参考 |
| [数据库设计](/wiki/database) | 表结构与 ER 关系图 |
| [爬虫系统](/wiki/crawler) | Playwright 爬虫技术详解 |
| [AI 分析](/wiki/llm) | LLM Agent 流水线与大盘分析 |
| [部署指南](/wiki/deployment) | Docker 部署与自动化运维 |
| [开发路线图](/wiki/roadmap) | 功能进度与未来规划 |

---

> **在线 API 交互文档**: [Swagger UI](/docs) | [ReDoc](/redoc)
"""
    html_content = _render_markdown(intro_md)
    nav_items = _build_nav("")
    return HTML_TEMPLATE.format(title="Buffotte Wiki", nav_items=nav_items, content=html_content)


def mount_wiki(app):
    """Mount the wiki documentation routes onto a FastAPI app."""

    from fastapi import Response

    @app.get("/wiki", include_in_schema=False)
    @app.get("/wiki/", include_in_schema=False)
    async def wiki_index():
        return Response(content=_render_index(), media_type="text/html; charset=utf-8")

    @app.get("/wiki/{doc_id}", include_in_schema=False)
    async def wiki_page(doc_id: str):
        if doc_id not in DOC_TITLES:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/wiki")
        return Response(content=_render_page(doc_id), media_type="text/html; charset=utf-8")

    logger.info("Wiki documentation mounted at /wiki")
