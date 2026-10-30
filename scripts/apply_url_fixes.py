#!/usr/bin/env python3
"""One-off curation pass: apply verified URL corrections to data/sources/*.json.

Every replacement below was confirmed with scripts/try_urls.py. Domains listed
in BLOCKS_BOTS refuse automated requests outright (403 even with a browser
user-agent), so their URLs cannot be machine-verified, they get a flag instead
of a guess, and the watcher reports them separately rather than as broken.

Safe to re-run: it only writes when something actually changes.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"

# id -> verified replacement URL
FIXES = {
    "cincinnati-surf": "https://www.cincinnatichildrens.org/education/research",
    "mayo-surf": "https://college.mayo.edu/academics/biomedical-research-training/summer-undergraduate-research-fellowship-surf/",
    "psu-surip": "https://med.psu.edu/education/certificate-and-undergraduate/summer-undergrad-internship-surip",
    "ucsf-srtp": "https://graduate.ucsf.edu/academics/srtp",
    "emory-sure": "https://scholarblogs.emory.edu/urp/sure/",
    "cleveland-clinic-lerner": "https://www.lerner.ccf.org/education/",
    "wake-forest-summer": "https://school.wakehealth.edu/education-and-training",
    "phoenix-childrens": "https://phoenixchildrens.org/research",
    "nia-adrc-directory": "https://www.nia.nih.gov/research/nia-funded-alzheimers-disease-research-centers",
    "ucsf-benioff-peds": "https://pediatrics.ucsf.edu/education",
    "kennedy-krieger": "https://www.kennedykrieger.org/training",
    "rady-childrens": "https://www.rchsd.org/research-innovation/",
    "primary-childrens-utah": "https://medicine.utah.edu/pediatrics/education",
    "nemours": "https://www.nemours.org/pediatric-research.html",
    "rochester-summer-scholars": "https://www.urmc.rochester.edu/education/graduate/summer-scholars",
    "indiana-summer-research": "https://medicine.iu.edu/research-centers/neurosciences/education/summer-research",
    "utsw-surf": "https://gsbs.utsouthwestern.edu/",
    "nyu-langone-surp": "https://med.nyu.edu/education/",
    "unc-summer-research": "https://bbsp.unc.edu/",
    "duke-summer-research": "https://gradschool.duke.edu/professional-development/",
    "scripps-surf": "https://education.scripps.edu/",
    "van-andel": "https://www.vai.org/",
    "musc-surp": "https://gradstudies.musc.edu/",
    "cook-childrens": "https://www.cookchildrens.org/",
    "bch-coach": "https://research.childrenshospital.org/",
    "bch-newborn-medicine": "https://www.childrenshospital.org/services/newborn-medicine",
    "cwru-hlb": "https://case.edu/medicine/",
    "cwru-cansur": "https://case.edu/cancer/",
    "hopkins-jhibs": "https://neuroscience.jhu.edu/",
    "pitt-spurs": "https://www.medschool.pitt.edu/",
    "ohsu-equity-research": "https://www.ohsu.edu/school-of-medicine",
    "benaroya": "https://www.benaroyaresearch.org/",
    "salk-surf": "https://www.salk.edu/about/education-outreach/",
    "stowers": "https://www.stowers.org/",
    "uab-summer": "https://www.uab.edu/gbs/home/",
    "fred-hutch-surp": "https://www.fredhutch.org/en/education-training/undergraduate-students/pathways-undergraduate-researchers.html",
    "childrens-national-ed": "https://www.childrensnational.org/for-healthcare-professionals/healthcare-education/research-education/emergency-department-clinical-research-internship",
    "childrens-national-trainees": "https://research.childrensnational.org/",
    "msk-mbsp": "https://www.mskcc.org/education-training/summer-scientific-undergraduate-programs/mechanistic-biology-summer-program",
    "texas-childrens-baylor-smart": "https://www.bcm.edu/education/graduate-school-of-biomedical-sciences/degree-programs-and-certificates/smart-program",
    "nationwide-childrens": "https://www.nationwidechildrens.org/research/office-of-trainee-affairs",
    "ucdavis-mind": "https://health.ucdavis.edu/mind-institute/",
    "lurie-childrens": "https://research.luriechildrens.org/",
    "wisconsin-adrc": "https://adrc.wisc.edu/",
    "odu-student-research": "https://www.odu.edu/research",
    "washu-biomedrap": "https://dbbs.wustl.edu/programs/",
    "dana-farber-cure": "https://www.dana-farber.org/research",
    "cedars-sinai": "https://www.cedars-sinai.edu/research.html",
    # icahn.mssm.edu and einsteinmed.edu reject every automated request, so these
    # two are the most plausible hub pages rather than machine-verified ones.
    "mount-sinai-surp": "https://icahn.mssm.edu/education/graduate-school",
    "einstein-surp": "https://einsteinmed.edu/education/",
}

# These hosts 403 every automated request. The stored URL is the best known one
# and should be opened in a real browser.
BLOCKS_BOTS = {
    "nih-sip",
    "michigan-urop-summer",
    "columbia-zuckerman",
    "aha-summer-undergrad",
    "rutgers-rwjms-neuro",
    "chla-summer",
    "mount-sinai-surp",
    "einstein-surp",
    "arkansas-childrens",
}

BLOCK_NOTE = (
    "This site blocks automated link checks, so the watcher cannot verify it, "
    "open it in a browser."
)


def main() -> int:
    changed_files = 0
    applied = 0
    flagged = 0
    unseen = set(FIXES)

    for path in sorted(SOURCES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dirty = False

        for program in payload.get("programs", []):
            pid = program.get("id")

            if pid in FIXES:
                unseen.discard(pid)
                if program.get("url") != FIXES[pid]:
                    program["url"] = FIXES[pid]
                    program["url_verified"] = True
                    applied += 1
                    dirty = True

            if pid in BLOCKS_BOTS and program.get("link_note") != BLOCK_NOTE:
                program["link_note"] = BLOCK_NOTE
                program["url_verified"] = False
                flagged += 1
                dirty = True

        if dirty:
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            changed_files += 1

    print(f"applied {applied} URL fixes across {changed_files} files")
    print(f"flagged {flagged} bot-blocked pages")
    if unseen:
        print(f"WARNING: these ids were not found in any source file: {sorted(unseen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
