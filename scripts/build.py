#!/usr/bin/env python3
"""Merge the per-category source files into one validated dataset.

Outputs:
    data/programs.json      merged + validated, the canonical dataset
    site/data/programs.json copy the static site fetches
    data/programs.csv       flat export for Notion / Sheets / Excel
    data/deadlines.ics      calendar feed of deadlines and open dates

Run: python scripts/build.py
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import pathlib
import sys

import guides
import kit
import watch_summary

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
CYCLE = "Summer 2027"

VALID_DEADLINE_STATUS = {"confirmed", "projected", "unknown", "rolling"}
VALID_HOUSING = {
    "provided",
    "provided-nonlocal",
    "not-provided",
    "varies",
    "stipend-covers",
}
VALID_SELECTIVITY = {"very-high", "high", "moderate"}
VALID_CLASS_YEARS = {"freshman", "sophomore", "junior", "senior"}
VALID_URL_CONFIDENCE = {"high", "medium", "low", "none"}

REQUIRED = ["id", "name", "org", "city", "url", "tracks", "focus"]


class ValidationError(Exception):
    pass


def parse_date(value, where):
    if value is None:
        return None
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{where}: bad date {value!r} (want YYYY-MM-DD)") from exc


def validate(program, category):
    pid = program.get("id", "<missing id>")
    where = f"{category} / {pid}"

    for field in REQUIRED:
        if not program.get(field):
            raise ValidationError(f"{where}: missing required field {field!r}")

    if not isinstance(program["tracks"], list) or not program["tracks"]:
        raise ValidationError(f"{where}: tracks must be a non-empty list")

    status = program.get("deadline_status", "unknown")
    if status not in VALID_DEADLINE_STATUS:
        raise ValidationError(
            f"{where}: deadline_status {status!r} not in {sorted(VALID_DEADLINE_STATUS)}"
        )

    housing = program.get("housing", "varies")
    if housing not in VALID_HOUSING:
        raise ValidationError(f"{where}: housing {housing!r} not in {sorted(VALID_HOUSING)}")

    sel = program.get("selectivity", "moderate")
    if sel not in VALID_SELECTIVITY:
        raise ValidationError(f"{where}: selectivity {sel!r} not in {sorted(VALID_SELECTIVITY)}")

    conf = program.get("url_confidence", "medium")
    if conf not in VALID_URL_CONFIDENCE:
        raise ValidationError(f"{where}: url_confidence {conf!r} invalid")

    elig = program.get("eligibility") or {}
    for year in elig.get("class_years", []):
        if year not in VALID_CLASS_YEARS:
            raise ValidationError(f"{where}: class year {year!r} invalid")

    opens = parse_date(program.get("opens"), where + " (opens)")
    deadline = parse_date(program.get("deadline"), where + " (deadline)")
    if opens and deadline and opens > deadline:
        raise ValidationError(f"{where}: opens ({opens}) is after deadline ({deadline})")

    if status == "confirmed" and deadline is None:
        raise ValidationError(f"{where}: deadline_status is 'confirmed' but no deadline is set")

    if not program["url"].startswith(("http://", "https://")):
        raise ValidationError(f"{where}: url must be absolute")


def load_sources():
    if not SOURCES.is_dir():
        raise SystemExit(f"no source directory at {SOURCES}")

    programs = []
    seen = {}
    errors = []

    for path in sorted(SOURCES.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON, {exc}")
            continue

        category = payload.get("category", path.stem)
        for program in payload.get("programs", []):
            try:
                validate(program, category)
            except ValidationError as exc:
                errors.append(str(exc))
                continue

            pid = program["id"]
            if pid in seen:
                errors.append(f"duplicate id {pid!r} in {path.name} (first seen in {seen[pid]})")
                continue
            seen[pid] = path.name

            program["category"] = category
            program["source_file"] = path.name
            programs.append(program)

    return programs, errors


def sort_key(program):
    """Undated programs sort last; otherwise soonest deadline first."""
    deadline = program.get("deadline")
    return (deadline is None, deadline or "9999-12-31", program["name"])



VOLATILE = [
    re.compile(rb'"generated": "[^"]*"'),
    re.compile(rb"DTSTAMP:[0-9TZ]+"),
]


def write_stable(path, blob):
    """Write only when the content changed, ignoring generation timestamps.

    Both outputs carry a stamp of when they were produced, so a plain write
    makes every build dirty the repo even when no data moved. That turns
    `git status` into noise and makes the weekly watcher commit churn. If the
    only difference is the stamp, the existing file is kept.
    """
    if isinstance(blob, str):
        blob = blob.encode("utf-8")
    def without_stamps(b):
        # git may check these out with CRLF while the build writes LF, so
        # normalise endings before comparing or every byte looks changed.
        b = b.replace(b"\r\n", b"\n")
        for pattern in VOLATILE:
            b = pattern.sub(b"", b)
        return b

    if path.is_file() and without_stamps(path.read_bytes()) == without_stamps(blob):
        return False
    path.write_bytes(blob)
    return True


def write_json(programs):
    tracks = sorted({t for p in programs for t in p["tracks"]})
    payload = {
        "cycle": CYCLE,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "count": len(programs),
        "tracks": tracks,
        "categories": sorted({p["category"] for p in programs}),
        "programs": programs,
    }
    blob = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    canonical = ROOT / "data" / "programs.json"
    write_stable(canonical, blob)

    site_data = ROOT / "site" / "data"
    site_data.mkdir(parents=True, exist_ok=True)
    (site_data / "programs.json").write_bytes(canonical.read_bytes())

    return payload


CSV_COLUMNS = [
    "id",
    "name",
    "org",
    "city",
    "category",
    "tracks",
    "focus",
    "opens",
    "deadline",
    "deadline_status",
    "program_dates",
    "duration_weeks",
    "stipend_usd",
    "housing",
    "selectivity",
    "min_gpa",
    "citizenship",
    "class_years",
    "requires",
    "url",
    "url_confidence",
    "notes",
]


def mirror_to_site(path):
    """The site is deployed from site/ alone, so downloads must live beside it."""
    site_data = ROOT / "site" / "data"
    site_data.mkdir(parents=True, exist_ok=True)
    target = site_data / path.name
    target.write_bytes(path.read_bytes())
    return target


def write_csv(programs):
    path = ROOT / "data" / "programs.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for program in programs:
            elig = program.get("eligibility") or {}
            writer.writerow(
                {
                    **program,
                    "tracks": ", ".join(program.get("tracks", [])),
                    "requires": ", ".join(program.get("requires", [])),
                    "class_years": ", ".join(elig.get("class_years", [])),
                    "min_gpa": elig.get("min_gpa") or "",
                    "citizenship": elig.get("citizenship") or "",
                }
            )
    mirror_to_site(path)
    return path



def fold_ics(line):
    """Fold a content line to 75 octets, per RFC 5545 section 3.1.

    Continuation lines begin with a single space. Folding happens on octet
    boundaries, so a split must not land inside a multi-byte UTF-8 sequence, 
    several program names carry em dashes and curly apostrophes.
    """
    data = line.encode("utf-8")
    if len(data) <= 75:
        return line

    pieces = []
    start, limit = 0, 75
    while start < len(data):
        end = min(start + limit, len(data))
        # 0b10xxxxxx marks a UTF-8 continuation byte: back off it
        while start < end < len(data) and (data[end] & 0xC0) == 0x80:
            end -= 1
        pieces.append(data[start:end].decode("utf-8"))
        start = end
        limit = 74  # the leading space counts toward the 75

    return '\r\n '.join(pieces)


def ics_escape(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def write_ics(programs):
    """All-day VEVENTs. Deadlines get a 14-day and 3-day alarm."""
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//jolene-s27//research-finder//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape('Research Apps, ' + CYCLE)}",
    ]

    def event(program, when, kind, summary, alarms):
        uid_seed = f"{program['id']}-{kind}".encode()
        uid = hashlib.sha1(uid_seed).hexdigest()[:20]
        start = when.strftime("%Y%m%d")
        end = (when + dt.timedelta(days=1)).strftime("%Y%m%d")
        status_note = program.get("deadline_status", "unknown")
        body = [
            "BEGIN:VEVENT",
            f"UID:{uid}@jolene-s27",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{ics_escape(program['org'] + ', ' + program['city'] + '. Date status: ' + status_note + '. ' + program['url'])}",
            f"URL:{ics_escape(program['url'])}",
            f"CATEGORIES:{ics_escape(kind)}",
        ]
        for days, label in alarms:
            body += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"TRIGGER:-P{days}D",
                # Six programs on this list are called "Summer Undergraduate
                # Research Program". A phone alarm that says only the name tells
                # her nothing, so the institution goes in the reminder too.
                f"DESCRIPTION:{ics_escape(label + ': ' + program['name'] + ', ' + program['org'])}",
                "END:VALARM",
            ]
        body.append("END:VEVENT")
        return body

    count = 0
    for program in programs:
        deadline = parse_date(program.get("deadline"), program["id"])
        opens = parse_date(program.get("opens"), program["id"])

        if deadline:
            marker = "" if program.get("deadline_status") == "confirmed" else " (est.)"
            lines += event(
                program,
                deadline,
                "deadline",
                f"DUE{marker}: {program['name']}, {program['org']}",
                [(14, "Two weeks out"), (3, "Three days out")],
            )
            count += 1

        if opens:
            lines += event(
                program,
                opens,
                "opens",
                f"Opens: {program['name']}, {program['org']}",
                [(1, "Opens tomorrow")],
            )
            count += 1

    lines.append("END:VCALENDAR")
    path = ROOT / "data" / "deadlines.ics"
    body = '\r\n'.join(fold_ics(line) for line in lines) + '\r\n'
    # write_text would translate each \n to \r\n on Windows, giving \r\r\n
    write_stable(path, body.encode("utf-8"))
    mirror_to_site(path)
    return path, count



def stamp_assets():
    """Version the CSS/JS links by content hash.

    GitHub Pages caches assets, so without this a deploy can hand someone new
    HTML alongside a stale script. The hash changes only when the file does.
    """
    index = ROOT / "site" / "index.html"
    html = index.read_text(encoding="utf-8")
    original = html

    for name in ("assets/styles.css", "assets/app.js"):
        path = ROOT / "site" / name
        if not path.is_file():
            continue
        # Hash the normalised bytes. Git hands this file out with CRLF on
        # Windows and LF in CI, so hashing it as it sits on disk gave the same
        # script two different versions depending on who built it: the commit
        # from a laptop named one, the deploy served the other, and a cache was
        # busted for a change that had not happened.
        digest = hashlib.sha1(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8]
        html = re.sub(
            re.escape(name) + r'(\?v=[0-9a-f]+)?"',
            name + "?v=" + digest + '"',
            html,
        )

    if html != original:
        index.write_text(html, encoding="utf-8")
    return html != original


def main():
    programs, errors = load_sources()

    if errors:
        print("Validation problems:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        if not programs:
            return 1

    programs.sort(key=sort_key)
    payload = write_json(programs)
    csv_path = write_csv(programs)
    ics_path, event_count = write_ics(programs)

    confirmed = sum(1 for p in programs if p.get("deadline_status") == "confirmed")
    projected = sum(1 for p in programs if p.get("deadline_status") == "projected")
    unknown = sum(1 for p in programs if p.get("deadline_status") == "unknown")
    needs_input = sum(1 for p in programs if p.get("needs_input"))

    print(f"Built {payload['count']} programs for {CYCLE}")
    print(f"  categories : {len(payload['categories'])}")
    print(f"  tracks     : {len(payload['tracks'])}")
    print(f"  dates      : {confirmed} confirmed, {projected} projected, {unknown} unknown")
    if needs_input:
        print(f"  needs input: {needs_input} (missing links from the original list)")
    guides.write()
    kit.write()
    watch_summary.write()
    stamp_assets()
    print(f"  wrote      : data/programs.json, site/data/programs.json")
    print(f"               {csv_path.relative_to(ROOT).as_posix()}")
    print(f"               {ics_path.relative_to(ROOT).as_posix()} ({event_count} events)")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
