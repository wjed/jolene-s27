#!/usr/bin/env python3
"""Test candidate URLs in bulk and report which ones actually resolve.

Used while curating data/sources/*.json, feed it candidates, keep the winners.

    python scripts/try_urls.py candidates.txt
    python scripts/try_urls.py - < candidates.txt

Input format: one URL per line, optionally "id<TAB>url" to group by program.
Blank lines and lines starting with # are ignored.
"""

from __future__ import annotations

import concurrent.futures
import pathlib
import ssl
import sys
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
TIMEOUT = 20


def probe(entry: tuple[str, str]) -> tuple[str, str, str, str]:
    label, url = entry
    request = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=ssl.create_default_context()) as response:
            final = response.geturl()
            body = response.read(400_000).decode("utf-8", errors="replace").lower()
            # Some sites serve a 200 for their own not-found page.
            soft404 = any(
                marker in body
                for marker in ("page not found", "404 error", "page cannot be found", "page you requested")
            )
            verdict = "SOFT-404" if soft404 or "/404" in final else "OK"
            return label, verdict, url, final
    except urllib.error.HTTPError as exc:
        return label, f"HTTP {exc.code}", url, ""
    except urllib.error.URLError as exc:
        return label, "UNREACHABLE", url, str(exc.reason)[:80]
    except Exception as exc: # noqa: BLE001
        return label, type(exc).__name__, url, str(exc)[:80]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    source = sys.argv[1]
    raw = sys.stdin.read() if source == "-" else pathlib.Path(source).read_text(encoding="utf-8")

    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        label, _, url = line.rpartition("\t")
        entries.append((label or "-", url))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(probe, entries))

    last = None
    for label, verdict, url, final in results:
        if label != last:
            print(f"\n== {label}")
            last = label
        flag = "  " if verdict == "OK" else "!!"
        print(f"{flag} {verdict:12} {url}")
        if final and final.rstrip("/") != url.rstrip("/"):
            print(f"               -> {final}")

    good = sum(1 for _, v, _, _ in results if v == "OK")
    print(f"\n{good}/{len(results)} resolved cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
