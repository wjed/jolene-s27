# Your Claude kit

Everything Claude needs to help with your applications. You set it up once,
keep the profile it gives you, and you never have to explain yourself twice.

## The one rule

**Every chat, attach two files: `CLAUDE.md` and your latest
`jolene-profile.md`.** Without the profile, Claude knows nothing about you and
would have to ask everything again. After your first chat, "your latest" means
the updated copy Claude gives you at the end of setup, not the blank one that
came in the kit.

To attach a file, click the paperclip or **+** button next to the box where you
type your message, and pick the file from your computer.

## Your first chat: setup, once

1. Download the kit from the site, https://wjed.github.io/jolene-s27/, under
   **Your Claude kit** in the sidebar. Unzip it: on Windows, right-click the zip
   and choose **Extract All**; on a Mac, double-click it. You get a folder
   called `jolene-claude-kit`. Keep it somewhere easy to find, like Documents.
2. Start a new chat at claude.ai or in the Claude app, attach `CLAUDE.md` and
   `jolene-profile.md` from that folder, and say hello.
3. Claude interviews you, in small rounds rather than all at once: your resume,
   details like your GPA and address, who might write your letters, some
   samples of your writing, why pediatrics, what you actually do in the lab,
   and your dates for next summer.
4. **At the end, Claude gives you an updated `jolene-profile.md`. Download it,
   put it in your kit folder, and delete the old one.** Your browser may save
   it as `jolene-profile (1).md`, which is fine, as long as the old one is gone
   and you never attach it by mistake. This is the step that matters: it is
   what stops you being asked the same questions again.
5. Done.

If you have to stop partway, ask Claude for the profile so far and save it the
same way. Next time, it picks up where you left off.

If you would rather fill some blanks in yourself first, you can. Open
`jolene-profile.md` in Notepad (Windows) or TextEdit (Mac) and type over
anything in square brackets. Leave the `setup_completed` line alone: Claude
changes it when setup is done.

## Every chat after that

1. Start a new chat and attach `CLAUDE.md` and your latest `jolene-profile.md`.
   Every time.
2. Say what you want. For example:
   - *"What should I do this week?"*
   - *"Help me apply to the Jackson Lab Summer Student Program."*
   - *"Help me ask my lab supervisor for a letter."*
3. When something changes, like a new GPA or a recommender saying yes, tell
   Claude. It gives you a new profile. Swap it in the same way, so the newest
   one is always the one you attach.

**Rather not attach files every time?** Use a Claude project, which keeps files
that every chat inside it can see. Make one (**Projects** in the sidebar), call
it something like "Summer 2027 applications", and add `CLAUDE.md`, your latest
`jolene-profile.md` and the three skill files to the project's files. Then start
each chat inside the project. Whenever Claude gives you a new profile, delete
the old one from the project's files and add the new one.

## What is in the box

| File | What it is for |
|---|---|
| `CLAUDE.md` | Tells Claude who you are and how to help. **Attach it to every chat.** |
| `jolene-profile.md` | Every fact a form might ask for, and later your personal statement and CV text too. Claude fills it in during setup and gives you an updated copy. **Attach your latest copy to every chat.** |
| `skills/fill-application/SKILL.md` | Fills an application form in your browser from your profile, and stops at anything it should not answer alone |
| `skills/email-a-lab/SKILL.md` | Researches a lab, then drafts a short, specific email to the professor |
| `skills/watch-deadlines/SKILL.md` | Tells you what opened, what changed and what is due soon |
| `README.md` | This page |

## Skills, and how to give them to Claude

A **skill** is a page of instructions for one job: filling in an application,
emailing a lab, or checking deadlines. When Claude has the skill for a job, it
follows those steps, safety stops included. The three skills are the files
called `SKILL.md` inside the `skills` folder, each in a folder named after its
job. If you downloaded them one at a time instead, they may be called
`SKILL (1).md` and so on; the `name:` line at the top of each says which is
which.

**The easy way, which always works:** when you want one of those jobs done,
attach that job's `SKILL.md` along with your two usual files. To fill in an
application, for example, attach `CLAUDE.md`, `jolene-profile.md` and
`skills/fill-application/SKILL.md`.

**The install-once way, if your Claude offers it:** some Claude accounts have a
**Skills** section in **Settings**, under **Capabilities**. If yours does, you
can upload each skill once, and Claude then uses it on its own in every chat.

1. In your kit folder, open `skills` and find the job's folder, for example
   `fill-application`.
2. Turn that folder into a zip. On Windows, right-click it and choose
   **Compress to ZIP file**, or **Send to**, then **Compressed (zipped)
   folder**. On a Mac, right-click it and choose **Compress**.
3. In Claude, open **Settings**, then **Capabilities**, find **Skills**, and
   upload that zip. If it asks you to turn on code execution first, turn it on.
4. Do the same for the other two folders.

If you do not see a Skills section, use the easy way. You lose nothing.

## Filling forms in your browser: Claude in Chrome

Claude can only fill in a form it can see, and a normal Claude chat cannot see
your other browser tabs. For this you need **Claude in Chrome**: an add-on (an
"extension") for the Google Chrome browser, made by Anthropic, the company
behind Claude. It opens a Claude panel beside the page you are on, and from
there Claude can read the page and type into it.

**Setting it up, once:**

1. Use Google Chrome. If you normally use Safari or Edge, install Chrome first.
2. In Chrome, open the Chrome Web Store, search for **Claude**, and add the one
   made by Anthropic. Check the maker's name, because look-alikes exist.
3. Sign in with the same Claude account you use for your chats. It may need a
   paid Claude plan.
4. To keep it handy, click the puzzle-piece icon at the top right of Chrome and
   pin Claude.

**Using it on an application:**

1. Open the application in Chrome and sign in to the portal yourself.
2. Click the Claude icon to open its panel beside the page. Type your requests
   in that panel, not in a claude.ai tab.
3. Give it the same files there: `CLAUDE.md`, your profile and the
   fill-application skill. Attach them, or paste the profile and the skill if
   the panel has no attach button. Then say *"Fill this in from my profile."*
4. The first time Claude works on a new website, it asks your permission. Allow
   it on the application site. Say no anywhere else, such as your email or your
   bank.
5. It fills the repetitive fields, leaves the essays and anything sensitive to
   you, and gives you a list to check. You read it, then you click submit.

**Without Claude in Chrome**, nothing is lost. In a normal chat, paste the
form's questions, or a screenshot of them, and Claude writes every answer for
you to copy in.

## Keeping an eye on deadlines

You do not have to check program pages yourself. The site reads every program
page each Monday, and its **The Plan** page says what changed and when it last
looked: https://wjed.github.io/jolene-s27/

Two catches. A few sites block that automatic check, and The Plan page lists
them, so open those yourself every couple of weeks. And if the date of the last
check is more than a week old, the check has stalled, so ask Claude to look
instead.

**If you would like Claude to tell you each week**, ask it:

> Every Monday at 8am, run the watch-deadlines skill and tell me what changed.

Some Claude apps can run a task on a schedule and some cannot. If Claude says
it cannot, set a weekly reminder on your phone for Monday morning. When it goes
off, start a chat with your two files and the watch-deadlines skill attached,
and say *"Run the weekly deadline check."*

To see every deadline in your own calendar, use **Add to calendar** in the
site's sidebar. It copies the dates as they stand that day, so the site is still
the place to check.

## What Claude will not do, on purpose

- Click submit on an application, or send an email for you. It fills and
  drafts, then hands it back to you to read and send.
- Type a password, a verification code or your Social Security number, or
  create an account for you. It can fill the name and email boxes on a sign-up
  page; you type the password and click the button.
- Make up a GPA, a grade, a date or a recommender. If it does not know, it asks
  you.

What it does do, before filling anything, is check that the program will take
you: your year, any GPA minimum, citizenship, and where you live or study. If
something rules you out, it tells you before you spend an evening on it.

## Two things worth knowing

**Your CITI certificates are an advantage.** You have three, including GCP.
Programs ask whether applicants have human subjects training and most
undergraduates do not. They belong near the top of your CV, and Claude is told
to mention them.

**Lead with the lab, not the EMT work.** The EMT and medical assistant
experience is genuinely unusual and clinical programs should hear about it. But
for research applications, the Depression and Anxiety Lab is the thing that
answers the question they are actually asking, so it goes first.

**Make a research version of your resume.** The one you have now is built for
clinical jobs: the lab is one line near the bottom and your CITI training is
not on it. For these applications the lab goes at the top, with real bullets,
and the CITI certificates go near it. Claude will offer to make it with you,
and it should be ready before your letter requests go out, since it goes in
the packet you send your recommenders.

## If something is wrong

Your profile started from your LinkedIn in October 2026 and was checked against
your resume in November 2026. If a date or a title
is off, tell Claude and it will give you a corrected profile to save, or fix it
in `jolene-profile.md` yourself. That file is the one Claude trusts.
