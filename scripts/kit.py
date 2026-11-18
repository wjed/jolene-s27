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
     "Every fact a form might ask for. Claude fills it in with you once; after that, attach your latest copy to every chat."),
    ("skills/fill-application/SKILL.md", "\U0001F5A5", "fill-application skill",
     "Fills an application form in the browser from your profile, and stops at anything it should not answer alone."),
    ("skills/email-a-lab/SKILL.md", "\U0001F4E7", "email-a-lab skill",
     "Researches a lab, then drafts a short specific email to the professor. The highest-return thing almost nobody does."),
    ("skills/watch-deadlines/SKILL.md", "⏰", "watch-deadlines skill",
     "What opened, what changed and what is due soon, read from this site's weekly check."),
    ("README.md", "\U0001F4D6", "README.md",
     "How to put the kit together, in five minutes."),
]


def build() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    files, entries = [], []
    for rel, icon, title, blurb in MANIFEST:
        src = KIT / rel
        if not src.is_file():
            print(f"  ! missing {rel}")
            continue
        # Git checks these out with CRLF on Windows and LF in CI. Published as
        # they sat on disk, the same kit had a different size and a different
        # zip depending on who built it, and each build undid the other's.
        data = src.read_bytes().replace(b"\r\n", b"\n")
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        entries.append((rel, data))
        files.append({
            "path": "kit/" + rel,
            "name": title,
            "icon": icon,
            "blurb": blurb,
            "bytes": len(data),
        })

    archive = OUT / "jolene-claude-kit.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for rel, data in entries:
            # Every field fixed, so the zip is a function of the files alone.
            # zf.write() stamped each entry with its file's mtime, and ZipInfo
            # records the building OS. Stored rather than deflated, because
            # compressed bytes vary with the zlib Python was built against, and
            # the whole kit is a few dozen KB of text.
            info = zipfile.ZipInfo("jolene-claude-kit/" + rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3  # Unix, so the permission bits below are read
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)

    payload = {
        "zip": "kit/jolene-claude-kit.zip",
        "zip_bytes": archive.stat().st_size,
        "files": files,
    }
    out = ROOT / "site" / "data" / "kit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Bytes, so the file is LF on every machine: write_text gives CRLF on Windows
    out.write_bytes((json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return payload


def write() -> int:
    payload = build()
    print(f"  kit        : {len(payload['files'])} files + zip "
          f"({payload['zip_bytes']:,} bytes) -> site/kit/")
    return len(payload["files"])


if __name__ == "__main__":
    write()
