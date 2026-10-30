# Summer 2027 Research Finder

A searchable database of **85 undergraduate summer research programs**, a
deadline-aware application tracker, a set of application templates, and a watcher
that notices when program pages change.

**→ [Open the site](https://wjed.github.io/jolene-s27/)**

Built around pediatric, neuroscience and clinical research, for a rising senior
applying in the Summer 2027 cycle.

---

## Why this exists

The starting point was a list of 24 programs in Notion. It had the right
instincts — St. Jude, CHOP, Cincinnati Children's, Yale Child Study — but as a
flat list it could not answer the questions that actually matter: *what is open
today, what is due first, what am I not eligible for, and what am I missing?*

This repo answers those, and adds 61 programs that were not on the list.

## What is here

| | |
|---|---|
| **[The site](https://wjed.github.io/jolene-s27/)** | Filterable database, prioritised action plan, application tracker, timeline |
| **[`data/`](data/)** | The dataset: JSON, a CSV export, and an `.ics` calendar with reminders |
| **[`materials/`](materials/)** | CV skeleton, personal statement template, recommendation requests, cold-email template, strategy guides |
| **[`scripts/`](scripts/)** | Build, validate, link-check and watch |

### The site, specifically

- **The plan** — not a list but an ordered set of actions: what is accepting
  applications today, which applications give the best return, what is due in 30
  days, what to do monthly.
- **All programs** — filter by research area, deadline month, housing, stipend,
  citizenship requirement and how competitive it is.
- **My applications** — per-program status, a requirements checklist and notes.
  Stored in the browser only; nothing is uploaded anywhere. Use **Backup** before
  clearing cookies.
- **Timeline** — every opening date and deadline in order.

## The honest part: which dates are real

Of 85 programs, as of **29 October 2026**:

| | |
|---|---|
| **3** | deadline confirmed on the program's own page |
| **53** | projected from a previous cycle — shown with an `est.` marker |
| **27** | nothing posted yet |

This is not sloppiness in the data — it is the actual state of the world in late
October. Most Summer 2027 cycles have not opened. Rather than guess and present
guesses as fact, every date carries its status, and the watcher checks the real
pages weekly.

**Confirmed so far:** Jackson Laboratory 25 Jan 2027 (5pm ET) · St. Jude POE
1 Feb 2027 · NYSCF 15 Mar 2027.

## The watcher

```bash
python scripts/watch.py
```

Fetches all 85 program pages, compares each against the previous run, and reports:

- pages whose content changed since last time
- **pages that have started mentioning 2027** — usually the week the new cycle goes live
- links that broke
- redirects worth folding back into the data

It runs every Monday in GitHub Actions and opens an issue when anything changes.
Running it during the build caught 43 dead or redirected URLs in the first pass.

Exit codes: `0` nothing notable · `1` broken links · `2` changes · `3` both.

## Running it locally

No dependencies beyond Python 3.9+ — the scripts are stdlib only and the site is
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

`deadline_status` must be `confirmed`, `projected`, `unknown` or `rolling` — and
only use `confirmed` for a date read off the program's own page.

## Two entries need a link

Two items came across from the original list without an institution attached and
could not be identified: **"Summer Biomedical Research Program"** and **"PROMISE
— Training in Oncology and Medicine to Inspire Students"**. Both appear in the
site's plan view under *Needs a link*. Finding the original Notion links takes a
minute and both entries can then be filled in properly.

## Where to start

1. Read **[the timeline](materials/guides/timeline.md)** — what to do between now
   and February.
2. Ask for **letters of recommendation** by mid-November. It is the only item
   that depends on someone else.
3. Apply to the **three already open**: Johns Hopkins Pathway, Cincinnati
   Children's SURF, INSPIRE.
4. **[Cold-email PIs](materials/templates/cold-email-pi.md)** — fifteen minutes
   each, and the thing most likely to change an outcome.
