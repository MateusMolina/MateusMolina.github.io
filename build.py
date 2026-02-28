#!/usr/bin/env python3
"""
build.py — static site generator for pub.mmolina.me

Reads links.yaml and writes index.html.

Usage:
    python build.py              # writes index.html
    python build.py --watch      # rebuild on links.yaml changes (requires watchdog)
"""

import sys
import textwrap
import html
from pathlib import Path
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required.  Install it with:  pip install pyyaml")
    sys.exit(1)

# ── Constants ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
SRC = ROOT / "links.yaml"
OUT = ROOT / "index.html"

TYPE_ORDER = ["website", "book", "paper", "thesis", "note", "project", "other"]

TYPE_BADGES = {
    "website": "web",
    "book": "book",
    "paper": "paper",
    "thesis": "thesis",
    "note": "note",
    "project": "project",
    "other": "other",
}

_YEAR_NONE = 0  # sentinel: entries without a year sort to the bottom


# ── Helpers ──────────────────────────────────────────────────────────────────


def esc(s: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(s)) if s else ""


def render_entry(entry: dict, show_badge: bool = True) -> str:
    title = esc(entry.get("title", "Untitled"))
    url = esc(entry.get("url", "#"))
    description = esc(entry.get("description", ""))
    authors = esc(entry.get("authors", ""))
    venue = esc(entry.get("venue", ""))
    docs_url = esc(entry.get("docs_url", ""))
    etype = entry.get("type", "other")
    badge = TYPE_BADGES.get(etype, etype)
    pinned_cls = " entry--pinned" if entry.get("pinned") else ""

    meta_parts = [p for p in [authors, venue] if p]
    meta_html = (
        f'<p class="entry-meta">{" · ".join(meta_parts)}</p>' if meta_parts else ""
    )
    desc_html = f'<p class="entry-desc">{description}</p>' if description else ""
    badge_html = (
        f'<span class="badge badge-{badge}">{badge}</span>' if show_badge else ""
    )
    links_html = (
        f'<p class="entry-links"><a href="{docs_url}" target="_blank" rel="noopener">docs ↗</a></p>'
        if docs_url
        else ""
    )

    return textwrap.dedent(
        f"""\
        <article class="entry{pinned_cls}" data-type="{etype}">
          <div class="entry-header">
            <a class="entry-title" href="{url}" target="_blank" rel="noopener">{title}</a>
            {badge_html}
          </div>
          {meta_html}
          {desc_html}
          {links_html}
        </article>"""
    )


def render_filter_bar(types: list[str]) -> str:
    tags = [f'<button class="filter-tag filter--active" data-filter="all">all</button>']
    for t in types:
        badge = TYPE_BADGES.get(t, t)
        tags.append(f'<button class="filter-tag" data-filter="{t}">{badge}</button>')
    inner = "\n    ".join(tags)
    return textwrap.dedent(
        f"""\
        <div class="filter-bar" id="filterBar">
          {inner}
        </div>"""
    )


def render_tl_block(year_label: str, entries: list[dict], extra_class: str = "") -> str:
    items = "\n".join(render_entry(e) for e in entries)
    cls = f'tl-block{" " + extra_class if extra_class else ""}'
    return textwrap.dedent(
        f"""\
        <div class="{cls}">
          <div class="tl-gutter">
            <span class="tl-year">{year_label}</span>
          </div>
          <div class="tl-entries">
            {items}
          </div>
        </div>"""
    )


def render_page(meta: dict, timeline_html: str, filter_bar_html: str = "") -> str:
    site_title = esc(meta.get("site_title", "Public links"))
    site_description = esc(meta.get("site_description", ""))
    owner = esc(meta.get("owner", ""))
    owner_url = esc(meta.get("owner_url", "#"))
    year = datetime.now(timezone.utc).year

    return textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="en" data-theme="dark">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>{site_title}</title>
          <meta name="description" content="{site_description}" />
          <link rel="stylesheet" href="styles.css" />
          <link rel="preconnect" href="https://fonts.googleapis.com" />
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
          <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet" />
        </head>
        <body>
          <header class="site-header">
            <div class="container">
              <h1 class="site-title"><a href="/">{site_title}</a></h1>
              <p class="site-desc">{site_description}</p>
              <nav class="header-nav">
                <a href="{owner_url}">{owner}</a>
              </nav>
              <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">☀</button>
            </div>
          </header>

          <main class="container">
            {filter_bar_html}
            <div class="timeline">
              {timeline_html}
            </div>
          </main>

          <footer class="site-footer">
            <div class="container">
              <p>© {year} <a href="{owner_url}">{owner}</a></p>
            </div>
          </footer>

          <script>
            const toggle = document.getElementById('themeToggle');
            const html   = document.documentElement;
            const stored = localStorage.getItem('theme');
            if (stored) html.setAttribute('data-theme', stored);
            toggle.addEventListener('click', () => {{
              const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
              html.setAttribute('data-theme', next);
              localStorage.setItem('theme', next);
              toggle.textContent = next === 'dark' ? '☀' : '☾';
            }});
            // Sync button label on load
            toggle.textContent = (html.getAttribute('data-theme') === 'dark') ? '☀' : '☾';

            // ── Filter bar ──────────────────────────────────────────────
            (function() {{
              const bar = document.getElementById('filterBar');
              if (!bar) return;
              bar.addEventListener('click', function(e) {{
                const btn = e.target.closest('[data-filter]');
                if (!btn) return;
                const f = btn.dataset.filter;
                bar.querySelectorAll('[data-filter]').forEach(function(b) {{
                  b.classList.toggle('filter--active', b === btn);
                }});
                document.querySelectorAll('.entry').forEach(function(el) {{
                  el.hidden = f !== 'all' && el.dataset.type !== f;
                }});
                document.querySelectorAll('.tl-block').forEach(function(block) {{
                  block.hidden = block.querySelectorAll('.entry:not([hidden])').length === 0;
                }});
                const divider = document.querySelector('.tl-divider');
                if (divider) {{
                  const pinned = document.querySelector('.tl-block--pinned');
                  divider.hidden = pinned ? pinned.hidden : false;
                }}
              }});
            }})();
          </script>
        </body>
        </html>"""
    )


# ── Build ────────────────────────────────────────────────────────────────────


def build() -> None:
    data = yaml.safe_load(SRC.read_text())
    meta = data.get("meta", {})
    entries = data.get("entries", [])

    pinned = [e for e in entries if e.get("pinned")]
    not_pinned = [e for e in entries if not e.get("pinned")]

    # Sort non-pinned by year descending; entries without a year go last
    not_pinned.sort(key=lambda e: -(e.get("year") or _YEAR_NONE))

    # Group non-pinned by year
    from itertools import groupby

    year_blocks: list[tuple[str, list]] = []
    for yr, grp in groupby(not_pinned, key=lambda e: e.get("year")):
        label = str(yr) if yr else "—"
        year_blocks.append((label, list(grp)))

    parts: list[str] = []

    # Pinned block at top
    if pinned:
        parts.append(render_tl_block("★", pinned, extra_class="tl-block--pinned"))
        if year_blocks:
            parts.append('<div class="tl-divider"></div>')

    for label, block_entries in year_blocks:
        parts.append(render_tl_block(label, block_entries))

    timeline_html = "\n\n".join(parts)

    # Collect unique types in display order for the filter bar
    seen: list[str] = []
    for e in entries:
        t = e.get("type", "other")
        if t not in seen:
            seen.append(t)
    seen.sort(key=lambda t: (TYPE_ORDER.index(t) if t in TYPE_ORDER else 99))
    filter_bar_html = render_filter_bar(seen)

    page = render_page(meta, timeline_html, filter_bar_html)
    OUT.write_text(page, encoding="utf-8")
    print(f"Built {OUT}  ({len(entries)} entries)")


# ── Watch mode ───────────────────────────────────────────────────────────────


def watch() -> None:
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("Error: watchdog is required for --watch mode.  pip install watchdog")
        sys.exit(1)

    import time

    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if Path(event.src_path).resolve() == SRC.resolve():
                print(f"Detected change in {SRC.name}, rebuilding…")
                try:
                    build()
                except Exception as exc:
                    print(f"Build error: {exc}")

    observer = Observer()
    observer.schedule(Handler(), str(ROOT), recursive=False)
    observer.start()
    print(f"Watching {SRC} for changes.  Ctrl-C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build()
    if "--watch" in sys.argv:
        watch()
