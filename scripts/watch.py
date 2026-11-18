#!/usr/bin/env python3
"""Fetch every program page, check the link works, and notice when it changes.

Why this exists: as of late 2026 most Summer 2027 cycles are not posted yet, so
the dataset is full of projected dates. Rather than guess, this watches the real
pages and tells you the week a page changes, which is almost always the week
the new dates drop.

    python scripts/watch.py              fetch, compare, report, save state
    python scripts/watch.py --links-only just check links; compares and saves nothing
    python scripts/watch.py --quiet      only print problems and changes

Exit codes: 0 nothing notable, 1 broken links, 2 changes detected, 3 both.
Python itself also exits 1 on a crash and 2 on a bad argument, so check that a
run finished before acting on its code: a full run always rewrites both
data/watch-report.md and data/watch-state.json.
Stdlib only, so it runs anywhere with Python 3.9+.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import http.client
import json
import os
import pathlib
import re
import socket
import ssl
import time
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
# TIMEOUT restarts with every packet, so a server that trickles out a few
# bytes at a time could hold a worker, and the whole weekly job, for hours.
# This bounds the full read of one page.
PAGE_TIMEOUT = 60
MAX_BYTES = 3_000_000
WORKERS = 8

# A bot check, or a page drawn entirely by scripts, answers 200 with next to
# no text. Hashing that watches nothing while counting the page as covered.
# The shortest real page read so far has about 1,200 characters.
THIN = 400

# Building a context loads the whole CA store, so every request shares one
# rather than rebuilding it about 150 times a run.
CONTEXT = ssl.create_default_context()
# OpenSSL's codes for an issuer it could not find or trust (2, 20, 21) or a
# root it does not know (19), as opposed to a certificate that is itself bad.
CHAIN_ERRORS = (2, 19, 20, 21)

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

MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December")
MONTHS = {name[:3].lower(): number for number, name in enumerate(MONTH_NAMES, 1)}
DATE_PARTS = re.compile(r"([a-z]+)\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", re.I)

# An edit this small that brings no new upcoming date and no change in status
# text is usually a "last updated" stamp or a news item, not a posting.
SMALL_EDIT = 200

# What a page keeps from its last read that worked, so that a week it cannot
# be read does not cost it the text the next good read is compared against.
BASELINE = ("checked", "final_url", "hash", "length", "mentions_2027",
            "dates_found", "status_phrases")


def visible_text(raw: str) -> str:
    body = raw
    for pattern in NOISE:
        body = pattern.sub(" ", body)
    body = TAGS.sub(" ", body)
    body = html.unescape(body)
    return WHITESPACE.sub(" ", body).strip()


def date_key(raw: str) -> tuple[int, int, int] | None:
    """(year, month, day) for a date as DATE_HINT finds it, or None."""
    m = DATE_PARTS.match(raw)
    month = MONTHS.get(m.group(1)[:3].lower()) if m else None
    return (int(m.group(3)), month, int(m.group(2))) if month else None


def tidy_dates(found) -> list[str]:
    """Spell each date one way and put them in calendar order.

    A page that rewrites "Jan. 5, 2027" as "January 5, 2027" has not posted a
    new date, so dates are compared in one spelling. The list is kept whole:
    it used to be sorted as text and capped, which dropped September to
    November first, the months application cycles open and close.
    """
    when = {}
    for raw in found:
        key = date_key(raw)
        if key:
            year, month, day = key
            when[f"{MONTH_NAMES[month - 1]} {day}, {year}"] = key
    return sorted(when, key=when.get)


def latest(dates: list[str], n: int = 6) -> str:
    """The last few dates, which on a program page are the likeliest to be the new cycle's."""
    shown = ", ".join(dates[-n:])
    return shown if len(dates) <= n else f"{shown} (and {len(dates) - n} earlier)"


def get(url: str, ua: str) -> tuple[str, str]:
    """Fetch one page as `ua`. Returns (final url, decoded body) or raises."""
    request = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,*/*"})
    give_up = time.monotonic() + PAGE_TIMEOUT
    with urllib.request.urlopen(request, timeout=TIMEOUT, context=CONTEXT) as response:
        payload = bytearray()
        while len(payload) < MAX_BYTES:
            chunk = response.read1(65536)
            if not chunk:
                break
            payload += chunk
            if time.monotonic() > give_up:
                raise TimeoutError(f"still loading after {PAGE_TIMEOUT} seconds")
        charset = response.headers.get_content_charset() or "utf-8"
        return response.geturl(), bytes(payload[:MAX_BYTES]).decode(charset, errors="replace")


def classify(exc: Exception) -> tuple[str, str, int | None, bool]:
    """Sort a failed fetch into (status, reason, HTTP code, worth retrying as a browser).

    Only evidence that a page is gone makes it broken. Anything else means
    this checker could not read it, which needs a person with a browser
    rather than a new link.
    """
    if isinstance(exc, urllib.error.HTTPError):
        # A server error says nothing about whether the page exists, and some
        # bot filters answer with a 503, so it is treated like a refusal.
        refused = exc.code in REFUSED or exc.code >= 500
        return ("blocked" if refused else "http-error", f"HTTP {exc.code}", exc.code, refused)
    # urllib wraps anything that fails while connecting, the TLS handshake
    # included, in URLError, so the real cause is underneath it.
    cause = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(cause, ssl.SSLCertVerificationError):
        why = getattr(cause, "verify_message", None) or cause
        # Browsers fetch a missing intermediate certificate themselves and
        # trust newer roots than Python's store, so a chain Python cannot
        # follow usually opens fine. An expired or mismatched certificate
        # makes a browser warn too, but the page is still not gone.
        if getattr(cause, "verify_code", None) in CHAIN_ERRORS:
            return ("blocked", f"certificate chain Python cannot verify ({why}), "
                    "usually fine in a browser", None, False)
        return ("blocked", f"certificate problem ({why}), a browser may warn too", None, False)
    if isinstance(cause, ssl.SSLError):
        why = getattr(cause, "reason", None) or cause
        return ("blocked", f"secure connection failed ({why})"[:200], None, False)
    if isinstance(cause, (TimeoutError, socket.timeout, ConnectionResetError, ConnectionAbortedError,
                          BrokenPipeError, http.client.IncompleteRead, http.client.BadStatusLine)):
        # Some hosts turn away a non-browser client by hanging up or by never
        # answering, rather than with a 403. That is a block, not a dead link.
        return ("blocked", f"{type(cause).__name__}: {cause}"[:200], None, True)
    if isinstance(exc, urllib.error.URLError):
        # DNS failures and refused connections are not about who is asking.
        return ("unreachable", str(cause)[:200], None, False)
    return ("error", f"{type(exc).__name__}: {exc}"[:200], None, False)


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

    final_url = text = None
    failure = None

    for agent in (UA, BROWSER_UA):
        try:
            final_url, raw = get(url, agent)
        except Exception as exc: # noqa: BLE001 - a watcher must never die on one bad page
            kind, reason, code, retry = classify(exc)
            failure = (kind, reason, code)
            if retry:
                continue
            break
        text = visible_text(raw)
        if len(text) >= THIN:
            failure = None
            break
        # Treated like a refusal and retried as a browser, since some of
        # these hand a browser the real page.
        failure = ("blocked", f"only {len(text)} characters of text, so the page is drawn "
                   "by scripts or sits behind a bot check", 200)

    if failure:
        kind, reason, code = failure
        result.update(status=kind, reason=reason)
        if code is not None:
            result["code"] = code
        return result

    result.update(
        status="ok",
        code=200,
        final_url=final_url,
        redirected=final_url.rstrip("/") != program["url"].rstrip("/"),
        hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        length=len(text),
        mentions_2027=bool(CYCLE_HINT.search(text)),
        dates_found=tidy_dates(m.group(0) for m in DATE_HINT.finditer(text)),
        status_phrases=sorted({m.group(0).lower() for m in CLOSED_HINT.finditer(text)}),
    )
    return result


def baseline(entry: dict | None) -> dict | None:
    """The last read of a page that worked: the entry itself, or what it kept."""
    if not entry:
        return None
    return entry if entry.get("status") == "ok" else entry.get("last_ok")


def persist(result: dict, before: dict | None) -> dict:
    """What to save for a page. Underscored fields only feed this run's report."""
    entry = {k: v for k, v in result.items() if not k.startswith("_")}
    base = baseline(before)
    if entry["status"] != "ok" and base:
        entry["last_ok"] = {k: base[k] for k in BASELINE if k in base}
    return entry


def load_state() -> dict:
    if not STATE.is_file():
        return {"runs": 0, "pages": {}}
    # A file that is there but will not parse is not the same as no file.
    # Starting over would report a week of real changes as nothing and then
    # save the empty baseline over the last good one, so stop instead: git
    # still has the previous copy.
    restore = "restore it with `git checkout -- data/watch-state.json`, or delete it to start over"
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"data/watch-state.json could not be read ({exc}); {restore}")
    if not isinstance(state, dict) or not isinstance(state.get("pages", {}), dict):
        raise SystemExit(f"data/watch-state.json is not a watch state; {restore}")
    return state


def save_state(state: dict) -> None:
    # Written beside the real file and then moved over it in one step, so a
    # run killed partway through leaves last week's baselines whole rather
    # than half a file.
    tmp = STATE.with_name(STATE.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, STATE)


def change_line(r: dict) -> str:
    # A page that could not be read last time is compared with an older read,
    # so the line says how far back the difference reaches.
    since = f" since {r['_since']}" if r.get("_since") else ""
    return f"- **{r['name']}** ({r['org']}), {r['_delta']:+d} chars{since}, [page]({r['url']})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--links-only", action="store_true",
                        help="only check the links; compares nothing and saves nothing")
    parser.add_argument("--quiet", action="store_true", help="only print problems and changes")
    args = parser.parse_args()

    if not PROGRAMS.is_file():
        raise SystemExit("data/programs.json missing, run scripts/build.py first")

    programs = json.loads(PROGRAMS.read_text(encoding="utf-8"))["programs"]
    state = load_state()
    previous = state.get("pages", {})

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(fetch, programs))

    today = dt.datetime.now(dt.timezone.utc).date()
    today_key = (today.year, today.month, today.day)
    broken, new_2027, skipped, blocked = [], [], [], []

    for result in results:
        pid = result["id"]
        before = previous.get(pid)

        if result["status"] == "skipped":
            skipped.append(result)
            continue

        if result["status"] == "blocked":
            # A page that could be read last time, or a program new to the
            # list, has just dropped out of what this can watch, which is
            # news. The rest are the same list as every other week.
            result["_newly_blocked"] = not before or before.get("status") == "ok"
            if not before or before.get("status") != "blocked":
                result["first_blocked_at"] = result["checked"][:10]
            elif before.get("first_blocked_at"):
                result["first_blocked_at"] = before["first_blocked_at"]
            blocked.append(result)
            continue

        if result["status"] != "ok":
            broken.append(result)
            continue

        # Compared with the last read that worked, not with last week's, which
        # may have failed. Skipping the page instead would compare it with this
        # week's text next time, so a change made during the gap would never
        # be reported.
        base = baseline(before)

        # A deliberate short link such as jax.org/ssp redirects on every single
        # run. Saying so once is useful; saying so every week is noise, so only
        # a redirect whose destination moved since last time earns a line.
        if result["redirected"] and (not base or base.get("final_url") != result["final_url"]):
            result["_new_redirect"] = True

        if args.links_only or not base:
            continue

        if base.get("hash") != result["hash"]:
            was = set(tidy_dates(base.get("dates_found", [])))
            result["_delta"] = result["length"] - base.get("length", 0)
            result["_fresh"] = [d for d in result["dates_found"] if d not in was]
            result["_was_phrases"] = base.get("status_phrases", [])
            if base is not before:
                result["_since"] = base.get("checked", "")[:10]
            # Plenty of pages differ by a few characters every week, a "last
            # updated" stamp or a news item, with nothing in the edit to act
            # on. They are still listed, under their own heading, so the edits
            # that brought an upcoming date, changed status text, a first
            # mention of 2027 or a real block of text are not buried among
            # them. A new date already past is a news item or a stamp; a
            # posting gives dates that are still ahead.
            result["_small"] = not (
                any(date_key(d) > today_key for d in result["_fresh"])
                or result["status_phrases"] != result["_was_phrases"]
                or (result["mentions_2027"] and not base.get("mentions_2027"))
                or abs(result["_delta"]) >= SMALL_EDIT
            )
            result["_candidate"] = True

        if result["mentions_2027"] and not base.get("mentions_2027"):
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

    changed = [r for r in candidates if not r.get("volatile") and not r["_small"]]
    small = [r for r in candidates if not r.get("volatile") and r["_small"]]
    volatile = [r for r in candidates if r.get("volatile")]
    newly_blocked = [r for r in blocked if r["_newly_blocked"]]
    still_blocked = [r for r in blocked if not r["_newly_blocked"]]

    state["runs"] = state.get("runs", 0) + 1
    state["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    ok_count = sum(1 for r in results if r["status"] == "ok")
    run = ("Links only, so nothing was compared or saved." if args.links_only
           else f"Run #{state['runs']}.")

    # Human-readable report, also used as the body of the CI issue.
    report = [
        f"# Watch report, {state['last_run'][:10]}",
        "",
        f"Checked **{len(results)}** program pages: {ok_count} OK, "
        f"{len(broken)} broken, {len(blocked)} unreadable, {len(skipped)} skipped. {run}",
        "",
    ]

    if new_2027:
        report += ["## Pages that just started mentioning 2027", ""]
        for r in new_2027:
            report.append(f"- **{r['name']}** ({r['org']}), [page]({r['url']})")
            if r["dates_found"]:
                report.append(f"  - dates on page: {latest(r['dates_found'])}")
            if r["status_phrases"]:
                report.append(f"  - status text: {'; '.join(r['status_phrases'])}")
        report.append("")

    if changed:
        report += ["## Pages whose content changed", ""]
        for r in changed:
            report.append(change_line(r))
            if r["_fresh"]:
                report.append(f"  - new dates on page: {latest(r['_fresh'])}")
            if r["status_phrases"] != r["_was_phrases"]:
                # Text that vanished matters too: "will open" disappearing
                # often means the application just did.
                now = "; ".join(r["status_phrases"]) or "none"
                was = "; ".join(r["_was_phrases"]) or "none"
                report.append(f"  - status text: {now} (was {was})")
            elif r["status_phrases"]:
                report.append(f"  - status text: {'; '.join(r['status_phrases'])}")
        report.append("")

    if small:
        report += [
            "## Small edits",
            "",
            f"Under {SMALL_EDIT} characters, with no new upcoming date and no change in status",
            "text, so usually a \"last updated\" stamp or a news item. Listed for the record, not",
            "counted above.",
            "",
        ]
        for r in small:
            report.append(change_line(r))
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

    if newly_blocked:
        report += [
            "## Newly unreadable (check these by hand in a browser)",
            "",
            "Read fine last time, or new to the list, so the weekly check has just lost",
            "sight of these.",
            "",
        ]
        for r in newly_blocked:
            report.append(f"- **{r['name']}** ({r['org']}), {r['reason']}, [page]({r['url']})")
        report.append("")

    if still_blocked:
        report += ["## Still unreadable (check these by hand in a browser)", ""]
        for r in still_blocked:
            since = f", since {r['first_blocked_at']}" if r.get("first_blocked_at") else ""
            report.append(f"- **{r['name']}** ({r['org']}), {r['reason']}{since}, [page]({r['url']})")
        report.append("")

    redirects = [r for r in results if r.get("_new_redirect")]
    if redirects:
        report += ["## Redirects (consider updating the stored URL)", ""]
        for r in redirects:
            report.append(f"- **{r['name']}**: `{r['url']}` -> `{r['final_url']}`")
        report.append("")

    if args.links_only:
        if not broken:
            report += ["No broken links.", ""]
    elif not (new_2027 or changed or broken or newly_blocked):
        report += ["Nothing new to act on since the last run.", ""]

    # --links-only leaves both files alone. Saving would make this run's text
    # the baseline, and the next full run would compare against it and miss
    # whatever changed in between.
    if not args.links_only:
        # The report goes first: should saving the state then fail, the next
        # run reports these changes again rather than never.
        REPORT.write_text("\n".join(report), encoding="utf-8")
        state["pages"] = {r["id"]: persist(r, previous.get(r["id"])) for r in results}
        save_state(state)

    if not args.quiet:
        print("\n".join(report))
    else:
        for bucket, label in ((broken, "broken"), (newly_blocked, "newly unreadable"),
                              (changed, "changed"), (new_2027, "new-2027")):
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
