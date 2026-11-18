# Summer 2027 Research Finder

A searchable database of **106 undergraduate summer research programs**, a
deadline-aware application tracker, a set of application templates, and a watcher
that notices when program pages change.

**→ [Open the site](https://wjed.github.io/jolene-s27/)**

Built around pediatric, neuroscience and clinical research, for a rising senior
applying in the Summer 2027 cycle.

---

## Why this exists

The starting point was a list of 24 programs in Notion. It had the right
instincts, St. Jude, CHOP, Cincinnati Children's, Yale Child Study, but as a
flat list it could not answer the questions that actually matter: *what is open
today, what is due first, what am I not eligible for, and what am I missing?*

This repo answers those, and adds more than eighty programs that were not on the
list.

## What is here

| | |
|---|---|
| **[The site](https://wjed.github.io/jolene-s27/)** | Filterable database, prioritized action plan, application tracker, timeline |
| **[`data/`](data/)** | The dataset: JSON, a CSV export, and an `.ics` calendar with reminders |
| **[`claude-kit/`](claude-kit/)** | Files she can attach to a Claude chat so it has full context: who she is, every fact a form asks for, and three skills (fill an application in the browser, email a lab, watch deadlines weekly). Published to the site as individual downloads and a zip by `scripts/kit.py`. |
| **[`materials/`](materials/)** | Source markdown for the nine guides and templates. They are rendered onto the site at build time by `scripts/guides.py`, so nobody has to read them on GitHub. |
| **[`scripts/`](scripts/)** | Build, validate, link-check and watch |

### Design

The interface follows Notion's workspace conventions, because that is what this
is actually used in alongside. The tokens were read off Notion's own stylesheets
rather than approximated: the ink `rgb(55,53,47)`, the hover
`rgba(25,23,17,.075)`, the hairline `rgba(55,53,47,.09)`, the blue
`rgb(35,131,226)`, the inset-plus-halo focus ring, Inter with lining numerals,
and the standard database select palette for the pills.

That means a page sidebar, database views (table / board / gallery), select
pills that keep one color per option, and a peek panel with a property table:
the same moves a Notion database makes.

### The site, specifically

- **The plan**: not a list but an ordered set of actions: what is accepting
  applications today, which applications give the best return, what is due in 30
  days, what to do monthly.
- **All programs**: filter by research area, deadline month, housing, stipend,
  citizenship requirement and how competitive it is.
- **My eligibility**: your year, GPA and citizenship, kept in the browser. The
  three things that rule applications out before anyone reads them are in the
  data, so every program that conflicts gets flagged with the reason, and a
  "Fits my profile" filter appears.
- **Copy for Notion**: copies whatever is on screen as a Markdown table, which
  Notion pastes as a real database.
- **My applications**: per-program status, a requirements checklist and notes.
  Stored in the browser only; nothing is uploaded anywhere. Use **Backup** before
  clearing cookies.
- **Timeline**: every opening date and deadline in order.

## The honest part: which dates are real

Every date carries one of four statuses, and the site shows it next to the date:

| | |
|---|---|
| **confirmed** | read off the program's own page |
| **projected** | carried forward from a previous cycle, shown with an `est.` marker |
| **unknown** | nothing posted yet |
| **rolling** | no fixed date |

The Plan counts them live, so there is no tally here to go stale. When this was
built in late October most Summer 2027 cycles had not posted their dates, and
some still have not. Rather than guess and present guesses as fact, every date
carries its status, and the watcher checks the real pages weekly.

**January is the first wall.** Seattle Children's closes **4 Jan** (5pm PT),
the Broad **10 Jan**, MD Anderson CATALYST **13 Jan**, Yale Child Study
**14 Jan** (5pm ET), the Jackson Laboratory **25 Jan** (5pm ET) and NIH SIP
**26 Jan** (noon ET), with the big cluster on **1 Feb** behind them. The site's
Timeline has every date.

## The watcher

```bash
python scripts/watch.py
```

Fetches all 106 program pages, compares each against the previous run, and reports:

- pages whose content changed since last time
- **pages that have started mentioning 2027**: usually the week the new cycle goes live
- links that broke
- redirects worth folding back into the data
- pages that refuse an automated reader, so the site can list them for her to
  check by hand

It runs every Monday in GitHub Actions and opens an issue when anything changes.
Running it during the build caught 43 dead or redirected URLs in the first pass.

Exit codes: `0` nothing notable · `1` broken links · `2` changes · `3` both.

## Testing

Two suites, because they reach different things.

`scripts/qa_all.py` is the repo side: every script compiles, both workflows are
well formed and reference commands that exist, a build is deterministic, the
published copies match their sources, the asset hashes in the HTML match the
files they name, the calendar is RFC 5545 conformant, and no British spellings
or stranded punctuation have crept in. It prints its own pass count.

```bash
python scripts/qa_all.py
```

`site/qa.js` is the browser side: every filter, sort, view, page, guide,
download and persistence path, and it reports its own totals. It is not linked
from the page. Open the site and run it from the console:

```js
await fetch("qa.js").then(r => r.text()).then(eval);
QA.reset(); await QA.runParts(["pages", "views", "chips", "sort"]);
await QA.runParts(["peek", "tracker", "timeline", "eligibility", "exports",
                   "own", "recs", "watch", "prep", "resilience"]);
```

Split into parts because a full run exceeds a single automation call. It checks
things a spot check misses: that every chip's badge count matches the rows it
actually shows, that two chips intersect rather than union, that each sortable
column reverses, that every program opens a peek without throwing, that the
export honors the active filter, and that corrupt localStorage does not break
the page.

One rule encoded in it: never assert on `getBoundingClientRect` for a
CSS-transformed element. It returns stale values under automation while a
screenshot shows the element in its final position.

## Running it locally

No dependencies beyond Python 3.9+, the scripts are stdlib only and the site is
plain HTML, CSS and JavaScript with no build step.

```bash
python scripts/build.py          # validate sources, write data/ and site/data/
python -m http.server -d site    # then open http://localhost:8000
```

Other scripts:

```bash
python scripts/watch.py --links-only   # just check the links
python scripts/try_urls.py cands.txt   # test candidate URLs while curating
```

## Adding or fixing a program

Edit the relevant file in [`data/sources/`](data/sources/) and run
`python scripts/build.py`. The build validates every record and refuses bad dates,
unknown enum values, duplicate ids and relative URLs.

```json
{
  "id": "short-slug",
  "name": "Program name",
  "org": "Institution",
  "city": "City, ST",
  "url": "https://...",
  "tracks": ["pediatrics", "neuroscience"],
  "focus": "One or two sentences on what the program actually is.",
  "duration_weeks": 10,
  "stipend_usd": 5000,
  "housing": "provided",
  "opens": "2026-12-01",
  "deadline": "2027-02-01",
  "deadline_status": "projected",
  "eligibility": {
    "class_years": ["sophomore", "junior"],
    "citizenship": "us-or-pr",
    "min_gpa": 3.0,
    "notes": "Anything disqualifying."
  },
  "requires": ["transcript", "cv", "personal-statement", "2-lor"],
  "selectivity": "high",
  "notes": "Anything worth knowing before applying."
}
```

`deadline_status` must be `confirmed`, `projected`, `unknown` or `rolling`, and
only use `confirmed` for a date read off the program's own page.

## Keeping dates honest

Two scripts do this, and they are deliberately separate:

- `scripts/watch.py` runs weekly and says **which pages changed**.
- `scripts/extract_dates.py` says **what they now say**: it pulls candidate
  deadline sentences off every page so they can be read and promoted by hand.

Nothing promotes a date automatically, because three separate traps turned up in
two sweeps:

- Van Andel's "Feb. 25, 2027" is a **fundraising gala**.
- Children's National's page describes a **fall-spring** internship whose
  deadline passed in August 2026, not a summer program.
- The University of Chicago Pritzker page advertises a **30 November 2026**
  deadline, which would have been the most urgent item on the entire list, but
  the surrounding text shows it is for UChicago's own **medical students**.

Each was caught by reading the sentence around the date. A regex finds the
candidate; a person confirms it.

```bash
python scripts/extract_dates.py          # pages mentioning a 2027 date
python scripts/extract_dates.py --all    # every page
```

## Where to start

1. Read **[the timeline](materials/guides/timeline.md)**: what to do between now
   and February. The first deadline is 4 January, not February.
2. Ask for **letters of recommendation** now. It is the only item that depends
   on someone else, and the first letters are due in January.
3. Start the applications that are **already open**, earliest deadline first:
   Seattle Children's (4 January), the Broad (10 January) and NIH SIP
   (26 January), which is the best fit for living at home in Leesburg. The
   timeline has the rest in date order.
4. **[Cold-email PIs](materials/templates/cold-email-pi.md)**: fifteen minutes
   each, and the thing most likely to change an outcome. At NIH it is part of
   applying, because investigators choose their own interns.
