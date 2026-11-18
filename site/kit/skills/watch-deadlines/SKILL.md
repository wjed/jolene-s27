---
name: watch-deadlines
description: Check which summer 2027 programs have posted new dates or opened their applications, and report what changed and what is due soon. Use weekly as a scheduled task, or when Jolene asks what is due soon, what opened, or what she should do this week.
---

# Watching the deadlines

The site already reads every program page each Monday and publishes what it
saw. Start from that rather than opening every page yourself: a chat cannot
reliably read that many pages, some sites block automated readers, and a blocked
page looks exactly like an unchanged one. The useful work is noticing the week a page
changes, because that is almost always the week the new dates appear, and then
reading the few pages that matter by hand.

## What to do

1. **Read the weekly check.** Fetch
   https://wjed.github.io/jolene-s27/data/watch.json. In it, `last_run` is the
   date of the latest check, `changes` lists pages whose text changed,
   `blocked_pages` lists sites that refused the automatic reader, and
   `checked`, `ok`, `blocked` and `broken` count the pages. The `changes` list
   can be cut short, so do not read it as complete. If `last_run` is more than
   eight days before today, the check has stalled: say so, and open by hand the
   page of every program she is applying to.
2. **Read the dates.** Fetch
   https://wjed.github.io/jolene-s27/data/programs.json and take every number
   from it, never from memory. Against today's date, pick out what is open now,
   what is due in the next 21 days and what opens in the next 14. Only a
   `deadline_status` of `confirmed` was read off the program's own 2027 page;
   `projected` is last year's date carried forward, `unknown` means nothing is
   posted, and `rolling` means there is no fixed deadline.
3. **Open by hand only the pages that matter**, among the programs in her
   profile, or the soonest ones if she has not picked any: those in `changes`
   or `blocked_pages`, those whose `opens` date has just passed, and those whose
   deadline is not yet `confirmed`. Once a month, also open the `rolling`
   entries, which are mostly directories that keep adding openings. On each
   page, look for:
   - a 2027 date that was not there before
   - "applications are open" or "applications are closed"
   - a changed deadline, or a time of day added to one
4. **Report only what changed**, plus anything due within 21 days. If nothing
   changed, say so in one line.

If you cannot open those links from this chat, say so in one line and ask her
to open The Plan page at https://wjed.github.io/jolene-s27/ and tell you what it
shows, or to download the spreadsheet from the site's sidebar (Export
spreadsheet) and attach it.

## Reading a program page

The dates on these pages are not all deadlines, and this is where it goes
wrong. Three real examples from building this list:

- Van Andel Institute's "Feb. 25, 2027" is a fundraising gala.
- Children's National's page describes a fall-spring internship whose deadline
  passed in August 2026, not a summer program.
- The University of Chicago Pritzker page advertises a 30 November 2026
  deadline, which is for UChicago's own **medical students**.

So: find the date, then read the sentence around it. A date with no sentence
claiming it is an application deadline is not one. The site's guide has more on
this, at https://wjed.github.io/jolene-s27/#guide/reading-a-program-page.

## What to report

Keep it short. For each change:

- Program name and institution
- What changed, in one line
- The deadline, with its time of day if the page gives one, and whether it is
  confirmed on the page or still projected
- A link

A page the automatic check could not read is "could not be checked", never
"unchanged". If one of hers is on that list and you could not open it either,
tell her to look at it herself.

Then a single closing line: what, if anything, she should do this week. Until
two recommenders in her profile have agreed, that line is about letters.

## Priorities to weigh

Flag these harder than the rest:

- Anything now due within 21 days
- Letters, until two recommenders have agreed
- The one-application-many-labs programs, because they are the best return on a
  single essay: NIH SIP, the Leadership Alliance and Vanderbilt's VSSA. Amgen
  Scholars is close but not the same: each host university takes its own
  application, with its own letter requests, so every extra host is real work.
- Fred Hutch SURP, which is restricted to rising seniors, so 2027 is the only
  year she can apply
- Anything that has just opened, since applying early costs nothing

## Setting it up as a scheduled task

Some Claude apps can run a task on a schedule and some cannot. If this one can,
the useful phrasing is something like:

> Every Monday at 8am, run the watch-deadlines skill and tell me what changed.

If it cannot, say so plainly rather than agreeing to something that will not
happen, and suggest a weekly phone reminder for Monday morning instead. When it
goes off, she starts a chat with her two files and this skill attached and says
"Run the weekly deadline check." Either way, the site's own Monday check keeps
running, and The Plan page shows its latest result.

It only needs to say something when something happened. A quiet week should
produce one line, not a report.
