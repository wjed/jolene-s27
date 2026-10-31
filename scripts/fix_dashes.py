#!/usr/bin/env python3
"""Replace em dashes with ordinary punctuation across the project.

A blanket swap to " - " reads just as mechanical as the em dash did, so each
occurrence is resolved by what follows it:

    " - and/but/so/or ..."      -> comma, the clause is being joined
    " - check it on the page"   -> full stop, an imperative sentence follows
    " - it is Penn State"       -> full stop, an independent clause follows
    "Housing - provided"        -> colon, a short label introduces its value
    everything else             -> comma, an appositive or elaboration

En dashes in numeric and date ranges become plain hyphens at the same time.

Two safety rules, both learned the hard way:

  * JSON is edited through the parser, never as raw text, so structure and
    escaping cannot be disturbed.
  * No tidy-up pattern may match across a newline. An earlier version used
    \\s+ before punctuation, which collapsed Python indentation preceding a
    colon and ate JavaScript spread operators.

Safe to re-run.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
EM = chr(8212)  # by code point: this file must not contain one
EN = chr(8211)

JSON_TARGETS = ["data/sources/*.json"]
TEXT_TARGETS = [
    "materials/*.md",
    "materials/*/*.md",
    "site/assets/app.js",
    "site/index.html",
    "README.md",
    "data/README.md",
    "scripts/*.py",
]

CONJUNCTIONS = ("and", "but", "so", "or", "yet", "then", "which", "though")

SENTENCE_STARTERS = (
    "check", "open", "verify", "do ", "use ", "pick", "start", "read", "skip",
    "ask", "confirm", "send", "name ", "say ", "write", "treat", "make", "keep",
    "go ", "email", "apply", "look", "watch", "find", "submit", "log ", "thank",
    "it is", "it was", "this is", "that is", "they are", "there is", "there are",
    "you are", "you can", "you have", "most ", "both ", "nothing ", "every ",
    "expect ", "budget ", "note ", "listed ", "half ", "one application",
)

LABELLY = re.compile(r"(\*\*[^*]+\*\*|[A-Z][A-Za-z0-9&().,'/ ]{0,40})$")

# horizontal whitespace only: never newlines
H = r"[^\S\n]"


def choose(before: str, after: str) -> str:
    nxt = after.lstrip()
    low = nxt.lower()

    if any(low.startswith(c + " ") for c in CONJUNCTIONS):
        return ", "
    if any(low.startswith(s) for s in SENTENCE_STARTERS):
        return ". "

    tail = before.rstrip()
    if tail.endswith("**") or (
        len(tail) <= 46 and LABELLY.search(tail) and not tail.endswith((".", "!", "?"))
    ):
        return ": "
    return ", "


def convert(text: str) -> str:
    """Replace every em dash, then tidy up without ever crossing a line break."""
    # a dash plus the horizontal space around it, newlines left alone
    pattern = re.compile(H + r"*" + re.escape(EM) + H + r"*")

    while True:
        m = pattern.search(text)
        if not m:
            break
        punct = choose(text[: m.start()], text[m.end():])
        rest = text[m.end():]
        if punct == ". " and rest[:1].islower():
            rest = rest[0].upper() + rest[1:]
        text = text[: m.start()] + punct + rest

    # ranges keep their shape: "4-6 courses", "May 24 - Jul 31"
    text = re.sub(H + r"+" + re.escape(EN) + H + r"+", " - ", text)
    text = text.replace(EN, "-")

    # single-line tidy-ups only
    text = re.sub(r",(" + H + r"*),", ",", text)
    text = re.sub(r":(" + H + r"*):", ":", text)
    text = re.sub(r",(" + H + r"*)\.", ".", text)
    text = re.sub(r"([,.:;])" + H + r"{2,}", r"\1 ", text)
    return text


def walk(value):
    if isinstance(value, str):
        return convert(value)
    if isinstance(value, list):
        return [walk(v) for v in value]
    if isinstance(value, dict):
        return {k: walk(v) for k, v in value.items()}
    return value


def main() -> int:
    changed = []

    for pattern in JSON_TARGETS:
        for path in sorted(ROOT.glob(pattern)):
            data = json.loads(path.read_text(encoding="utf-8"))
            updated = walk(data)
            blob = json.dumps(updated, indent=2, ensure_ascii=False) + "\n"
            if blob != path.read_text(encoding="utf-8"):
                path.write_text(blob, encoding="utf-8")
                changed.append(path.relative_to(ROOT).as_posix())

    for pattern in TEXT_TARGETS:
        for path in sorted(ROOT.glob(pattern)):
            if path.name == "fix_dashes.py":
                continue  # this file documents the characters it removes
            original = path.read_text(encoding="utf-8")
            if EM not in original and EN not in original:
                continue
            updated = convert(original)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed.append(path.relative_to(ROOT).as_posix())

    for name in changed:
        print("  " + name)
    print(f"\nrewrote {len(changed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
