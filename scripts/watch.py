#!/usr/bin/env python3
"""Fetch every program page, check the link works, and notice when it changes.

Why this exists: as of late 2026 most Summer 2027 cycles are not posted yet, so
the dataset is full of projected dates. Rather than guess, this watches the real
pages and tells you the week a page changes, which is almost always the week
the new dates drop.

    python scripts/watch.py              fetch, compare, report, save state
    python scripts/watch.py --links-only skip change detection, just check links
    python scripts/watch.py --quiet      only print problems and changes

Exit codes: 0 nothing notable, 1 broken links, 2 changes detected, 3 both.
Stdlib only, so it runs anywhere with Python 3.9+.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import ssl
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAMS = ROOT / "data" / "programs.json"
STATE = ROOT / "data" / "watch-state.json"
REPORT = ROOT / "data" / "watch-report.md"

UA = "Mozilla/5.0 (compatible; jolene-s27-research-finder/1.0; +https://github.com/wjed/jolene-s27)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# NIH and a handful of other hosts sit behind a filter that refuses a
# self-identifying bot while serving the same page to a browser without
# complaint. Calling those pages broken every week would be wrong, so a
# refusal is retried once as a browser before it is believed.
REFUSED = (401, 403, 405, 406, 429)
TIMEOUT = 25
WORKERS = 8

# Content we never want to hash: it changes on every page load and would make
# every single page look like it had been updated.
NOISE = [
    re.compile(r"<script\b.*?</script>", re.S | re.I),
    re.compile(r"<style\b.*?</style>", re.S | re.I),
    re.compile(r"<noscript\b.*?</noscript>", re.S | re.I),
    re.compile(r"<!--.*?-->", re.S),
    re.compile(r"<svg\b.*?</svg>", re.S | re.I),
    re.compile(r"csrf[-_]?token[\"':=\s]+[\w-]+", re.I),
    re.compile(r"nonce=[\"'][^\"']+[\"']", re.I),
    re.compile(r"\b\d{10,13}\b"), # epoch timestamps in cache-busting query strings
]

TAGS = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")

# Signals worth surfacing in the report.
CYCLE_HINT = re.compile(r"\b(2027|summer\s+2027)\b", re.I)
DATE_HINT = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+20\d{2}\b",
    re.I,
)
CLOSED_HINT = re.compile(
    r"(applications?\s+(?:are\s+)?closed|no longer accepting|deadline has passed|"
    r"check back|will open|now open|applications?\s+open)",
    re.I,
)


def visible_text(raw: str) -> str:
    body = raw
    for pattern in NOISE:
        body = pattern.sub(" ", body)
    body = TAGS.sub(" ", body)
    body = html.unescape(body)
    return WHITESPACE.sub(" ", body).strip()


def get(url: str, ua: str) -> tuple[str, str]:
    """Fetch one page as `ua`. Returns (final url, decoded body) or raises."""
    request = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(request, timeout=TIMEOUT,
                                context=ssl.create_default_context()) as response:
        payload = response.read(3_000_000)
        charset = response.headers.get_content_charset() or "utf-8"
        return response.geturl(), payload.decode(charset, errors="replace")


def fetch(program: dict) -> dict:
    url = program["url"]
    result = {
        "id": program["id"],
        "name": program["name"],
        "org": program["org"],
        "url": url,
        "checked": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }

    # Search-engine placeholders for the two unidentified programs: nothing to watch.
    if "google.com/search" in url:
        result.update(status="skipped", reason="placeholder search URL")
        return result

    final_url = raw = None
    failure = None

    for agent in (UA, BROWSER_UA):
        try:
            final_url, raw = get(url, agent)
            failure = None
            break
        except urllib.error.HTTPError as exc:
            refused = exc.code in REFUSED
            failure = ("blocked" if refused else "http-error", f"HTTP {exc.code}", exc.code)
            if not refused:
                break
        except urllib.error.URLError as exc:
            # DNS and connection failures are not about who is asking.
            failure = ("unreachable", str(exc.reason)[:200], None)
            break
        except Exception as exc: # noqa: BLE001 - a watcher must never die on one bad page
            # Some hosts refuse a non-browser client at the connection level
            # rather than with a 403. That is a block, not a dead link.
            name = type(exc).__name__
            at_connection = name in ("RemoteDisconnected", "ConnectionResetError",
                                     "IncompleteRead", "BadStatusLine")
            failure = ("blocked" if at_connection else "error", f"{name}: {exc}"[:200], None)
            if not at_connection:
                break

    if failure:
        kind, reason, code = failure
        result.update(status=kind, reason=reason)
        if code is not None:
            result["code"] = code
        return result

    text = visible_text(raw)

    result.update(
        status="ok",
        code=200,
        final_url=final_url,
        redirected=final_url.rstrip("/") != program["url"].rstrip("/"),
        hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        length=len(text),
        mentions_2027=bool(CYCLE_HINT.search(text)),
        dates_found=sorted({m.group(0) for m in DATE_HINT.finditer(text)})[:12],
        status_phrases=sorted({m.group(0).lower() for m in CLOSED_HINT.finditer(text)})[:6],
    )
    return result


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"runs": 0, "pages": {}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--links-only", action="store_true", help="skip change detection")
    parser.add_argument("--quiet", action="store_true", help="only print problems and changes")
    args = parser.parse_args()

    if not PROGRAMS.is_file():
        raise SystemExit("data/programs.json missing, run scripts/build.py first")

    programs = json.loads(PROGRAMS.read_text(encoding="utf-8"))["programs"]
    state = load_state()
    previous = state.get("pages", {})

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(fetch, programs))

    broken, new_2027, skipped, blocked = [], [], [], []

    for result in results:
        pid = result["id"]
        before = previous.get(pid)

        if result["status"] == "skipped":
            skipped.append(result)
            continue

        if result["status"] == "blocked":
            blocked.append(result)
            continue

        if result["status"] != "ok":
            broken.append(result)
            continue

        # A deliberate short link such as jax.org/ssp redirects on every single
        # run. Saying so once is useful; saying so every week is noise, so only
        # a redirect whose destination moved since last time earns a line.
        if result["redirected"] and (not before or before.get("final_url") != result["final_url"]):
            result["_new_redirect"] = True

        if args.links_only or not before or before.get("status") != "ok":
            continue

        if before.get("hash") != result["hash"]:
            result["_delta"] = result["length"] - before.get("length", 0)
            result["_was"] = before.get("dates_found", [])
            result["_candidate"] = True

        if result["mentions_2027"] and not before.get("mentions_2027"):
            new_2027.append(result)

    # A page that differs from last week may have been updated, or may simply
    # render something different on every load: clinic wait times, a rotating
    # banner, a shuffled list of featured links. Reading it a second time tells
    # the two apart. If two reads seconds apart disagree with each other, the
    # page is volatile, and reporting it every single week would bury the real
    # signal under pages that have nothing to say.
    candidates = [r for r in results if r.get("_candidate")]
    if candidates:
        by_id = {p["id"]: p for p in programs}
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
            again = list(pool.map(fetch, [by_id[r["id"]] for r in candidates]))
        for first, second in zip(candidates, again):
            if second.get("status") == "ok" and second.get("hash") != first["hash"]:
                first["volatile"] = True

    changed = [r for r in candidates if not r.get("volatile")]
    volatile = [r for r in candidates if r.get("volatile")]

    # Persist state for the next run.
    state["runs"] = state.get("runs", 0) + 1
    state["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    state["pages"] = {r["id"]: r for r in results}
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok_count = sum(1 for r in results if r["status"] == "ok")

    # Human-readable report, also used as the body of the CI issue.
    report = [
        f"# Watch report, {state['last_run'][:10]}",
        "",
        f"Checked **{len(results)}** program pages: {ok_count} OK, "
        f"{len(broken)} broken, {len(blocked)} bot-blocked, {len(skipped)} skipped. "
        f"Run #{state['runs']}.",
        "",
    ]

    if new_2027:
        report += ["## Pages that just started mentioning 2027", ""]
        for r in new_2027:
            report.append(f"- **{r['name']}** ({r['org']}), [page]({r['url']})")
            if r["dates_found"]:
                report.append(f"  - dates on page: {', '.join(r['dates_found'][:6])}")
            if r["status_phrases"]:
                report.append(f"  - status text: {'; '.join(r['status_phrases'])}")
        report.append("")

    if changed:
        report += ["## Pages whose content changed", ""]
        for r in changed:
            arrow = f"{r['_delta']:+d} chars"
            report.append(f"- **{r['name']}** ({r['org']}), {arrow}, [page]({r['url']})")
            fresh = [d for d in r["dates_found"] if d not in r["_was"]]
            if fresh:
                report.append(f"  - new dates on page: {', '.join(fresh[:6])}")
            if r["status_phrases"]:
                report.append(f"  - status text: {'; '.join(r['status_phrases'])}")
        report.append("")

    if volatile:
        report += [
            "## Pages that change on every load",
            "",
            "These differ every time they are read (wait times, rotating banners), so a",
            "difference here does not mean the program page was updated. Not counted above.",
            "",
        ]
        for r in volatile:
            report.append(f"- **{r['name']}** ({r['org']}), [page]({r['url']})")
        report.append("")

    if broken:
        report += ["## Links that need fixing", ""]
        for r in broken:
            report.append(f"- **{r['name']}** ({r['org']}), {r['reason']}, `{r['url']}`")
        report.append("")

    if blocked:
        report += [
            "## Bot-blocked (check these by hand in a browser)",
            "",
        ]
        for r in blocked:
            report.append(f"- **{r['name']}** ({r['org']}), {r['reason']}, [page]({r['url']})")
        report.append("")

    redirects = [r for r in results if r.get("_new_redirect")]
    if redirects:
        report += ["## Redirects (consider updating the stored URL)", ""]
        for r in redirects:
            report.append(f"- **{r['name']}**: `{r['url']}` -> `{r['final_url']}`")
        report.append("")

    if not (new_2027 or changed or broken):
        report += ["Nothing changed since the last run.", ""]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not args.quiet:
        print("\n".join(report))
    else:
        for bucket, label in ((broken, "broken"), (changed, "changed"), (new_2027, "new-2027")):
            for r in bucket:
                print(f"{label}: {r['name']}, {r['url']}")

    code = 0
    if broken:
        code |= 1
    if changed or new_2027:
        code |= 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
