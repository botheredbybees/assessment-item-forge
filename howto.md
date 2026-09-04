# How to use Assessment Item Forge

This guide is for the person directing Claude, not for someone reading the code. If you're an
educator, trainer, or course author who wants Claude to turn a piece of content into a Moodle
quiz, this is for you.

## What you get

Hand Claude a document — a lesson, a wiki page, a policy, a set of lecture notes — and it will
produce one file: a Moodle-XML quiz made of a deliberately varied mix of question types, chosen
because they fit what your document actually contains, not because Multiple Choice is the easiest
default. You import that one file into Moodle's question bank and you have a quiz.

## 1. Install the skill

You need [Claude Code](https://claude.com/claude-code) (or another tool that loads custom Claude
Skills from a `.claude/skills/` folder).

**For one project** — put the skill inside that project's own repo:

```bash
git clone https://github.com/botheredbybees/assessment-item-forge.git .claude/skills/assessment-item-forge
```

**For every project on your machine** — put it in your personal skills folder instead:

```bash
git clone https://github.com/botheredbybees/assessment-item-forge.git ~/.claude/skills/assessment-item-forge
```

Either location works the same way — pick whichever matches how you use Claude Code day to day.
Restart Claude Code (or start a new session) after cloning, so it picks up the new skill.

## 2. Ask for a quiz

Open a Claude Code session and give it your source content plus what you want. For example:

> "Here's our onboarding page on shift handover procedure [paste the content]. Turn this into a
> quiz."

or, pointing at a file already on disk:

> "Read `docs/onboarding/shift-handover.md` and write a quiz from it."

Claude will read the whole document, decide which question types actually fit what's in it (a
sequence of steps might become an Ordering question, a precise term might become a Cloze
question, a handful of standalone facts might become Multiple Choice), draft every question, run
its own automatic checks, and write out one XML file — tell Claude where you'd like it saved if
you care, otherwise it will pick a sensible name and location and tell you where to find it.

**What to expect in the mix:** by design, the skill leans away from Short Answer and Essay
questions unless you specifically ask for them — Short Answer does brittle exact-text matching
(a correct-but-differently-typed answer gets marked wrong) and Essay needs a human to grade every
attempt by hand. If your use case genuinely needs one of those two types, just say so.

## 3. Import the quiz into Moodle

1. Log in to your Moodle site as a user with question-bank editing rights.
2. Go to your course, then **Site administration → Question bank → Import** (or, from a course
   page, **More → Question bank → Import**).
3. Under "File format," choose **Moodle XML format**.
4. Choose the **Category** the questions should be imported into (create a new one first if you
   want this batch kept separate — a category named after the source document works well).
5. Drag the XML file Claude produced into the file-upload box, or click to browse and select it.
6. Click **Import**. Moodle will show you a preview of every question it parsed — check the count
   matches what you expected, then confirm.
7. The questions now live in your question bank. To actually give the quiz to students, create or
   open a **Quiz activity** in your course and add the imported questions to it from the question
   bank (this step is the same as adding any other questions — the skill produces question-bank
   content, it doesn't create the Quiz activity itself, since that's specific to your course's own
   structure).

**Expected outcome at each step:** a successful import shows a green "importing X questions from
file" summary listing every question's name and type, with no red error rows. If you see a red row
for a specific question, note its name — the sanity check described below should have already
kept this from happening, but Moodle's own importer is the final word.

## 4. Trust, but read it over

The skill runs its own mechanical checks before it ever hands you the file — well-formed XML, no
leftover placeholder text, no structurally broken question — so a file it produces should import
cleanly. That's not the same as pedagogically finished:

- **Read every question once yourself.** Automatic checks catch broken XML and lazy answer-length
  patterns; they don't catch a question that's technically fine but doesn't actually test anything
  useful.
- **Spot-check any Calculated question especially closely.** It's the one question type in this
  skill that hasn't been verified end-to-end against a real Moodle import (see
  `references/moodle-xml-formats.md` for the full detail on which types are verified how) — cheap
  insurance is trying one in your own Moodle instance before relying on a whole set of them.
  Manually testing this once per Moodle version is enough — the format itself doesn't change
  between quizzes.
- **Drag-and-drop-onto-image and drag-markers questions need a real image.** If your source
  document describes a diagram or photo, tell Claude where to find the actual image file — the
  skill can't invent a background image from a text description alone.

## Getting a better result

The skill can only work with what's in your document. A source that already has some natural
structure — a numbered procedure, a term that's defined precisely, a handful of distinct facts —
gives Claude real material to build a varied quiz from. A single dense, unstructured wall of text
will still produce a quiz, but a more repetitive one (mostly Multiple Choice, since that's the
type recall-style content most easily supports). If you want a specific mix — "make sure there's
an Ordering question about the procedure" — just ask; the skill takes direction well.

## If something goes wrong

- **Claude reports the sanity check failed and won't finish:** this is working as intended — it
  means a real structural problem was caught before you ever saw the file. Ask Claude what the
  check reported and let it fix the problem; don't ask it to skip the check.
- **Moodle's import rejects a question the skill said was fine:** this is worth reporting — please
  open an issue at <https://github.com/botheredbybees/assessment-item-forge/issues> with the
  question type involved and, if you're comfortable sharing it, the XML snippet that failed.
- **You want a question type this skill doesn't support, or want to change how it decides the
  type mixture:** also worth an issue — this is a young project and real usage is exactly what
  should shape it next.

## License

This project is CC BY-SA 4.0 — see `LICENSE` and `ATTRIBUTION.md`. You're free to use, adapt, and
share it, including commercially, as long as you credit it and share adaptations under the same
license.
