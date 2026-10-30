---
name: watch-deadlines
description: Check which summer 2027 programs have posted new dates or opened their applications, and report what changed. Use weekly as a scheduled task, or when Jolene asks what is due soon, what opened, or what she should do this week.
---

# Watching the deadlines

As of late October 2026, most Summer 2027 cycles are not posted yet. Of 104
programs tracked, 16 have a confirmed deadline, 48 are projected from last
year, and 37 have nothing posted. The useful work is noticing the week a page
changes, because that is almost always the week the new dates appear.

Run this weekly. Monday morning is a good slot.

## What to do

1. Fetch https://wjed.github.io/jolene-s27/data/programs.json
2. Work through programs where `deadline_status` is `projected` or `unknown`,
   plus anything whose `opens` date has just passed.
3. For each, open the program page and look for:
   - a 2027 date that was not there before
   - "applications are open" or "applications are closed"
   - a changed deadline
4. Report only what changed. If nothing changed, say so in one line.

## Reading a program page

The dates on these pages are not all deadlines, and this is where it goes
wrong. Three real examples from building this list:

- Van Andel Institute's "Feb. 25, 2027" is a fundraising gala.
- Children's National's page describes a fall-spring internship whose deadline
  passed in August 2026, not a summer programme.
- The University of Chicago Pritzker page advertises a 30 November 2026
  deadline, which is for UChicago's own **medical students**.

So: find the date, then read the sentence around it. A date with no sentence
claiming it is an application deadline is not one.

## What to report

Keep it short. For each change:

- Program name and institution
- What changed, in one line
- The deadline, and whether it is confirmed on the page or still projected
- A link

Then a single closing line: what, if anything, she should do this week.

## Priorities to weigh

Flag these harder than the rest:

- Anything now due within 21 days
- The one-application-many-labs programs, because they are the best return on a
  single essay: NIH SIP, Amgen Scholars, the Leadership Alliance, Vanderbilt
- Fred Hutch SURP, which is restricted to rising seniors, so 2027 is the only
  year she can apply
- Anything that has just opened, since applying early costs nothing

## Setting it up as a scheduled task

Ask Claude to run this weekly. The useful phrasing is something like:

> Every Monday at 8am, run the watch-deadlines skill and tell me what changed.

It only needs to say something when something happened. A quiet week should
produce one line, not a report.
