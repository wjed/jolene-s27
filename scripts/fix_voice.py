#!/usr/bin/env python3
"""QA fix: rewrite user-facing copy from third person into second person.

The dataset was drafted as notes *about* the applicant. She is the one who
opens the site, so "she can apply to as many hosts as she likes" reads as if
she is being discussed rather than helped. Every rewrite below is hand-written;
a find/replace on pronouns produces broken grammar ("if she has" -> "if you has").

Safe to re-run.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"

NOTES = {
    "fred-hutch-surp": "PERFECT TIMING FIT: restricted to rising seniors, which is precisely your junior summer. The 2026 deadline was Jan 9. Fred Hutch said 2027 info posts in November. Early deadline — do it in the December block.",
    "indiana-summer-research": "Same institution as INSPIRE on your list — you may be able to be considered for several IU tracks at once. Worth asking the program coordinator.",
    "allen-institute": "Excellent pay. Leans computational — a good fit if you have any coding or data analysis background. Pairs with Seattle Children's for one city.",
    "amgen-scholars": "BEST VALUE PER UNIT OF EFFORT. You can apply to as many US hosts as you like, and much of the essay content is reusable across them. Applications open Nov 1, 2026. CONFIRMED on the page: Feb 1, 2027 for all US hosts.",
    "shpep": "Aimed at freshmen and sophomores, so almost certainly too early for a rising senior — listed so the set is honest about what exists. Skip it unless you want clinical exposure rather than research.",
    "harvard-shurp": "Requires prior lab experience — check you meet that bar before spending an application on it.",
    "pitt-spurs": "Pairs with UPMC Children's Hospital of Pittsburgh, also on your list — same city, two applications.",
    "scripps-surf": "Heavily chemistry-leaning — a fit only if you want molecular work rather than clinical.",
    "aha-summer-undergrad": "The Penn State AHA-USF on your list is one instance of this. Other institutions host their own AHA-funded versions — worth finding the one nearest you.",
    "nih-sip": "HIGHEST PRIORITY. One application reaches an enormous number of labs, and you can email individual PIs directly to improve your odds — that outreach is what actually gets people placed. The 2026 cycle closed Feb 18; 2027 is expected to open mid-November 2026 and close mid-February 2027. Verify at training.nih.gov/sip.",
    "rady-childrens": "A rare pediatric genomics angle, if that interests you.",
    "lebonheur-uthsc": "Same city as St. Jude. If you are applying to POE anyway, a direct email here costs nothing, and the pediatric epilepsy work overlaps with the Boston Children's lab on your list. Likely arranged by direct contact rather than a portal.",
    "nia-adrc-directory": "Not a program — a hunting ground. Pick the three centers nearest you and email the education coordinator at each. Most do not advertise undergraduate slots but will take a strong student who asks. The single highest-leverage move for an Alzheimer's interest.",
    "janelia-undergrad": "Small and very selective. Best fit if you have any computational or imaging leaning. Housing on campus is typically included.",
    "odu-student-research": "The weakest entry on your list unless you have an ODU connection — this is a general campus page, not a competitive national program.",
}

ELIGIBILITY_NOTES = {
    "fred-hutch-surp": "RISING SENIORS ONLY — you must be entering the summer before your final year of undergrad. That is exactly this year.",
    "cornell-travelers": "Must be at least a junior at the time of application and a declared pre-medical student. The program targets students from underserved racial and ethnic groups or socioeconomically disadvantaged backgrounds, and looks for demonstrated engagement with underserved communities — check whether you are eligible before spending time on it.",
}

# "the original list" is accurate but distant; it is her list.
SWAPS = [
    ("Flagged on the original list", "Flagged on your list"),
    ("on her original list", "on your list"),
    ("entry on the original list", "entry on your list"),
    ("the bare 'PROMISE' entry on the original list", "the bare 'PROMISE' entry on your list"),
    ("'Summer Biomedical Research Program' entry on the original list",
     "'Summer Biomedical Research Program' entry on your list"),
    ("the original list had the right one", "your list had the right one"),
]


def main() -> int:
    changed = 0

    for path in sorted(SOURCES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dirty = False

        for p in payload.get("programs", []):
            pid = p.get("id")

            if pid in NOTES and p.get("notes") != NOTES[pid]:
                p["notes"] = NOTES[pid]
                changed += 1
                dirty = True

            if pid in ELIGIBILITY_NOTES:
                elig = p.setdefault("eligibility", {})
                if elig.get("notes") != ELIGIBILITY_NOTES[pid]:
                    elig["notes"] = ELIGIBILITY_NOTES[pid]
                    changed += 1
                    dirty = True

            for field in ("notes", "focus"):
                text = p.get(field)
                if not text:
                    continue
                new = text
                for old, repl in SWAPS:
                    new = new.replace(old, repl)
                if new != text:
                    p[field] = new
                    changed += 1
                    dirty = True

        if dirty:
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"rewrote {changed} copy fields into second person")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
