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
import io
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

# Whether the opening date is known, guessed, or replaced by the page simply
# saying the portal is open. Without this the site had to treat a guessed
# opening date in the past as proof the portal was open, and said so as fact.
#   confirmed  `opens` was read off the program's own page
#   projected  `opens` is an estimate, usually last cycle carried forward
#   open-now   the page says applications are open but gives no date (opens null)
#   unknown    nothing is known (opens null)
VALID_OPENS_STATUS = {"confirmed", "projected", "open-now", "unknown"}
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

# date.fromisoformat also takes 20270115 and 2027-W03-1 on Python 3.11+. The
# sort, the CSV and the site's own date parser all read the raw string, and
# this is the only shape that means the same day to every one of them.
DATE_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# The calendar carries the link raw, as a URI value must be, so a line break
# in one would start a calendar line of its own.
URL_BREAKS = re.compile(r"[\s\x00-\x1f\x7f]")


class ValidationError(Exception):
    pass


def parse_date(value, where):
    if value is None:
        return None
    if not isinstance(value, str) or not DATE_SHAPE.fullmatch(value):
        raise ValidationError(f"{where}: bad date {value!r} (want YYYY-MM-DD)")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{where}: bad date {value!r} (want YYYY-MM-DD)") from exc


def is_text_list(value):
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def is_number(value):
    # bool is a subclass of int, so true would otherwise pass as a $1 stipend
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_one_of(value, choices):
    # `in` hashes its operand, so a list here raised TypeError instead of
    # reaching the error message that names the record
    return isinstance(value, str) and value in choices


def validate(program, category):
    pid = program.get("id", "<missing id>")
    where = f"{category} / {pid}"

    for field in REQUIRED:
        if not program.get(field):
            raise ValidationError(f"{where}: missing required field {field!r}")

    # Only truthiness was checked above, so a number or a list in one of these
    # got through and crashed the build later, far from the record at fault.
    for field in ("id", "name", "org", "city", "url", "focus"):
        if not isinstance(program[field], str):
            raise ValidationError(f"{where}: {field} must be text")

    if not is_text_list(program["tracks"]):
        raise ValidationError(f"{where}: tracks must be a non-empty list of text")

    # One requirement written as "transcript" rather than ["transcript"] is an
    # easy slip, and ", ".join() spelled it out letter by letter in the CSV.
    if not is_text_list(program.get("requires", [])):
        raise ValidationError(f"{where}: requires must be a list of text")

    for field in ("stipend_usd", "duration_weeks"):
        if program.get(field) is not None and not is_number(program[field]):
            raise ValidationError(f"{where}: {field} must be a number or null")

    # The site filters on these with !!value, so the text "false" would put a
    # program in the can-live-at-home list.
    for field in ("near_home", "home_institution", "paid"):
        if field in program and not isinstance(program[field], bool):
            raise ValidationError(f"{where}: {field} must be true or false")

    status = program.get("deadline_status", "unknown")
    if not is_one_of(status, VALID_DEADLINE_STATUS):
        raise ValidationError(
            f"{where}: deadline_status {status!r} not in {sorted(VALID_DEADLINE_STATUS)}"
        )

    housing = program.get("housing", "varies")
    if not is_one_of(housing, VALID_HOUSING):
        raise ValidationError(f"{where}: housing {housing!r} not in {sorted(VALID_HOUSING)}")

    sel = program.get("selectivity", "moderate")
    if not is_one_of(sel, VALID_SELECTIVITY):
        raise ValidationError(f"{where}: selectivity {sel!r} not in {sorted(VALID_SELECTIVITY)}")

    conf = program.get("url_confidence", "medium")
    if not is_one_of(conf, VALID_URL_CONFIDENCE):
        raise ValidationError(f"{where}: url_confidence {conf!r} invalid")

    # `or {}` let a non-empty string through to .get() below
    elig = program.get("eligibility")
    if elig is None:
        elig = {}
    if not isinstance(elig, dict):
        raise ValidationError(f"{where}: eligibility must be an object")
    years = elig.get("class_years", [])
    if not is_text_list(years):
        raise ValidationError(f"{where}: eligibility.class_years must be a list of text")
    for year in years:
        if year not in VALID_CLASS_YEARS:
            raise ValidationError(f"{where}: class year {year!r} invalid")
    if elig.get("min_gpa") is not None and not is_number(elig["min_gpa"]):
        raise ValidationError(f"{where}: eligibility.min_gpa must be a number or null")

    opens = parse_date(program.get("opens"), where + " (opens)")
    deadline = parse_date(program.get("deadline"), where + " (deadline)")
    if opens and deadline and opens > deadline:
        raise ValidationError(f"{where}: opens ({opens}) is after deadline ({deadline})")

    if status == "confirmed" and deadline is None:
        raise ValidationError(f"{where}: deadline_status is 'confirmed' but no deadline is set")

    opens_status = program.get("opens_status", "projected" if opens else "unknown")
    if not is_one_of(opens_status, VALID_OPENS_STATUS):
        raise ValidationError(
            f"{where}: opens_status {opens_status!r} not in {sorted(VALID_OPENS_STATUS)}"
        )
    if opens_status in ("confirmed", "projected") and opens is None:
        raise ValidationError(f"{where}: opens_status is {opens_status!r} but no opens date is set")
    if opens_status in ("open-now", "unknown") and opens is not None:
        raise ValidationError(f"{where}: opens_status is {opens_status!r} but an opens date is set")

    if not program["url"].startswith(("http://", "https://")):
        raise ValidationError(f"{where}: url must be absolute")
    if URL_BREAKS.search(program["url"]):
        raise ValidationError(f"{where}: url must not contain spaces or line breaks")


def load_sources():
    if not SOURCES.is_dir():
        raise SystemExit(f"no source directory at {SOURCES}")

    programs = []
    seen = {}
    errors = []

    # Ordered by name as a plain string. Sorting Paths compares them
    # case-folded on Windows and as-is elsewhere, and glob matches .JSON on
    # Windows only, so either one let the machine decide the record order.
    sources = sorted(
        (p for p in SOURCES.iterdir() if p.name.endswith(".json") and p.is_file()),
        key=lambda p: p.name,
    )
    for path in sources:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:  # invalid JSON, or bytes that are not UTF-8
            errors.append(f"{path.name}: invalid JSON, {exc}")
            continue

        # Anything that parses but is not {"category": ..., "programs": [...]}
        # crashed here with a traceback instead of an error line. A bare
        # top-level list of records is the likeliest way to get there.
        if not isinstance(payload, dict) or not isinstance(payload.get("programs", []), list):
            errors.append(f'{path.name}: want {{"category": ..., "programs": [...]}}')
            continue
        category = payload.get("category", path.stem)
        if not isinstance(category, str) or not category:
            errors.append(f"{path.name}: category must be text")
            continue

        for index, program in enumerate(payload.get("programs", [])):
            if not isinstance(program, dict):
                errors.append(f"{path.name}: programs[{index}] is not an object")
                continue
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
    """Undated programs sort last; otherwise soonest deadline first.

    Several programs share a name and dozens have no deadline, so the id
    breaks the ties. Without it the order of tied records came from file order.
    """
    deadline = program.get("deadline")
    return (deadline is None, deadline or "9999-12-31", program["name"], program["id"])



VOLATILE = [
    re.compile(rb'"generated": "[^"]*"'),
    re.compile(rb"DTSTAMP:[0-9TZ]+"),
]


def write_stable(path, blob):
    """Write only when the content changed, ignoring generation timestamps.

    Two outputs carry a stamp of when they were produced, so a plain write
    makes every build dirty the repo even when no data moved. That turns
    `git status` into noise and makes the weekly watcher commit churn. If the
    only difference is the stamp, the existing file is kept.

    Line endings count like any other byte. Folding CRLF into LF here let an
    LF checkout of the calendar pass for the CRLF file RFC 5545 requires, so
    CI kept the LF copy and published it.
    """
    if isinstance(blob, str):
        blob = blob.encode("utf-8")
    def without_stamps(b):
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
    "near_home",
    "home_institution",
    "category",
    "tracks",
    "focus",
    "opens",
    "opens_status",
    "deadline",
    "deadline_status",
    "program_dates",
    "duration_weeks",
    "stipend_usd",
    "paid",
    "stipend_note",
    "housing",
    "selectivity",
    "min_gpa",
    "citizenship",
    "class_years",
    "requires",
    "url",
    "url_confidence",
    "contact",
    "notes",
]

# Excel and Sheets run a cell that starts with one of these as a formula, so a
# note pasted as "- confirm with the department" opens as #NAME?, and a hostile
# value could do worse. A leading apostrophe is the spreadsheet's own marker
# for "this is text".
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def opens_status_of(program):
    """The record's opens_status, or what an older record without one means."""
    return program.get("opens_status") or ("projected" if program.get("opens") else "unknown")


def csv_cell(value):
    if isinstance(value, bool):
        return "yes" if value else ""
    if not isinstance(value, str):
        return "" if value is None else value
    if value.startswith(FORMULA_START):
        value = "'" + value
    # The file is LF throughout, so a pasted CRLF inside a note goes too
    return value.replace("\r\n", "\n").replace("\r", "\n")


def mirror_to_site(path):
    """The site is deployed from site/ alone, so downloads must live beside it."""
    site_data = ROOT / "site" / "data"
    site_data.mkdir(parents=True, exist_ok=True)
    target = site_data / path.name
    target.write_bytes(path.read_bytes())
    return target


def write_csv(programs):
    buffer = io.StringIO()
    # LF like the other text files the site serves. The csv module's CRLF
    # default rewrote the committed LF file on every build.
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for program in programs:
        elig = program.get("eligibility") or {}
        row = {
            **program,
            "tracks": ", ".join(program.get("tracks", [])),
            "requires": ", ".join(program.get("requires", [])),
            "class_years": ", ".join(elig.get("class_years", [])),
            "min_gpa": elig.get("min_gpa") or "",
            "citizenship": elig.get("citizenship") or "",
            "opens_status": opens_status_of(program),
        }
        writer.writerow({column: csv_cell(row.get(column)) for column in CSV_COLUMNS})

    path = ROOT / "data" / "programs.csv"
    # utf-8-sig adds the BOM, which is what tells Excel the file is UTF-8
    write_stable(path, buffer.getvalue().encode("utf-8-sig"))
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


# RFC 5545 allows no control characters in TEXT but the tab
ICS_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def ics_escape(text):
    # Every line break becomes \n first. A bare CR used to go through raw,
    # and a parser that splits on CR then saw a line with no property name.
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    return (
        ICS_CONTROL.sub("", text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def morning_before(days):
    """TRIGGER for 9 a.m., `days` days before an all-day event.

    An all-day event starts at midnight, so a plain -P3D fired at midnight
    too, while she was asleep, and on a silenced phone it was buried by
    morning. Fifteen hours short of the whole days lands on 9 a.m. local.
    """
    return f"-P{days - 1}DT15H" if days > 1 else "-PT15H"


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
        # Left to itself a subscribed calendar polls when it likes, often a
        # day or more apart, so a date that moved reached her phone late.
        # REFRESH-INTERVAL is the standard hint; many clients read only the
        # older X-PUBLISHED-TTL.
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]

    def event(program, when, kind, summary, status, alarms):
        uid_seed = f"{program['id']}-{kind}".encode()
        uid = hashlib.sha1(uid_seed).hexdigest()[:20]
        start = when.strftime("%Y%m%d")
        end = (when + dt.timedelta(days=1)).strftime("%Y%m%d")
        body = [
            "BEGIN:VEVENT",
            f"UID:{uid}@jolene-s27",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{ics_escape(program['org'] + ', ' + program['city'] + '. Date status: ' + status + '. ' + program['url'])}",
            # A URI value takes no backslash escaping, so TEXT escaping put a
            # literal backslash into any link with a ; or a , in it.
            # validate() has already refused a link with a line break.
            f"URL:{program['url']}",
            f"CATEGORIES:{ics_escape(kind)}",
            # A deadline is a reminder, not an appointment. Left at the
            # default, OPAQUE, every one marked her busy for the whole day.
            "TRANSP:TRANSPARENT",
        ]
        for days, label in alarms:
            body += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"TRIGGER:{morning_before(days)}",
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
            status = program.get("deadline_status", "unknown")
            marker = "" if status == "confirmed" else " (est.)"
            lines += event(
                program,
                deadline,
                "deadline",
                f"DUE{marker}: {program['name']}, {program['org']}",
                status,
                [(14, "Two weeks out" + marker), (3, "Three days out" + marker)],
            )
            count += 1

        # Most opening dates are last cycle's carried forward, so only one
        # read off the program's own page goes in as fact. An alarm saying
        # "Opens tomorrow" for a guess reads as a promise the portal is up.
        if opens:
            status = opens_status_of(program)
            marker = "" if status == "confirmed" else " (est.)"
            lines += event(
                program,
                opens,
                "opens",
                f"Opens{marker}: {program['name']}, {program['org']}",
                status,
                [(1, "Opens tomorrow" + marker)],
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
        # Hash the normalized bytes. Git hands this file out with CRLF on
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
        # Bytes, so the page stays LF: write_text gives CRLF on Windows
        index.write_bytes(html.encode("utf-8"))
    return html != original


def main():
    programs, errors = load_sources()

    if errors:
        print("Validation problems:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        # Writing the records that did pass published a dataset with whole
        # categories missing (one stray comma drops a file) and left it on
        # disk ready to commit, so nothing is written until the sources are clean.
        print("Nothing was written.", file=sys.stderr)
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
    watch_summary.write(programs)
    stamp_assets()
    print(f"  wrote      : data/programs.json, site/data/programs.json")
    print(f"               {csv_path.relative_to(ROOT).as_posix()}")
    print(f"               {ics_path.relative_to(ROOT).as_posix()} ({event_count} events)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
