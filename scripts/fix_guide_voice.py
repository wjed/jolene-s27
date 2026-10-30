#!/usr/bin/env python3
"""QA fix: rewrite materials/*.md from third person into second person.

The guides render as pages on the site, so the person reading them is the
applicant herself. Notes written *about* her ("if she has a conflict") read
badly when she is the one reading them.

Phrase rules, not a pronoun swap: "she has" must become "you have", and "her"
is possessive in "her control" but an object in "rule her out". Rules match
across line breaks, because these files are hard-wrapped and a pronoun
routinely sits at the end of one line with its verb at the start of the next.

The check at the end fails the run on anything missed or mangled.

Safe to re-run.
"""

from __future__ import annotations

import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
MATERIALS = ROOT / "materials"

# Ordered: the specific rules have to win over the general ones.
RULES: list[tuple[str, str]] = [
    ("only Jolene can fill in", "only you can fill in"),
    ("she has saved herself a summer", "you have saved yourself a summer"),
    ("check hers specifically", "check yours specifically"),
    ("genuinely hers to tell", "genuinely yours to tell"),
    ("SHOWS SHE READ IT", "SHOWS YOU READ IT"),
    ("[What SHE did", "[What YOU did"),
    ("[HER OWN EXPERIENCE]", "[YOUR OWN EXPERIENCE]"),

    # possessive "her" + noun
    ("within her control", "within your control"),
    ("If her research experience is light", "If your research experience is light"),
    ("or her problem", "or your problem"),
    ("her own university's", "your own university's"),
    ("seen her work in a lab", "seen you work in a lab"),
    ("she submits her part", "you submit your part"),
    ("this is her last summer", "this is your last summer"),
    ("If her experience is thin", "If your experience is thin"),

    # object "her"
    ("stop her spending", "stop you spending"),
    ("supervised her beats", "supervised you beats"),
    ("taught her in a lecture", "taught you in a lecture"),
    ("has watched her work", "has watched you work"),
    ("has watched her", "has watched you"),
    ("rule her out", "rule you out"),
    ("available to her", "available to you"),
    ("surprised her", "surprised you"),
    ("bore her", "bore you"),
    ("help her decide", "help you decide"),
    ("pick her out of a crowd", "pick you out of a crowd"),
    ("interests her", "interests you"),
    ("draws her", "draws you"),
    ("an argument *for* her here", "an argument *for* you here"),

    # she + verb: the third-person -s has to go
    ("she seriously wants", "you seriously want"),
    ("she genuinely wants", "you genuinely want"),
    ("she can", "you can"),
    ("she has", "you have"),
    ("she is", "you are"),
    ("she was", "you were"),
    ("she wants", "you want"),
    ("she finds", "you find"),
    ("she starts", "you start"),
    ("she asks", "you ask"),
    ("she never sees", "you never see"),
    ("she could", "you could"),
    ("she would", "you would"),

    # she + past tense: verb unchanged
    ("she spoke", "you spoke"),
    ("she ran", "you ran"),
    ("she handled", "you handled"),
    ("she did not get", "you did not get"),
    ("she did", "you did"),
    ("she owned", "you owned"),
    ("she contributed", "you contributed"),
    ("she worked", "you worked"),
    ("she came", "you came"),
    ("she emailed", "you emailed"),
    ("she read", "you read"),

    # agreement left behind when an earlier rule fixed half a sentence
    ("you ask early and makes it easy", "you ask early and make it easy"),
]

WORD = re.compile(r"[A-Za-z0-9]")
LEFTOVER = re.compile(r"\b(she|her|hers|herself|Jolene)\b", re.I)
BROKEN = re.compile(
    r"\byou (has|is|was|wants|finds|does|needs|gets|asks|starts|makes|seems|takes|"
    r"writes|sends|reads|knows|says|comes|runs|owns|submits|spends)\b",
    re.I,
)


def apply_rule(text: str, old: str, new: str) -> str:
    """Apply a phrase rule across line breaks without destroying the wrapping.

    Every inter-word gap becomes a capture group that is put back verbatim, so
    hard wraps and hanging indents survive the rewrite.
    """
    old_parts = old.split(" ")
    new_parts = new.split(" ")
    if len(old_parts) != len(new_parts):
        return text.replace(old, new)

    lead = r"\b" if WORD.match(old[:1]) else ""
    tail = r"\b" if WORD.match(old[-1:]) else ""
    pattern = lead + r"(\s+)".join(re.escape(p) for p in old_parts) + tail

    repl = new_parts[0]
    for index, part in enumerate(new_parts[1:], start=1):
        repl += "\\" + str(index) + part

    return re.sub(pattern, repl, text)


def main() -> int:
    rewritten = 0
    problems: list[str] = []

    for path in sorted(MATERIALS.rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        text = original
        for old, new in RULES:
            text = apply_rule(text, old, new)

        if text != original:
            path.write_text(text, encoding="utf-8")
            rewritten += 1

        rel = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(text.split("\n"), 1):
            for m in LEFTOVER.finditer(line):
                problems.append(f"{rel}:{number} leftover {m.group(0)!r}, {line.strip()[:88]}")
            for m in BROKEN.finditer(line):
                problems.append(f"{rel}:{number} agreement {m.group(0)!r}, {line.strip()[:88]}")

    print(f"rewrote {rewritten} file(s)")
    if problems:
        print(f"\n{len(problems)} issue(s) still need a rule:")
        for p in problems:
            print("  " + p)
        return 1

    print("no leftovers, no agreement errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
