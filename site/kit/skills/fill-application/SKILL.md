---
name: fill-application
description: Fill out a summer research program application in the browser using Jolene's profile. Use when she is on an application form, says "fill this in", "help me apply to X", or pastes a program application URL. Checks eligibility first, handles the repetitive fields, and stops for passwords, essays and anything it should not answer alone.
---

# Filling a research program application

Most of these applications ask the same forty fields. The point of this skill is
that she answers the interesting questions and never retypes her address again.

## Before touching the form

1. **Read her profile.** It is the file that starts with the line
   `# Jolene VanderHeyden: application facts`, usually `jolene-profile.md`, and
   it is the source of truth for every factual field. If it is not in this
   chat, ask for it before anything else. Anything still in square brackets is
   unknown: ask, never guess.
2. **Make sure you can see the form.** Filling it in place needs Claude in
   Chrome, the browser extension. If you cannot see or act on her page from
   this chat, say so in one line and switch to the fallback instead of
   stalling: she pastes the form's questions or a screenshot, you draft every
   answer in the form's order, and she copies them in.
3. **Check eligibility**, as below, before filling a single field.
4. **Read the program's own page.** You need the deadline, with its time of day
   and time zone, what they ask for, and at least one faculty member or
   research area to name later.
5. Say what you are about to do in one line, then start.

## Checking eligibility

Look the program up in https://wjed.github.io/jolene-s27/data/programs.json,
in its `eligibility` block and `notes`, then on the program's own page, and
compare with the profile:

- **Year.** `class_years` means her year when she applies, which is junior
  this cycle. In summer 2027 she is a rising senior, graduating in May 2028.
  Match that against however the page words it.
- **GPA.** Compare any minimum with her cumulative GPA, and with her science
  GPA when the floor covers math or science courses too. An empty `min_gpa`
  means none is recorded, not that there is none. If her GPA is still a
  placeholder in the profile, say the floor cannot be checked and ask her.
- **Citizenship.** She is a US citizen, so this never rules her out. Do not
  raise it.
- **Residency or home school.** Some programs take only residents of one city
  or state, or only students of the host or partner universities. Her
  permanent address is in Leesburg, Virginia, and she studies at Penn State,
  in Pennsylvania.
- **Anything else the page requires**, such as prior research experience (hers
  is human-subjects psychology, so a demand for bench or wet-lab experience is
  a real question), fixed start dates (check *Constraints for summer 2027*), or
  being enrolled after the summer.

Then say where she stands, in one line, before filling anything:

- Nothing conflicts: *"Nothing in the program's data or on its page rules you
  out."* Never "you qualify", since only the program can say that.
- Something conflicts: name it, quote where it is written, and ask whether she
  still wants to apply. Fill nothing until she says yes.

Fit is a separate question. A program built for students heading to a PhD is a
weaker fit if the career goal in her profile is MD only. Mention it once; it is
her call.

## What she does herself, never you

These are not things to ask permission for. They are hers.

- **Passwords and accounts.** Most portals want an account before the form.
  You may fill the plain fields of a sign-up page from the profile: her name,
  email, phone and address. Then stop. She chooses and types the password,
  answers any security questions, enters any code sent to her email or phone,
  and clicks the button that creates the account. When you reach a sign-in
  page, say in one line that she needs to sign in, and wait. Never type a
  password and never ask for one. If she pastes one into the chat, say you
  will not use it.
- **Submitting.** Never click submit, or anything else that sends the
  application. Saving a draft is fine.
- **Signatures and certifications.** "I certify that" boxes, typed-name
  signatures and agreements to terms are hers to tick or type.
- **Money and ID numbers.** Application fees, card or bank details, and her
  Social Security number. She enters those herself.

## What you fill without asking

Anything that is a plain fact already in the profile:

- Name, pronouns, email (the one the profile says to put on applications),
  phone, address, citizenship, date of birth, student ID, emergency contact,
  languages
- School, major, minor, expected graduation, class standing
- Employment and research history: titles, employers, locations, dates, and
  the supervisors and hours a week where the profile has them
- Certifications, including the credential IDs in the profile
- Courses and grades, exactly as the *Science coursework* table has them
- Research interests, when the field is a free-text box and you can draw on the
  interests section of the profile

Fill these in, then tell her what you filled so she can scan it.

## What you never fill without asking

Stop and ask when a field wants:

- **GPA**, unless it is written in the profile. Never estimate it.
- **Transcripts or file uploads.** Tell her which file is needed, by the name
  in the profile's *Documents* table, and let her attach it.
- **A reference's contact details**, unless the profile's *Recommenders* table
  shows that person agreed. Listing someone who has not said yes is worse than
  leaving it blank.
- **Demographic questions**: race, ethnicity, gender identity, disability,
  veteran status, first-generation or income status. Hers to answer on every
  form. Never infer them, and never carry an answer over from another form.
  Pronouns from the profile are fine.
- **Any question where the honest answer is unknown to you**, such as whether
  she can start on a specific date or attend a particular orientation. Check
  *Constraints for summer 2027* first.

When she answers something that will come up again, such as a supervisor's
phone number, offer to add it to the profile, and hand her the updated file at
the end.

## The essay fields

These are the only part worth real time.

**Personal statement.** Her master version is in the profile, under *Master
personal statement*. Paste it, then adjust length to the word limit. Do not
rewrite it for each program. If that section is still a placeholder, stop at
this field and say so, then offer to write the master with her first, using the
site's guide at https://wjed.github.io/jolene-s27/#guide/personal-statement,
and to put it in the profile so every later application reuses it. Never write
a one-off statement for a single program.

**Why this program.** This one is written fresh every time. It must name
something that exists only at this program: a named faculty member, a center, a
specific resource, the structure of the summer. If the program page lists
mentors, pick two or three whose work genuinely connects to developmental
psychology, pediatrics or mood disorders, read one abstract each, and reference
the actual finding rather than the title. If a mentor has agreed to host her,
which her profile's *Programs* notes will say, write it plainly: "Dr. X has
agreed to host me."

If you cannot find a mentor list, say so rather than writing a vague paragraph.

**Research experience.** Lead with the Depression and Anxiety Lab: participant
sessions, data coding, technology-based emotion tracking, and her own detail
from *What she runs herself* when the profile has it. Mention the CITI human
subjects training, because most undergraduate applicants do not have it.

**Short answers** such as career goals or why research: draw on *Research
interests, in her words*. Use the real reason only if the profile says it can
go in essays.

## Before she submits

Never click submit yourself. When the form is complete:

1. List every field you filled, grouped as "facts" and "writing".
2. List anything you left blank and why.
3. Flag anything you were unsure about.
4. Give the deadline again, with its time and time zone.
5. Tell her to read it, then submit it herself.

## After she submits

Remind her to set the status on the tracker at
https://wjed.github.io/jolene-s27/ so the board stays accurate, and to check
whether recommenders got their link. Several programs only email the
recommender after the student's part is submitted.

## Worth knowing

A few programs have quirks that catch people out. Confirm each on the page:

- **St. Jude POE**: wants research experience already, a 3.40 GPA overall and
  in math and science, and a start on one of four fixed dates (May 10, May 17,
  May 24 or June 1, 2027). The deadline covers letters and transcripts too, not
  just the form, and St. Jude has asked for credentials by mid-to-late
  December, so she should submit her part without waiting for letters.
- **NIH SIP**: closes at noon Eastern, with letters due about a week later. Its
  investigators pick their own interns, so emailing NIH labs (`email-a-lab`) is
  part of applying, not an extra.
- **Jackson Lab SSP**: closes at 5 p.m. Eastern.
- **MSK MBSP**: closes at 8:00 a.m., not end of day.
- **Seattle Children's**: closes at 5 p.m. Pacific, which is 8 p.m. Eastern.
- **Penn SUIP**: letters must arrive by the application deadline itself.
- **Amgen Scholars**: each host university runs its own application, with its
  own letter requests.
- **Vanderbilt VSSA**: each track has its own deadline; check the one she picks.
- **Caltech SURF**: the application is a research proposal written with a
  prospective mentor, so it cannot be done in one sitting.
