#!/usr/bin/env python3
"""Publish the watcher's findings to the site.

The weekly job opens a GitHub issue. That is fine for whoever maintains this
and useless for the person actually applying, who will never look at a repo.
This lifts the headline out of the report so the site can say when the
programs were last checked and what moved.
"""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "data" / "watch-state.json"
REPORT = ROOT / "data" / "watch-report.md"
OUT = ROOT / "site" / "data" / "watch.json"

BROKEN_STATES = ("http-error", "unreachable", "error")
HEADINGS = {
    "Pages that just started mentioning 2027": "now mentions 2027",
    "Pages whose content changed": "page changed",
}
BULLET = re.compile(r"^- \*\*(.+?)\*\*(?:\s*\((.+?)\))?")


def build() -> dict | None:
    if not STATE.is_file():
        return None
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    pages = state.get("pages", {})
    summary = {
        "last_run": (state.get("last_run") or "")[:10],
        "runs": state.get("runs", 0),
        "checked": len(pages),
        "ok": sum(1 for p in pages.values() if p.get("status") == "ok"),
        "blocked": sum(1 for p in pages.values() if p.get("status") == "blocked"),
        "broken": sum(1 for p in pages.values() if p.get("status") in BROKEN_STATES),
        "changes": [],
    }

    # Ten or so of these sites refuse an automated reader. The weekly job will
    # therefore never notice when they post 2027 dates, and two of them are on
    # her original list. Saying nothing would quietly leave a hole in the one
    # promise this page makes, so they are published and named on the site.
    summary["blocked_pages"] = sorted(
        ({"name": p.get("name", ""), "org": p.get("org", ""), "url": p.get("url", "")}
         for p in pages.values() if p.get("status") == "blocked"),
        key=lambda r: r["name"],
    )

    if REPORT.is_file():
        current = None
        for line in REPORT.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                continue
            if current in HEADINGS:
                m = BULLET.match(line)
                if m:
                    summary["changes"].append({
                        "name": m.group(1).strip(),
                        "org": (m.group(2) or "").strip(),
                        "what": HEADINGS[current],
                    })

    summary["changes"] = summary["changes"][:12]
    return summary


def write() -> dict | None:
    summary = build()
    if summary is None:
        return None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if not OUT.is_file() or OUT.read_text(encoding="utf-8") != blob:
        OUT.write_text(blob, encoding="utf-8")
    print(f"  watcher    : last run {summary['last_run']}, "
          f"{summary['ok']}/{summary['checked']} ok, "
          f"{len(summary['changes'])} change(s) -> site/data/watch.json")
    return summary


if __name__ == "__main__":
    write()
