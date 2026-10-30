#!/usr/bin/env python3
"""Curation tool: pull candidate 2027 deadline sentences off every program page.

The watcher tells you a page *changed*. This tells you what it now says. Run it
when the watcher flags pages mentioning 2027, read the sentences it prints, and
promote the ones that are unambiguous from "projected" to "confirmed" by hand.

Deliberately does not write to the dataset. A regex is good enough to find a
candidate sentence and nowhere near good enough to be trusted with a date that
someone will plan a summer around.

    python scripts/extract_dates.py            # only pages mentioning 2027
    python scripts/extract_dates.py --all      # every page
    python scripts/extract_dates.py --id nih-sip
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import pathlib
import re
import ssl
import sys
import urllib.error
import urllib.request

# Program pages are full of curly quotes and dashes; a Windows console defaults
# to cp1252 and would die on the first one.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAMS = ROOT / "data" / "programs.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
TIMEOUT = 25

STRIP = [
    re.compile(r"<script\b.*?</script>", re.S | re.I),
    re.compile(r"<style\b.*?</style>", re.S | re.I),
    re.compile(r"<!--.*?-->", re.S),
]

DATE_2027 = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+"
    r"\d{1,2}(?:st|nd|rd|th)?,?\s+2027\b",
    re.I,
)

# A sentence that talks about applying AND carries a date is worth reading.
DEADLINE_SENTENCE = re.compile(
    r"[^.!?]{0,140}"
    r"(?:deadline|due\b|applications?\s+(?:open|close|will open|are open|are due|must be)|"
    r"apply by|submit(?:ted)?\s+by|closes?\s+on)"
    r"[^.!?]{0,180}[.!?]",
    re.I,
)


def visible(raw: str) -> str:
    for pattern in STRIP:
        raw = pattern.sub(" ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def fetch(program: dict) -> dict:
    url = program["url"]
    out = {"id": program["id"], "name": program["name"], "url": url, "status": program.get("deadline_status")}

    if "google.com/search" in url:
        out["error"] = "placeholder URL"
        return out

    try:
        request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
            body = response.read(3_000_000)
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        out["error"] = f"HTTP {exc.code}"
        return out
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}"
        return out

    text = visible(body.decode(charset, errors="replace"))
    out["dates_2027"] = sorted(set(m.group(0) for m in DATE_2027.finditer(text)))
    out["sentences"] = [
        s.strip()
        for s in dict.fromkeys(m.group(0) for m in DEADLINE_SENTENCE.finditer(text))
        if "2027" in s or "2026" in s
    ][:4]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="include pages with no 2027 mention")
    parser.add_argument("--id", help="only this program id")
    args = parser.parse_args()

    programs = json.loads(PROGRAMS.read_text(encoding="utf-8"))["programs"]
    if args.id:
        programs = [p for p in programs if p["id"] == args.id]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch, programs))

    hits = 0
    for r in results:
        if r.get("error"):
            continue
        has2027 = bool(r.get("dates_2027"))
        if not has2027 and not args.all:
            continue
        hits += 1
        flag = "ALREADY CONFIRMED" if r["status"] == "confirmed" else "-> review"
        print(f"\n## {r['name']}  [{r['id']}]  {flag}")
        print(f"   {r['url']}")
        if r.get("dates_2027"):
            print(f"   2027 dates: {', '.join(r['dates_2027'][:8])}")
        for s in r.get("sentences", []):
            print(f"   > {s[:190]}")

    errors = [r for r in results if r.get("error")]
    print(f"\n{hits} page(s) mention a 2027 date · {len(errors)} unreadable")
    if errors:
        print("unreadable: " + ", ".join(f"{r['id']}({r['error']})" for r in errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
