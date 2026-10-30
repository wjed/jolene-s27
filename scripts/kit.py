#!/usr/bin/env python3
"""Publish claude-kit/ to the site: individual files plus a single zip.

She should be able to grab everything in one click, or pick off one skill if
that is all she wants. Both paths come from the same source folder, so they
cannot drift.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
KIT = ROOT / "claude-kit"
OUT = ROOT / "site" / "kit"

# Order shown on the page.
MANIFEST = [
    ("CLAUDE.md", "\U0001F4CB", "CLAUDE.md",
     "Who you are, what you are applying to, and how you want Claude to help. Attach this every time."),
    ("jolene-profile.md", "\U0001F9FE", "jolene-profile.md",
     "Every fact a form might ask for. Fill in the blanks once, then never retype your address again."),
    ("skills/fill-application/SKILL.md", "\U0001F5A5", "fill-application skill",
     "Fills an application form in the browser from your profile, and stops at anything it should not answer alone."),
    ("skills/email-a-lab/SKILL.md", "\U0001F4E7", "email-a-lab skill",
     "Researches a lab, then drafts a short specific email to the professor. The highest-return thing almost nobody does."),
    ("skills/watch-deadlines/SKILL.md", "⏰", "watch-deadlines skill",
     "A weekly scheduled check of which programs have posted their 2027 dates."),
    ("README.md", "\U0001F4D6", "README.md",
     "How to put the kit together, in five minutes."),
]


def build() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    files = []
    for rel, icon, title, blurb in MANIFEST:
        src = KIT / rel
        if not src.is_file():
            print(f"  ! missing {rel}")
            continue
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        files.append({
            "path": "kit/" + rel,
            "name": title,
            "icon": icon,
            "blurb": blurb,
            "bytes": src.stat().st_size,
        })

    archive = OUT / "jolene-claude-kit.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, *_ in MANIFEST:
            src = KIT / rel
            if src.is_file():
                zf.write(src, "jolene-claude-kit/" + rel)

    payload = {
        "zip": "kit/jolene-claude-kit.zip",
        "zip_bytes": archive.stat().st_size,
        "files": files,
    }
    (ROOT / "site" / "data" / "kit.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def write() -> int:
    payload = build()
    print(f"  kit        : {len(payload['files'])} files + zip "
          f"({payload['zip_bytes']:,} bytes) -> site/kit/")
    return len(payload["files"])


if __name__ == "__main__":
    write()
