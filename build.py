#!/usr/bin/env python3
"""
build.py — static site generator for pub.mmolina.me

Reads links.yaml, renders template.html (Jinja2) → index.html.

Usage:
    python build.py              # writes index.html
    python build.py --watch      # rebuild on links.yaml changes (requires watchdog)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from itertools import groupby

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required.  pip install pyyaml")
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Error: Jinja2 is required.  pip install jinja2")
    sys.exit(1)

# ── Constants ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
SRC = ROOT / "links.yaml"
TMPL = ROOT / "template.html"
OUT = ROOT / "index.html"

TYPE_ORDER = ["website", "book", "paper", "preprint", "thesis", "note", "project", "other"]

TYPE_BADGES = {
    "website": "web",
    "book": "book",
    "paper": "paper",
    "thesis": "thesis",
    "note": "note",
    "project": "project",
    "preprint": "preprint",
    "other": "other",
}

_YEAR_NONE = 0  # sentinel: entries without a year sort to the bottom


# ── Build ────────────────────────────────────────────────────────────────────


def build() -> None:
    data = yaml.safe_load(SRC.read_text())
    meta = data.get("meta", {})
    entries = data.get("entries", [])

    pinned = [e for e in entries if e.get("pinned")]
    not_pinned = [e for e in entries if not e.get("pinned")]

    # Sort non-pinned by year descending; entries without a year go last
    not_pinned.sort(key=lambda e: -(e.get("year") or _YEAR_NONE))

    # Group non-pinned entries by year
    year_blocks: list[tuple[str, list]] = []
    for yr, grp in groupby(not_pinned, key=lambda e: e.get("year")):
        label = str(yr) if yr else "—"
        year_blocks.append((label, list(grp)))

    # Collect unique types in display order for the filter bar
    seen: list[str] = []
    for e in entries:
        t = e.get("type", "other")
        if t not in seen:
            seen.append(t)
    seen.sort(key=lambda t: TYPE_ORDER.index(t) if t in TYPE_ORDER else 99)

    env = Environment(
        loader=FileSystemLoader(str(ROOT)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(TMPL.name)

    page = template.render(
        meta=meta,
        pinned=pinned,
        year_blocks=year_blocks,
        filter_types=seen,
        type_badges=TYPE_BADGES,
        current_year=datetime.now(timezone.utc).year,
    )
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
