#!/usr/bin/env python3
"""QA sweep over the built dataset, checking things the build does not.

scripts/build.py validates structure. This checks for the subtler failures:
values the UI has no label for (which render as raw slugs), dates that make no
sense against today, duplicates, and copy problems.

    python scripts/qa.py

Exit code is the number of ERROR findings; warnings do not fail.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "programs.json"
APP = ROOT / "site" / "assets" / "app.js"

TODAY = dt.date(2026, 10, 30)
CYCLE_START = dt.date(2026, 10, 1)
CYCLE_END = dt.date(2027, 9, 30)

errors: list[str] = []
warns: list[str] = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warns.append(msg)


def js_keys(source: str, var: str) -> set[str]:
    """Pull the key names out of an object literal in app.js."""
    m = re.search(rf"const {var} = \{{(.*?)\n  \}};", source, re.S)
    if not m:
        return set()
    body = m.group(1)
    return set(re.findall(r'^\s*["\']?([A-Za-z0-9_-]+)["\']?\s*:', body, re.M))


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    programs = payload["programs"]
    app = APP.read_text(encoding="utf-8")

    # ---- label-map coverage: anything missing renders as a raw slug in the UI
    maps = {
        "TRACKS": (js_keys(app, "TRACKS"), "tracks", True),
        "HOUSING_LABELS": (js_keys(app, "HOUSING_LABELS"), "housing", False),
        "CITIZENSHIP_LABELS": (js_keys(app, "CITIZENSHIP_LABELS"), "citizenship", False),
        "SELECTIVITY": (js_keys(app, "SELECTIVITY"), "selectivity", False),
        "REQUIREMENT_LABELS": (js_keys(app, "REQUIREMENT_LABELS"), "requires", True),
    }

    for name, (keys, field, is_list) in maps.items():
        if not keys:
            err(f"could not parse {name} out of app.js. Check the regex")
            continue
        seen = set()
        for p in programs:
            if field == "citizenship":
                v = (p.get("eligibility") or {}).get("citizenship")
                if v:
                    seen.add(v)
            elif is_list:
                seen.update(p.get(field) or [])
            elif p.get(field):
                seen.add(p[field])
        missing = seen - keys
        if missing:
            err(f"{name} has no entry for {sorted(missing)}, the UI will print the raw slug")
        unused = keys - seen
        if unused:
            warn(f"{name} defines unused keys {sorted(unused)}")

    # ---- dates
    for p in programs:
        pid = p["id"]
        o = dt.date.fromisoformat(p["opens"]) if p.get("opens") else None
        d = dt.date.fromisoformat(p["deadline"]) if p.get("deadline") else None

        if d and d < TODAY:
            err(f"{pid}: deadline {d} is already in the past")
        if o and d and o > d:
            err(f"{pid}: opens {o} after deadline {d}")
        if d and not (CYCLE_START <= d <= CYCLE_END):
            warn(f"{pid}: deadline {d} sits outside the Summer 2027 cycle window")
        if o and o < CYCLE_START:
            warn(f"{pid}: opens {o} is before the cycle window")
        if p.get("deadline_status") == "confirmed" and not d:
            err(f"{pid}: marked confirmed with no deadline")
        if p.get("deadline_status") == "rolling" and d:
            warn(f"{pid}: rolling but also carries a deadline")

    # ---- duplicates
    for field, label in (("url", "URL"), ("name", "name")):
        counts = collections.Counter(p[field] for p in programs)
        for value, n in counts.items():
            if n > 1:
                ids = [p["id"] for p in programs if p[field] == value]
                (warn if field == "name" else err)(
                    f"{n} programs share the same {label}: {value} -> {ids}")

    # ---- org + city sanity
    for p in programs:
        if p["city"] == "Unknown" or p["org"].startswith("Unknown"):
            err(f"{p['id']}: still has an Unknown org/city placeholder")
        if p.get("needs_input"):
            err(f"{p['id']}: still flagged needs_input")
        if "google.com/search" in p["url"]:
            err(f"{p['id']}: still points at a search-engine placeholder")

    # ---- copy
    for p in programs:
        for field in ("focus", "notes"):
            text = p.get(field) or ""
            if "  " in text:
                warn(f"{p['id']}: double space in {field}")
            if text and not text.rstrip().endswith((".", "!", "?", ")")):
                warn(f"{p['id']}: {field} does not end in punctuation")
            if re.search(r"\bshe\b|\bher\b|\bJolene\b", text):
                warn(f"{p['id']}: {field} refers to the user by name/pronoun")

    # ---- stipend sanity
    for p in programs:
        s = p.get("stipend_usd")
        if s is not None and not (500 <= s <= 15000):
            warn(f"{p['id']}: stipend {s} looks out of range")

    # ---- summary
    print(f"QA over {len(programs)} programs\n")
    if errors:
        print(f"ERRORS ({len(errors)})")
        for e in errors:
            print(f"  ✗ {e}")
        print()
    if warns:
        print(f"WARNINGS ({len(warns)})")
        for w in warns:
            print(f"  ! {w}")
        print()
    if not errors and not warns:
        print("clean")

    confirmed = sum(1 for p in programs if p["deadline_status"] == "confirmed")
    print(f"dates: {confirmed} confirmed / {len(programs)} total")
    return len(errors)


if __name__ == "__main__":
    raise SystemExit(main())
