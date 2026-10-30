#!/usr/bin/env python3
"""Curation pass: promote dates that are now posted on the programs' own pages.

Every change below was read off the official page on 30 October 2026 via
scripts/extract_dates.py, and the surrounding sentence was checked by hand
before anything was marked "confirmed". Program pages publish plenty of dates
that are not deadlines — Van Andel's 2027 dates turned out to be fundraising
galas — so a bare date match was never enough.

Safe to re-run.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"

# id -> fields to merge. deadline_status "confirmed" means the deadline sentence
# was read on the program's own page.
UPDATES = {
    "psu-promise": {
        "opens": "2026-12-01",
        "deadline": "2027-01-31",
        "deadline_status": "confirmed",
        "program_dates": "May 24 – Jul 31, 2027",
    },
    "psu-aha-usf": {
        "opens": "2026-12-01",
        "deadline": "2027-02-15",
        "deadline_status": "confirmed",
        "program_dates": "May 24 – Jul 27, 2027",
    },
    "psu-surip": {
        "opens": "2026-12-01",
        "deadline": "2027-02-01",
        "deadline_status": "confirmed",
        "program_dates": "May 24 – Jul 31, 2027",
    },
    "amgen-scholars": {
        "opens": "2026-11-01",
        "deadline": "2027-02-01",
        "deadline_status": "confirmed",
        "program_dates": "Varies by host, roughly May 17 – Aug 27, 2027",
    },
    "msk-mbsp": {
        "opens": "2026-11-02",
        "deadline": "2027-02-01",
        "deadline_status": "confirmed",
        "program_dates": "Jun 1 – Aug 6, 2027",
    },
    "leadership-alliance-sreip": {
        "deadline": "2027-02-03",
        "deadline_status": "confirmed",
    },
    "ucsf-srtp": {
        "opens": "2026-11-01",
        "deadline": "2027-02-01",
        "deadline_status": "confirmed",
        "program_dates": "May 30 – Aug 7, 2027",
    },
    "nyu-langone-surp": {
        "deadline": "2027-02-02",
        "deadline_status": "confirmed",
        "program_dates": "Jun 1 – Jul 30, 2027",
    },
    "yale-child-study": {
        "opens": "2026-12-01",
        "deadline": "2027-01-14",
        "deadline_status": "confirmed",
    },
    "vanderbilt-vssa": {
        "opens": "2026-11-01",
        "deadline": "2027-02-01",
        "deadline_status": "confirmed",
        "program_dates": "Through Aug 6, 2027",
    },
    "mayo-surf": {
        "opens": "2026-11-01",
        "deadline": "2027-02-03",
        "deadline_status": "confirmed",
        "program_dates": "Jun 1 – Aug 6, 2027",
    },
    # Opening date posted; the 2027 deadline itself is not up yet.
    "ecu-sbrp": {
        "opens": "2026-11-02",
        "program_dates": "May 24 – Jul 23, 2027",
    },
    # Program dates posted, no deadline yet.
    "mit-msrp": {"program_dates": "Jun 7 – Aug 7, 2027"},
    "texas-childrens-baylor-smart": {"program_dates": "Jun 7 – Aug 6, 2027"},
}

# Appended to the existing note rather than replacing it.
NOTE_ADDITIONS = {
    "yale-child-study": "CONFIRMED on the page: opens Dec 1, 2026, closes Jan 14, 2027 at 5pm ET. That is far earlier than the February cluster — it is one of the first deadlines in the whole cycle.",
    "vanderbilt-vssa": "CONFIRMED on the page: applications open Nov 1, 2026 and close between Jan 16 and Feb 15, 2027 depending on the track, with most on Feb 1. Check the specific track's date — the earliest is Jan 16.",
    "leadership-alliance-sreip": "CONFIRMED on the page: Feb 3, 2027, and the deadline covers the whole package including two letters and official transcripts.",
    "msk-mbsp": "CONFIRMED on the page: portal opens Nov 2, 2026 and closes Feb 1, 2027 at 8:00 a.m. — a morning cutoff, not end of day.",
    "ecu-sbrp": "The 2027 cycle opens Nov 2, 2026 and runs May 24 – Jul 23, 2027. The 2027 deadline is not posted yet; the 2026 cycle closed Feb 13.",
    "nyu-langone-surp": "CONFIRMED on the page: Feb 2, 2027 at 5 p.m.",
    "ucsf-srtp": "CONFIRMED on the page: opens Nov 1, 2026, closes Feb 1, 2027 at 11:59 p.m.",
    "mayo-surf": "CONFIRMED on the page: application window Nov 1, 2026 – Feb 3, 2027.",
}

# Corrections where the page said something different from what was assumed.
REWRITES = {
    "childrens-national-ed": {
        "name": "Emergency Department Clinical Research Internship",
        "deadline": None,
        "opens": None,
        "deadline_status": "unknown",
        "duration_weeks": None,
        "program_dates": None,
        "notes": (
            "CORRECTION: the posted cycle is a FALL-SPRING internship (Sept 13, 2026 – May 15, 2027) "
            "whose deadline was Aug 10, 2026 and has passed — not a summer program. 15 hours/week onsite, "
            "ten interns taken. Real pediatric emergency-medicine patient contact, which is rare and valuable, "
            "so it is worth emailing to ask whether a summer 2027 session runs and when it opens. "
            "Do not plan the summer around this one."
        ),
        "eligibility": {
            "class_years": ["sophomore", "junior", "senior"],
            "citizenship": "unspecified",
            "min_gpa": None,
            "notes": "Roughly 15 hours/week onsite during the fall-spring session.",
        },
    },
}


def main() -> int:
    touched = 0

    for path in sorted(SOURCES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dirty = False

        for program in payload.get("programs", []):
            pid = program.get("id")

            if pid in UPDATES:
                for key, value in UPDATES[pid].items():
                    if program.get(key) != value:
                        program[key] = value
                        dirty = True

            if pid in NOTE_ADDITIONS:
                addition = NOTE_ADDITIONS[pid]
                existing = program.get("notes", "") or ""
                if addition not in existing:
                    program["notes"] = (existing + " " + addition).strip()
                    dirty = True

            if pid in REWRITES:
                for key, value in REWRITES[pid].items():
                    if value is None and key in program:
                        program.pop(key)
                        dirty = True
                    elif value is not None and program.get(key) != value:
                        program[key] = value
                        dirty = True

            if dirty:
                touched += 1

        if dirty:
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

    print(f"updated {len(UPDATES)} programs with posted 2027 dates")
    print(f"rewrote {len(REWRITES)} entry that described the wrong cycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
