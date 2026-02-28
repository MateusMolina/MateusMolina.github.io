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
TYPE_LABELS = {
    "website": "Websites",
    "book": "Books & Notes",
    "paper": "Papers",
    "thesis": "Theses",
    "note": "Notes",
    "project": "Projects",
    "other": "Other",
}
TYPE_BADGES = {
    "website": "web",
    "book": "book",
    "paper": "paper",
    "thesis": "thesis",
    "note": "note",
    "project": "project",
    "other": "other",
}

# ── Helpers ──────────────────────────────────────────────────────────────────


def esc(s: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(s)) if s else ""


def render_entry(entry: dict) -> str:
    title = esc(entry.get("title", "Untitled"))
    url = esc(entry.get("url", "#"))
    description = esc(entry.get("description", ""))
    authors = esc(entry.get("authors", ""))
    venue = esc(entry.get("venue", ""))
    year = esc(str(entry.get("year", "")))
    etype = entry.get("type", "other")
    badge = TYPE_BADGES.get(etype, etype)

    meta_parts = [p for p in [authors, venue, year] if p]
    meta_html = (
        f'<p class="entry-meta">{" · ".join(meta_parts)}</p>' if meta_parts else ""
    )
    desc_html = f'<p class="entry-desc">{description}</p>' if description else ""

    return textwrap.dedent(
        f"""\
        <article class="entry">
          <div class="entry-header">
            <a class="entry-title" href="{url}" target="_blank" rel="noopener">{title}</a>
            <span class="badge badge-{badge}">{badge}</span>
          </div>
          {meta_html}
          {desc_html}
        </article>"""
    )


def render_section(type_key: str, entries: list[dict]) -> str:
    label = TYPE_LABELS.get(type_key, type_key.title())
    # Pinned entries first, then alphabetical by title
    sorted_entries = sorted(
        entries, key=lambda e: (not e.get("pinned", False), e.get("title", "").lower())
    )
    items = "\n".join(render_entry(e) for e in sorted_entries)
    return textwrap.dedent(
        f"""\
        <section class="section">
          <h2>{label}</h2>
          {items}
        </section>"""
    )


def render_page(meta: dict, sections_html: str) -> str:
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
            {sections_html}
          </main>

          <footer class="site-footer">
            <div class="container">
              <p>© {year} <a href="{owner_url}">{owner}</a> ·
                 <a href="https://github.com/MateusMolina/MateusMolina.github.io">source</a></p>
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
          </script>
        </body>
        </html>"""
    )


# ── Build ────────────────────────────────────────────────────────────────────


def build() -> None:
    data = yaml.safe_load(SRC.read_text())
    meta = data.get("meta", {})
    entries = data.get("entries", [])

    # Group by type
    grouped: dict[str, list] = {}
    for entry in entries:
        t = entry.get("type", "other")
        grouped.setdefault(t, []).append(entry)

    sections_html = "\n\n".join(
        render_section(t, grouped[t]) for t in TYPE_ORDER if t in grouped
    )
    # Catch any types not in TYPE_ORDER
    extra = [t for t in grouped if t not in TYPE_ORDER]
    for t in extra:
        sections_html += "\n\n" + render_section(t, grouped[t])

    page = render_page(meta, sections_html)
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
