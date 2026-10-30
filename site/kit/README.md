# Your Claude kit

Four files that give Claude everything it needs to help with these
applications, so you never have to explain yourself twice.

## The five minute version

1. Download the kit and unzip it.
2. Fill in the `[ ]` blanks in `jolene-profile.md`: email, phone, address, GPA.
   Takes two minutes. Claude is told never to guess these, so a blank means it
   will stop and ask rather than invent something.
3. Start a Claude chat and attach `CLAUDE.md`, `jolene-profile.md`, and your
   resume.
4. Say what you want. For example: *"Help me apply to the Jackson Lab Summer
   Student Program."*

That is enough to be useful immediately.

## What is in the box

| File | What it is for |
|---|---|
| `CLAUDE.md` | Background: who you are, what you are applying to, and how you want to be helped. Attach this every time. |
| `jolene-profile.md` | Every fact a form might ask for, in one place. Fill in the blanks once. |
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
