#!/usr/bin/env python3
"""Publish the watcher's findings to the site.

The weekly job opens a GitHub issue. That is fine for whoever maintains this
and useless for the person actually applying, who will never look at a repo.
This lifts the headline out of the report so the site can say when the
programs were last checked and what moved.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAMS = ROOT / "data" / "programs.json"
STATE = ROOT / "data" / "watch-state.json"
REPORT = ROOT / "data" / "watch-report.md"
OUT = ROOT / "site" / "data" / "watch.json"

# The only results that prove a link is dead: the server answered and said the
# page is not there. A certificate the checker cannot verify, a timeout or a
# server error means the check could not read the page, not that it is gone.
# Baylor's SMART page is the live case: it fails certificate verification for
# the checker, opens fine in a browser, and is taking applications.
DEAD_CODES = (404, 410)
HEADINGS = {
    "Pages that just started mentioning 2027": "now mentions 2027",
    "Pages whose content changed": "page changed",
}
# Some org names carry their own parentheses, "(Lurie Children's)" for one, so
# the org may hold one nested pair rather than stop at the first ")".
BULLET = re.compile(r"^- \*\*(.+?)\*\*(?:\s*\(((?:[^()]|\([^()]*\))+)\))?")
REPORT_DAY = re.compile(r"^# Watch report, ([0-9]{4}-[0-9]{2}-[0-9]{2})")
ISO_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
SHOWN_CHANGES = 12


def as_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def day_of(value) -> str:
    """The YYYY-MM-DD a timestamp starts with, or "" when it has none."""
    first = as_text(value)[:10]
    try:
        return first if ISO_DAY.fullmatch(first) and dt.date.fromisoformat(first) else ""
    except ValueError:
        return ""


def unavailable(why: str) -> dict:
    """What to publish when the watcher's files cannot be trusted.

    Returning nothing left last week's watch.json in place, so the site kept
    telling her the programs were checked on a date the build could no longer
    vouch for. With no last_run the site shows no weekly-check panel at all,
    which is true, and state_unreadable says the gap is a fault, not a watcher
    that has never run.
    """
    print(f"  ! watcher    : {why}, so no last-checked date is published")
    return {
        "last_run": None,
        "state_unreadable": True,
        "runs": 0,
        "checked": 0,
        "ok": 0,
        "blocked": 0,
        "broken": 0,
        "changes": [],
        "changes_total": 0,
        "blocked_pages": [],
        "broken_pages": [],
    }


def build(programs: list | None = None) -> dict:
    """Summarize the last run for the programs on the list now.

    `programs` is the dataset build.py has just validated. Run on its own,
    this reads the copy build.py last wrote, which is the one watch.py reads.
    """
    if programs is None:
        try:
            programs = json.loads(PROGRAMS.read_text(encoding="utf-8"))["programs"]
        except (OSError, ValueError, KeyError, TypeError):
            programs = None
        if not isinstance(programs, list):
            return unavailable("data/programs.json is missing or unreadable")

    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return unavailable("no data/watch-state.json yet")
    except (OSError, ValueError) as exc:  # unreadable, not UTF-8, or not JSON
        return unavailable(f"data/watch-state.json is unreadable ({exc})")

    pages = state.get("pages") if isinstance(state, dict) else None
    last_run = day_of(state.get("last_run")) if isinstance(state, dict) else ""
    if not isinstance(pages, dict) or not last_run:
        return unavailable("data/watch-state.json is not in the shape watch.py writes")

    try:
        report = REPORT.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return unavailable("no data/watch-report.md")
    except (OSError, ValueError) as exc:
        return unavailable(f"data/watch-report.md is unreadable ({exc})")
    # watch.py saves these two files one after the other, so a run that died
    # between them leaves one week's changes beside another week's date.
    stamped = REPORT_DAY.match(report[0]) if report else None
    if stamped and stamped.group(1) != last_run:
        return unavailable(
            f"data/watch-report.md is from {stamped.group(1)} but the state is from {last_run}")

    # Ten or so of these sites refuse an automated reader. The weekly job will
    # therefore never notice when they post 2027 dates, and two of them are on
    # her original list. Saying nothing would quietly leave a hole in the one
    # promise this page makes, so every page the check did not read goes on the
    # list she checks by hand. That is judged against the list as it is now: a
    # program dropped since the run is not hers to check, and one added since,
    # or whose link was corrected, has not been read at that address.
    current = {p["id"]: p for p in programs if isinstance(p, dict) and isinstance(p.get("id"), str)}
    ok, unseen, dead = 0, [], []
    for pid, program in current.items():
        row = {
            "name": as_text(program.get("name")),
            "org": as_text(program.get("org")),
            "url": as_text(program.get("url")),
        }
        page = pages.get(pid)
        page = page if isinstance(page, dict) else {}
        if as_text(page.get("url")) != row["url"]:
            unseen.append(row)
        elif page.get("status") == "ok":
            ok += 1
        elif page.get("status") == "skipped":  # a placeholder link, nothing to read
            continue
        elif page.get("code") in DEAD_CODES:
            dead.append({**row, "reason": as_text(page.get("reason")) or f"HTTP {page['code']}"})
        else:
            unseen.append(row)

    # The report names pages as they were on the day of the run. Matched back
    # through the state, a change to a program since taken off the list is
    # dropped, and the rest are shown under the names the list uses now.
    by_label = {(as_text(p.get("name")), as_text(p.get("org"))): pid
                for pid, p in pages.items() if isinstance(p, dict)}
    changes, heading = [], None
    for line in report:
        if line.startswith("## "):
            heading = line[3:].strip()
            continue
        m = BULLET.match(line) if heading in HEADINGS else None
        if not m:
            continue
        name, org = m.group(1).strip(), (m.group(2) or "").strip()
        pid = by_label.get((name, org))
        if pid is not None and pid not in current:
            continue
        if pid is not None:
            name, org = as_text(current[pid].get("name")), as_text(current[pid].get("org"))
        changes.append({"name": name, "org": org, "what": HEADINGS[heading]})

    runs = state.get("runs")
    return {
        "last_run": last_run,
        "runs": runs if isinstance(runs, int) and not isinstance(runs, bool) else 0,
        "checked": len(current),
        "ok": ok,
        "blocked": len(unseen),
        "broken": len(dead),
        # The site lists the first dozen. The total goes with them so it can
        # say "12 of 33" rather than pass the first dozen off as the week.
        "changes": changes[:SHOWN_CHANGES],
        "changes_total": len(changes),
        "blocked_pages": sorted(unseen, key=lambda r: (r["name"], r["org"], r["url"])),
        "broken_pages": sorted(dead, key=lambda r: (r["name"], r["org"], r["url"])),
    }


def write(programs: list | None = None) -> dict:
    summary = build(programs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Bytes, so the file is LF on every machine: write_text gives CRLF on Windows
    blob = (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if not OUT.is_file() or OUT.read_bytes() != blob:
        OUT.write_bytes(blob)
    if summary["last_run"]:
        print(f"  watcher    : last run {summary['last_run']}, "
              f"{summary['ok']}/{summary['checked']} ok, {summary['broken']} dead, "
              f"{summary['changes_total']} change(s) -> site/data/watch.json")
    return summary


if __name__ == "__main__":
    write()
