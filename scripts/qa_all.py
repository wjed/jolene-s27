#!/usr/bin/env python3
"""Repo-level QA: everything the browser suite cannot reach.

site/qa.js checks the running page. This checks the things underneath it:
that every script still compiles, that the workflows are well formed and
reference commands that exist, that a build is deterministic, that the
published copies match their sources, that the exports parse, and that the
asset hashes in the HTML match the files they name.

    python scripts/qa_all.py

Exit code is the number of failures.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS: list[tuple[str, bool, str]] = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), "" if cond else str(detail)))


def section(title):
    RESULTS.append((f"__{title}__", True, ""))


# ------------------------------------------------------------------ scripts

def qa_scripts():
    section("scripts and syntax")
    import ast

    for path in sorted((ROOT / "scripts").glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
            check(f"compiles: {path.name}", True)
        except SyntaxError as exc:
            check(f"compiles: {path.name}", False, f"line {exc.lineno}: {exc.msg}")

    for rel in ("site/assets/app.js", "site/qa.js"):
        path = ROOT / rel
        try:
            out = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True, timeout=60)
            check(f"parses: {rel}", out.returncode == 0, out.stderr.strip()[:160])
        except Exception as exc:  # node missing is itself worth knowing
            check(f"parses: {rel}", False, str(exc)[:120])

    css = (ROOT / "site/assets/styles.css").read_text(encoding="utf-8")
    check("css braces balance", css.count("{") == css.count("}"), f"{css.count('{')} open, {css.count('}')} close")
    check("css has no stray media nesting", not re.search(r",\s*\n\s*@media", css))

    html = (ROOT / "site/index.html").read_text(encoding="utf-8")
    for tag in ("html", "head", "body", "aside", "main", "nav"):
        check(f"html tag balanced: {tag}",
              len(re.findall(rf"<{tag}\b", html)) == len(re.findall(rf"</{tag}>", html)),
              f"{len(re.findall(rf'<{tag}' + r'\b', html))} open")


# ---------------------------------------------------------------- workflows

def qa_workflows():
    section("github workflows")
    wf_dir = ROOT / ".github/workflows"
    files = sorted(wf_dir.glob("*.yml"))
    check("workflows present", len(files) == 2, [f.name for f in files])

    for path in files:
        text = path.read_text(encoding="utf-8")
        check(f"{path.name}: has name", text.lstrip().startswith("name:"))
        check(f"{path.name}: has trigger", re.search(r"^on:", text, re.M) is not None)
        check(f"{path.name}: has jobs", re.search(r"^jobs:", text, re.M) is not None)
        check(f"{path.name}: no tabs", "\t" not in text, "tabs break yaml")
        try:
            import yaml  # optional
            data = yaml.safe_load(text)
            check(f"{path.name}: parses as yaml", isinstance(data, dict) and "jobs" in data)
        except ImportError:
            pass

        # every script a workflow runs must exist
        for ref in re.findall(r"python (scripts/[\w_]+\.py)", text):
            check(f"{path.name}: runs real script {ref}", (ROOT / ref).is_file(), ref)
        # every file it writes back must exist
        for ref in re.findall(r"git add ([\w/\.\- ]+)", text):
            for one in ref.split():
                check(f"{path.name}: commits real file {one}", (ROOT / one).is_file(), one)

    watch = (wf_dir / "watch.yml").read_text(encoding="utf-8")
    check("watcher is scheduled", "cron:" in watch)
    check("watcher may write", "contents: write" in watch)
    check("watcher may open issues", "issues: write" in watch)
    check("watcher tolerates nonzero exit", "set +e" in watch, "a findings exit code would fail the job")
    check("watcher issue has a fallback label path", watch.count("gh issue create") >= 2)

    pages = (wf_dir / "pages.yml").read_text(encoding="utf-8")
    check("pages builds before deploy", pages.index("scripts/build.py") < pages.index("upload-pages-artifact"))
    check("pages uploads the site dir", re.search(r"path:\s*site", pages) is not None)


# ------------------------------------------------------------------- build

def qa_build():
    section("build")
    before = {p: p.read_bytes() for p in sorted((ROOT / "site" / "data").glob("*")) if p.is_file()}
    out = subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    check("build succeeds", out.returncode == 0, out.stderr.strip()[-200:])

    # a second build must produce byte-identical output
    after = {p: p.read_bytes() for p in sorted((ROOT / "site" / "data").glob("*")) if p.is_file()}
    drifted = [p.name for p in before if p in after and before[p] != after[p] and p.name != "programs.json"]
    # programs.json carries a generated timestamp, so compare it without that
    if (ROOT / "site/data/programs.json") in before:
        strip = lambda b: re.sub(rb'"generated": "[^"]*"', b'', b)
        if strip(before[ROOT / "site/data/programs.json"]) != strip(after[ROOT / "site/data/programs.json"]):
            drifted.append("programs.json (beyond timestamp)")
    check("build is deterministic", not drifted, drifted)

    # published copies must match their sources
    for name in ("programs.csv", "deadlines.ics"):
        a, b = ROOT / "data" / name, ROOT / "site/data" / name
        check(f"site copy matches source: {name}", a.read_bytes() == b.read_bytes())

    # asset hashes in the HTML must match the files
    html = (ROOT / "site/index.html").read_text(encoding="utf-8")
    for rel in ("assets/styles.css", "assets/app.js"):
        m = re.search(re.escape(rel) + r"\?v=([0-9a-f]+)", html)
        check(f"asset is versioned: {rel}", m is not None)
        if m:
            actual = hashlib.sha1((ROOT / "site" / rel).read_bytes()).hexdigest()[:8]
            check(f"asset hash is current: {rel}", m.group(1) == actual, f"html={m.group(1)} file={actual}")


# ------------------------------------------------------------------ outputs

def qa_outputs():
    section("generated outputs")
    data = json.loads((ROOT / "data/programs.json").read_text(encoding="utf-8"))
    programs = data["programs"]

    ids = [p["id"] for p in programs]
    check("ids are unique", len(ids) == len(set(ids)), len(ids) - len(set(ids)))
    check("count matches list", data["count"] == len(programs))

    confirmed = [p for p in programs if p["deadline_status"] == "confirmed"]
    check("every confirmed date has a deadline", all(p.get("deadline") for p in confirmed))
    check("confirmed count is 16", len(confirmed) == 16, len(confirmed))

    # csv
    raw = (ROOT / "data/programs.csv").read_bytes()
    check("csv has excel BOM", raw[:3] == b"\xef\xbb\xbf")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    check("csv row count matches", len(rows) == len(programs), f"{len(rows)} vs {len(programs)}")
    check("csv has no empty names", all(r["name"] for r in rows))
    check("csv urls all absolute", all(r["url"].startswith("http") for r in rows))

    # ics
    ics = (ROOT / "data/deadlines.ics").read_bytes()
    text = ics.decode("utf-8")
    check("ics starts correctly", text.startswith("BEGIN:VCALENDAR\r\n"))
    check("ics has no doubled CRLF", b"\r\r\n" not in ics)
    check("ics folds long lines", all(len(l.encode()) <= 75 for l in text.split("\r\n")))
    check("ics events balanced", text.count("BEGIN:VEVENT") == text.count("END:VEVENT"))
    check("ics alarms balanced", text.count("BEGIN:VALARM") == text.count("END:VALARM"))
    expected = sum(1 for p in programs if p.get("opens")) + sum(1 for p in programs if p.get("deadline"))
    check("ics covers every date", text.count("BEGIN:VEVENT") == expected,
          f"{text.count('BEGIN:VEVENT')} vs {expected}")

    # guides html structure
    guides = json.loads((ROOT / "site/data/guides.json").read_text(encoding="utf-8"))["guides"]
    check("nine guides", len(guides) == 9, len(guides))
    for g in guides:
        h = g["html"]
        for tag in ("p", "ul", "ol", "li", "table", "blockquote", "pre"):
            opens = len(re.findall(rf"<{tag}[\s>]", h))
            closes = len(re.findall(rf"</{tag}>", h))
            if opens != closes:
                check(f"guide tags balanced: {g['slug']}/{tag}", False, f"{opens} open, {closes} close")
        check(f"guide has content: {g['slug']}", len(h) > 400)
        check(f"guide has no raw markdown: {g['slug']}", "**" not in h and "](" not in h)


# --------------------------------------------------------------------- kit

def qa_kit():
    section("claude kit")
    kit = ROOT / "claude-kit"
    z = zipfile.ZipFile(ROOT / "site/kit/jolene-claude-kit.zip")
    check("zip is valid", z.testzip() is None)
    names = z.namelist()
    check("zip has six files", len(names) == 6, len(names))

    # zip contents must match the sources byte for byte
    mismatched = []
    for n in names:
        src = kit / n.replace("jolene-claude-kit/", "")
        if not src.is_file():
            mismatched.append(n + " (missing source)")
        elif z.read(n) != src.read_bytes():
            mismatched.append(n + " (differs)")
    check("zip matches sources", not mismatched, mismatched)

    # published loose files must match too
    kj = json.loads((ROOT / "site/data/kit.json").read_text(encoding="utf-8"))
    bad = [f["path"] for f in kj["files"] if not (ROOT / "site" / f["path"]).is_file()]
    check("every listed kit file exists", not bad, bad)

    for skill in sorted(kit.glob("skills/*/SKILL.md")):
        fm = re.match(r"^---\n(.*?)\n---\n", skill.read_text(encoding="utf-8"), re.S)
        check(f"skill frontmatter: {skill.parent.name}", fm is not None)
        if fm:
            name = re.search(r"^name:\s*(\S+)", fm.group(1), re.M)
            check(f"skill name matches folder: {skill.parent.name}",
                  name and name.group(1) == skill.parent.name, name.group(1) if name else None)


# ------------------------------------------------------------------- prose

def qa_prose():
    section("prose and house style")
    EM, EN = "—", "–"
    targets = (list((ROOT / "materials").rglob("*.md")) + list((ROOT / "claude-kit").rglob("*.md"))
               + list((ROOT / "site").rglob("*.json")) + [ROOT / "README.md", ROOT / "site/index.html",
                                                          ROOT / "site/assets/app.js"])
    dashes = [p.relative_to(ROOT).as_posix() for p in targets
              if p.is_file() and (EM in p.read_text(encoding="utf-8", errors="replace")
                                  or EN in p.read_text(encoding="utf-8", errors="replace"))]
    check("no em or en dashes anywhere", not dashes, dashes[:4])

    brit = re.compile(r"\b(paediatric|behavioural|prioritis|subsidis|programme|realise|analyse\b|emphasis[ei]|colour)", re.I)
    offenders = [p.relative_to(ROOT).as_posix() for p in targets
                 if p.is_file() and brit.search(p.read_text(encoding="utf-8", errors="replace"))]
    check("american spellings throughout", not offenders, offenders[:4])

    ABBR = re.compile(r"\b(e\.g|i\.e|etc|Dr|Mr|Mrs|St|vs|Inc|No|a\.m|p\.m)\.$", re.I)
    broken = []
    for p in list((ROOT / "materials").rglob("*.md")) + list((ROOT / "claude-kit").rglob("*.md")):
        t = p.read_text(encoding="utf-8")
        for n, line in enumerate(t.split("\n"), 1):
            if re.search(r"[,.:;]\s+$", line) and line.strip():
                broken.append(f"{p.name}:{n} trailing punctuation")
        for m in re.finditer(r"([.!?])(\s*\n\s*|\s+)([a-z]\w+)", t):
            if ABBR.search(t[max(0, m.start() - 12):m.start() + 1]):
                continue
            if "  " in t[max(0, m.start() - 40):m.start()]:
                continue
            broken.append(f"{p.name} lowercase after sentence end")
    check("no stranded punctuation or lowercase sentence starts", not broken, broken[:4])


# -------------------------------------------------------------------- repo

def qa_repo():
    section("repo hygiene")
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    check("git tracks the site", any(f.startswith("site/") for f in tracked))
    check("git tracks the kit sources", any(f.startswith("claude-kit/") for f in tracked))
    check("git tracks the data sources", any(f.startswith("data/sources/") for f in tracked))

    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    check("working tree is clean after a build", status == "", status.replace("\n", " | ")[:200])

    check("no pycache committed", not any("__pycache__" in f for f in tracked))
    srcs = sorted((ROOT / "data/sources").glob("*.json"))
    check("source files present", len(srcs) == 7, len(srcs))
    for s in srcs:
        try:
            json.loads(s.read_text(encoding="utf-8"))
            check(f"valid json: {s.name}", True)
        except json.JSONDecodeError as exc:
            check(f"valid json: {s.name}", False, str(exc))


def main() -> int:
    for fn in (qa_scripts, qa_workflows, qa_build, qa_outputs, qa_kit, qa_prose, qa_repo):
        try:
            fn()
        except Exception as exc:  # a broken check must not hide the rest
            check(f"{fn.__name__} crashed", False, repr(exc)[:180])

    fails = [r for r in RESULTS if not r[1]]
    for name, passed, detail in RESULTS:
        if name.startswith("__"):
            print(f"\n== {name.strip('_')}")
        elif not passed:
            print(f"  FAIL  {name}  :: {detail}")
    passed = sum(1 for r in RESULTS if r[1] and not r[0].startswith("__"))
    total = sum(1 for r in RESULTS if not r[0].startswith("__"))
    print(f"\n{passed}/{total} passed, {len(fails)} failed")
    return len(fails)


if __name__ == "__main__":
    raise SystemExit(main())
