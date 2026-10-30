# Your Claude kit

Everything Claude needs to help with these applications, so you never have
to explain yourself twice. Set it up once and it remembers.

## How this works

**You set it up once.** After that, every chat already knows who you are and
you just ask for what you want.

1. Download the kit and unzip it.
2. Start a Claude chat, attach `CLAUDE.md` and `jolene-profile.md`, and say
   hello.
3. Claude interviews you. It asks for your resume, a few blanks like your GPA
   and address, some samples of your writing, and the things that make an
   application good, such as why pediatrics and what you actually do in the
   lab. It asks in small rounds, not all at once.
4. **At the end it hands you a filled-in `jolene-profile.md`. Save that over
   the old one.** This is the step that matters: it is what stops you being
   asked the same questions again.
5. Done. From then on, just say what you want: *"Help me apply to the Jackson
   Lab Summer Student Program."*

If you would rather fill the blanks in yourself first, you can. Claude will
skip the questions it no longer needs.

## After setup, almost nothing needs maintaining

Tell Claude when one of these changes, and it will give you an updated profile
to save. There is no routine to keep up with.

- Your GPA, once a semester
- A new job, lab role or certification
- A recommender saying yes, or no
- A new version of your resume

Two things look after themselves: which programs have posted their 2027 dates,
via the weekly check, and which applications you have submitted, which the site
remembers.

## What is in the box

| File | What it is for |
|---|---|
| `CLAUDE.md` | Background: who you are, what you are applying to, and how you want to be helped. Attach this every time. |
| `jolene-profile.md` | Every fact a form might ask for. Claude fills this in during setup and hands it back for you to save. |
| `skills/fill-application/` | Fills an application form in the browser from your profile, and stops at anything it should not answer alone |
| `skills/email-a-lab/` | Researches a lab, then drafts a short specific email to the professor |
| `skills/watch-deadlines/` | A weekly check of which programs have posted their 2027 dates |

## Using the skills

A skill is a set of instructions Claude loads when it is relevant, so you do
not have to repeat them.

**If you use Claude projects:** make a project called something like "Summer
2027 applications", add `CLAUDE.md` and `jolene-profile.md` to its knowledge,
and drop the `skills/` folder in. Claude will pick the right one up when it
fits what you asked.

**If you are not using projects:** paste the contents of whichever `SKILL.md`
you need into the chat along with the other two files. Less tidy, works fine.

## Filling forms in the browser

The `fill-application` skill is written for Claude in Chrome, the browser
extension. With it open on an application form you can say *"fill this in from
my profile"* and it will handle the repetitive forty fields while leaving the
essays and anything sensitive to you.

It will not click submit. That is deliberate.

## The weekly check

`watch-deadlines` works as a scheduled task. Ask Claude:

> Every Monday at 8am, run the watch-deadlines skill and tell me what changed.

Most 2027 cycles are not posted yet, so the useful thing is being told the week
a page changes. A quiet week should produce one line.

## Two things worth knowing

**Your CITI certificates are an advantage.** You have three, including GCP.
Programs ask whether applicants have human subjects training and most
undergraduates do not. They belong near the top of your CV, and Claude is told
to mention them.

**Lead with the lab, not the EMT work.** The EMT and medical assistant
experience is genuinely unusual and clinical programs should hear about it. But
for research applications, the Depression and Anxiety Lab is the thing that
answers the question they are actually asking, so it goes first.

## If something is wrong

Everything here was assembled from your LinkedIn in October 2026. If a date or
a title is off, fix it in `jolene-profile.md`. That file is the one Claude
trusts.
