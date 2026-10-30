# Reading a program page in five minutes

Program pages bury the things that decide whether an application is worth
starting. This is the order to look for them.

---

## The five disqualifiers — check these first

Before reading a single word about the research, find:

1. **Citizenship requirement.** "US citizen or permanent resident" appears on
   most federally funded programs. Non-negotiable.
2. **Class year.** Look for "rising senior", "must have completed sophomore
   year", "may not graduate before/during the program". Fred Hutch and Seattle
   Children's both have hard rules here that point in opposite directions.
3. **GPA minimum.** Often in a FAQ rather than the main page.
4. **Dates.** Fixed start dates (St. Jude has four and only four), and whether
   the full term is mandatory.
5. **Deadline, and what it covers.** Specifically: are letters due on the same
   date, or later? St. Jude's deadline includes credentials. The Broad gave
   letters two extra days.

If any of these rule you out, stop. That is a win — four hours saved.

## Then find the mentor list

The most valuable page on any program site, and often two clicks deep:
"Faculty", "Mentors", "Research areas", "Labs", or a PDF of last year's projects.

This is where the [why-this-program paragraph](../templates/why-this-program.md)
and the [cold emails](../templates/cold-email-pi.md) come from. A program with no
published mentor list is one where naming a mentor matters less — and a program
with a long list is one where naming a mentor matters a great deal.

## Then the practicalities

- **Stipend** — and whether housing is separate. A $7,500 stipend with housing
  included (Jackson Lab) is worth far more than $5,000 with no housing in Boston.
- **Housing** — provided, subsidised, or your problem.
- **Travel** — Jackson Lab and several others reimburse it; most do not.
- **Length** — nine to eleven weeks, and whether it collides with anything.

The dataset already has all of this, but verify it on the page before applying —
the stipend figures in particular are the fields most likely to be stale.

## Signs the page is from a previous cycle

Important right now, because most 2027 pages have not been updated:

- Dates in 2025 or 2026 with no mention of 2027
- "Applications are closed", "check back in the fall", "will open in November"
- A deadline that has already passed

None of these mean the program is gone. They mean the new cycle is not posted.
Note the date, and let the watcher catch the update:

```bash
python scripts/watch.py
```

It flags any page that changes, and specifically any page that *starts*
mentioning 2027 — which is almost always the week the new cycle goes live.

## When the page says almost nothing

Some real programs have one thin paragraph and an email address. That is not a
bad sign — it often means placements are arranged directly rather than through a
portal, which is good news for anyone willing to write an email.

In that case skip the application entirely and go straight to a
[cold email](../templates/cold-email-pi.md) to the listed contact or to a
relevant PI. The NIA Alzheimer's centers, UCSF pediatrics and the UC Davis MIND
Institute all work this way.
