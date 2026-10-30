#!/usr/bin/env python3
"""Curation pass: replace the two unidentified entries with the real programs,
and fold in URL corrections found while identifying them.

Both placeholders came from the original Notion list with no institution
attached. Identified and verified 30 October 2026:

  PROMISE  -> Penn State College of Medicine. The list entry sat directly beside
              another med.psu.edu link, and the URL slug matches that pattern.
              Official name is "...Inspire Student Engagement", not "Students".
  Summer Biomedical Research Program
           -> East Carolina University, Brody School of Medicine. The entry sat
              beside Old Dominion; both are in the same coastal VA/NC corridor.

Safe to re-run.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"

PSU_PROMISE = {
    "id": "psu-promise",
    "name": "PROMISE — Research Training in Oncology and Medicine to Inspire Student Engagement",
    "org": "Penn State College of Medicine / Penn State Cancer Institute",
    "city": "Hershey, PA",
    "url": "https://med.psu.edu/education/certificate-and-undergraduate/promise",
    "tracks": ["oncology", "basic-science", "translational"],
    "focus": "NCI-funded, team-based cancer research with weekly career-development sessions, ending in a poster symposium.",
    "duration_weeks": None,
    "stipend_usd": None,
    "housing": "varies",
    "opens": None,
    "deadline": "2027-01-31",
    "deadline_status": "projected",
    "eligibility": {
        "class_years": ["sophomore", "junior", "senior"],
        "citizenship": "unspecified",
        "min_gpa": None,
        "notes": "STEM majors who have completed at least two years of college — rising juniors and seniors. Engineering, computer science, statistics and biological sciences all count. Students underrepresented in the biomedical workforce are encouraged to apply.",
    },
    "requires": ["cv", "personal-statement"],
    "selectivity": "high",
    "notes": "IDENTIFIED: this was the bare 'PROMISE' entry on the original list — it is Penn State. That makes three Penn State programs on the list (SURIP, AHA-USF, PROMISE), all at Hershey. Worth asking the coordinators whether one application can be considered for more than one. Listed deadline is 'late January' on a third-party listing, so confirm it.",
    "url_verified": True,
    "url_confidence": "high",
}

ECU_SBRP = {
    "id": "ecu-sbrp",
    "name": "Summer Biomedical Research Program (SBRP)",
    "org": "East Carolina University — Brody School of Medicine",
    "city": "Greenville, NC",
    "url": "https://medicine.ecu.edu/sbrp/",
    "tracks": ["basic-science", "translational"],
    "focus": "Basic science research at the Brody School of Medicine and ECU Health, with lab safety training and career workshops.",
    "duration_weeks": 9,
    "stipend_usd": None,
    "housing": "varies",
    "opens": None,
    "deadline": "2027-02-13",
    "deadline_status": "projected",
    "eligibility": {
        "class_years": ["sophomore", "junior"],
        "citizenship": "unspecified",
        "min_gpa": None,
        "notes": "Undergraduates. An older ECU document describes the program as targeting students from underrepresented, low-socioeconomic or rural backgrounds — confirm current rules on the page.",
    },
    "requires": ["transcript", "cv", "personal-statement"],
    "selectivity": "moderate",
    "notes": "IDENTIFIED: this was the bare 'Summer Biomedical Research Program' entry on the original list. The 2026 cycle closed 13 February and the 2025 cohort ran 27 May - 25 July. Smaller applicant pool than the national programs, and regionally adjacent to the Old Dominion entry.",
    "url_verified": True,
    "url_confidence": "high",
}

REPLACE = {
    "unidentified-promise": PSU_PROMISE,
    "unidentified-summer-biomed": ECU_SBRP,
}

# Better URLs surfaced while running the searches above.
URL_FIXES = {
    "nyu-langone-surp": "https://med.nyu.edu/research/vilcek-institute-graduate-biomedical-sciences/summer-undergraduate-research-program",
    "mount-sinai-surp": "https://icahn.mssm.edu/education/non-degree/surp4us",
}


def main() -> int:
    replaced = 0
    fixed = 0

    for path in sorted(SOURCES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dirty = False

        for index, program in enumerate(payload.get("programs", [])):
            pid = program.get("id")

            if pid in REPLACE:
                payload["programs"][index] = REPLACE[pid]
                replaced += 1
                dirty = True
                continue

            if pid in URL_FIXES and program.get("url") != URL_FIXES[pid]:
                program["url"] = URL_FIXES[pid]
                # icahn.mssm.edu refuses robots, so this one still cannot be
                # machine-verified even though it is now the right address.
                program["url_confidence"] = "medium" if pid == "mount-sinai-surp" else "high"
                if pid != "mount-sinai-surp":
                    program["url_verified"] = True
                    program.pop("link_note", None)
                fixed += 1
                dirty = True

        if dirty:
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

    print(f"replaced {replaced} placeholder entries")
    print(f"corrected {fixed} URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
