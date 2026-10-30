#!/usr/bin/env python3
"""Second confirmation pass, covering the programs added in the expansion.

Read off the official pages on 30 October 2026 via scripts/extract_dates.py,
with the surrounding sentence checked by hand in every case.

The Pritzker entry is the reason that hand-check is not optional. The page
advertises a 30 November 2026 deadline, which would have been the most urgent
item on the whole list — but the surrounding text ("Eligible students will
receive the electronic SRP application", "used by Pritzker students") makes
clear it is the University of Chicago's own MEDICAL STUDENT programme, not an
undergraduate one. Repointed at the Biological Sciences Division hub instead.

Safe to re-run.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"

UPDATES = {
    "md-anderson-summer": {
        "name": "CATALYST Summer Training Programs",
        "opens": "2026-11-16",
        "deadline": "2027-01-13",
        "deadline_status": "confirmed",
        "program_dates": "Jun 7 – Aug 13, 2027",
        "notes": (
            "CONFIRMED on the page: applications open 16 Nov 2026 and close 13 Jan 2027, "
            "programme runs 7 Jun – 13 Aug 2027. An informational webinar runs 19 Nov. "
            "Several tracks sit behind this one page — read it properly and pick the right one. "
            "Houston also has Baylor SMART and Texas Children's, so one city covers three applications."
        ),
    },
    "stanford-ssrp": {
        "opens": "2026-11-01",
        "deadline": "2027-02-01",
        "deadline_status": "confirmed",
        "program_dates": "Through Aug 14, 2027",
        "notes": (
            "This is the UNDERGRADUATE Stanford program. Not to be confused with SIMR, which is "
            "widely recommended online but is for high school students — worth knowing before "
            "wasting an application. CONFIRMED on the page: opens 1 Nov 2026, closes 1 Feb 2027, "
            "matching the Amgen Scholars date across all US hosts. Note the page labels the cycle "
            "\"2026 SSRP\" even though it is the summer 2027 intake."
        ),
    },
}

# The Pritzker page turned out to describe a medical-student programme.
REWRITES = {
    "uchicago-pritzker-srp": {
        "id": "uchicago-bsd",
        "name": "Biological Sciences Division — summer research",
        "org": "University of Chicago",
        "city": "Chicago, IL",
        "url": "https://biosciences.uchicago.edu/",
        "tracks": ["basic-science", "clinical", "translational"],
        "focus": "Biomedical research across the Biological Sciences Division, with Comer Children's Hospital for pediatric projects.",
        "duration_weeks": None,
        "stipend_usd": None,
        "housing": "varies",
        "opens": None,
        "deadline": None,
        "deadline_status": "unknown",
        "eligibility": {
            "class_years": ["sophomore", "junior"],
            "citizenship": "unspecified",
            "min_gpa": None,
            "notes": "",
        },
        "requires": ["cv", "personal-statement"],
        "selectivity": "high",
        "notes": (
            "CORRECTED: the Pritzker Summer Research Program page, with its 30 Nov 2026 deadline, "
            "is for the University of Chicago's own MEDICAL students — not undergraduates. Do not "
            "chase that date. UChicago is a Leadership Alliance member institution, so the SR-EIP "
            "application is the reliable undergraduate route in; this hub is the place to look for "
            "a direct lab contact. Comer Children's is the pediatric angle."
        ),
        "url_verified": True,
        "url_confidence": "medium",
    }
}


def main() -> int:
    for path in sorted(SOURCES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dirty = False

        for index, program in enumerate(payload.get("programs", [])):
            pid = program.get("id")

            if pid in UPDATES:
                for key, value in UPDATES[pid].items():
                    if program.get(key) != value:
                        program[key] = value
                        dirty = True

            if pid in REWRITES:
                payload["programs"][index] = REWRITES[pid]
                dirty = True

        if dirty:
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

    print(f"confirmed dates for {len(UPDATES)} programs")
    print(f"rewrote {len(REWRITES)} entry that was a medical-student program")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
