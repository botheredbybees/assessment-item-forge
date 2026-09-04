# Assessment Item Forge: A Pedagogy-First Moodle Question-Authoring Skill

**Status:** Approved

**Goal:** A reusable Claude Skill that authors Moodle quiz questions across every practical
question type — starting from the pedagogical judgment of *which type actually tests the target
understanding*, not just from the mechanics of generating valid Moodle content.

**Architecture:** One Claude Skill (`SKILL.md`) drives an authoring workflow whose primary unit of
work is **a whole source document in, a whole quiz out** — not one question at a time. Given a
document (a module's lesson text, a wiki page, a Confluence page's content), the skill identifies
the distinct concepts/passages within it worth testing, decides — for the document as a whole, not
independently per fact — a *considered mixture* of question types across those concepts (drawing
on the evidence-grounded rubric in `references/pedagogy.md`, which explicitly treats "does this
quiz's type mixture actually fit what the content offers" as part of the judgment, not just
"which single type fits this one fact"), drafts each question via a small set of Python dataclasses
(`scripts/moodle_xml.py`, one class per question type), enforces mechanical correctness and the
answer-length-distribution rule as *code* across the resulting question set
(`scripts/length_distribution.py`, `scripts/item_sanity_check.py`) rather than as prose the model
must remember mid-draft, and emits a single Moodle XML file — the whole quiz, ready for import via
Moodle's own `qformat_xml` question-bank importer. Moodle XML is used uniformly for every question
type — GIFT is not used at all, since XML is a strict superset of GIFT's capability (every question
type, richer feedback/formatting, no backslash-escaping) with no corresponding downside for an
authoring tool that generates its own source rather than requiring hand-typed syntax.

## Background

This grew directly out of a real incident, not a hypothetical: while executing Phase 3 of the
Nuyina Data Officer Training LMS (a separate, Moodle-based training course — see that project's
own `CLAUDE.md`), three drafted pre-test quizzes shipped with correct answers running 3–6× longer
than their distractors, a live human-review catch during content authoring. This is a textbook
case of **construct-irrelevant variance** (Messick, 1989; via Wiliam's *Balancing dilemmas:
Traditional theories and new applications*) — a feature of the item itself, unrelated to the
knowledge being tested, that lets a test-wise trainee answer correctly without understanding. The
bug existed because the rule ("keep options comparable") lived only as an instruction a model had
to remember while drafting, with nothing mechanically enforcing it before import.

Investigating that bug's fix led to two further, separately valuable findings:

1. Two of Moodle's richer question types — Cloze/Embedded Answers and Ordering — serve pedagogical
   purposes Multiple Choice and True/False structurally cannot: Cloze forces close reading of
   *specific* wording within a passage (catching pattern-matching rather than comprehension),
   Ordering tests whether a trainee can *construct* a correct procedure end-to-end rather than
   recognise one correct step among four given options. Neither is reachable through GIFT, the
   format the Nuyina LMS project currently uses — both need Moodle's native XML question format.
2. Real prior art already exists and is worth building on rather than duplicating:
   [`danielcregg/moodle-mcq`](https://github.com/danielcregg/claude-code-skill-moodle-mcq) (MIT)
   is a mature Claude Skill for Moodle GIFT/XML/Aiken question authoring, with a stronger
   answer-length-balancing rule than the one that would have caught the original bug — it targets
   a **15% shortest / 15% longest / 70% middle** distribution of where the *correct* answer lands,
   computed across a whole question set, which defeats even a "the answer is never the extreme
   option" heuristic. It does not, however, generate Cloze/Ordering/drag-and-drop content despite
   noting XML enables them (confirmed by reading its actual XML template, which only covers
   `multichoice`).
   [`GarethManning/education-agent-skills`](https://github.com/GarethManning/education-agent-skills)
   (CC BY-SA 4.0, 165 evidence-grounded pedagogical skills) has two directly relevant skills in
   its `curriculum-assessment` domain: `assessment-validity-checker` (citing the same Messick 1989
   validity framework behind the bug that started this) and `formative-assessment-technique-selector`
   (citing Black & Wiliam 1998, Wiliam 2011, Heritage 2010) — built for live-classroom technique
   selection, but its reasoning skeleton (match technique to purpose → timing → response format →
   constraints) transfers directly to matching a *question type* to a learning goal.

This project is a fresh build informed by both, not a fork of either — see Licensing below for
why that distinction matters here specifically.

## Goals

1. **Take a whole source document as input and produce a whole quiz as output** — a module's
   lesson text, a wiki page, a Confluence page's exported content — not a tool that authors one
   question at a time on request. The skill identifies what in the document is worth testing and
   drafts a complete question set from it in one pass.
2. **Choose a considered *mixture* of question types across that document**, not just the right
   type for each fact in isolation. A document with a sequential procedure, a passage whose exact
   wording matters, and several factual claims should produce a quiz reflecting that variety —
   Ordering for the procedure, Cloze for the precise wording, Multiple Choice/True-False for the
   facts — rather than defaulting every item to the same type because it's the path of least
   resistance. Judging the *mixture* is itself a pedagogical decision, not a mechanical afterthought
   once each item's type is picked independently.
3. Author across every practical question type (list below), each backed by a clear statement of
   *what kind of understanding it tests* and *when it's the right choice* — not just correct XML
   syntax.
4. Make the answer-length-distribution rule, and other mechanically-checkable correctness
   properties, enforced by code that runs before anything is considered "drafted" — never rules
   that exist only as instructions a model must remember while writing prose.
5. Ship as a real, usable tool from day one (an XML file the skill produces, ready for Moodle's
   own XML question import), not guidance-only — validated by actually authoring real quizzes for
   1–2 modules of the Nuyina Data Officer Training LMS once built (tracked separately — see
   "Follow-on work" below; not part of this project's own scope).
6. Stay self-contained and portable: no dependency on the Nuyina workspace, no assumption about
   which Moodle instance it's pointed at, nothing that couldn't be handed to an unrelated educator
   as-is.

## Non-goals

- **GIFT format support.** Moodle XML covers every question type GIFT does plus everything GIFT
  can't reach, with no corresponding capability GIFT has and XML lacks. Maintaining two output
  paths would be pure duplication for no benefit.
- **Calculated Multi / Calculated Simple / Random Short-Answer Matching in v1.** Calculated
  (plain) is in scope — genuinely useful for numeric/config-value training content — but its two
  close variants and the bank-level "random short-answer matching" meta-type are deferred:
  minor variants of limited additional value, not worth building without a concrete use case
  driving their specific requirements.
- **A hard exclusion of Short Answer or Essay.** Their tradeoffs (exact-match fragility;
  per-attempt manual grading) are real and the skill actively steers authors away from them by
  default — but "broadly useful to other educators" means supporting them when a user judges the
  tradeoff acceptable for their context, not deciding on their behalf.
- **Building `import_xml.php` for the Nuyina Data Officer Training LMS.** That repo's own
  content-authoring pipeline currently imports via GIFT (`import_gift.php`); wiring it to consume
  this project's XML output is real, separate follow-on work, tracked as its own Jira task (see
  below) — not something this spec or its implementation plan builds.
- **A hosted service, web UI, or MCP server.** This is a Claude Skill invoked directly in a
  session with file access — nothing more, at least for v1.

## Question types in scope

Every question type is authored via the same pipeline: a Python dataclass in `scripts/moodle_xml.py`
→ Moodle XML, validated by `scripts/item_sanity_check.py`, with any question offering multiple
distractor-style options additionally checked against `scripts/length_distribution.py`.

**v1 scope:** Multiple Choice, True/False, Numerical, Matching, Description, Short Answer, Essay,
Cloze/Embedded Answers, Drag-and-drop into Text, Drag-and-drop onto Image, Drag-and-drop Markers,
Select Missing Words, Ordering, Calculated.

**Explicitly deferred, not excluded:** Calculated Multi, Calculated Simple, Random Short-Answer
Matching.

## Input

A whole document's worth of content, handed to the skill as plain text (a pasted lesson, a wiki
page body, an exported Confluence page) — the skill does not fetch content itself (no Confluence/
wiki API integration in scope; whatever tool session invokes it is responsible for gathering the
source text first, matching how the Nuyina LMS's own `gather_module_sources.py` already separates
"collect the source material" from "draft from it"). Output is one Moodle XML file: a complete
quiz, not a single question.

## The pedagogical judgment layer

`references/pedagogy.md` holds the evidence-grounded rubric the skill consults before drafting
anything — not a lookup table mapping content-shape to question-type mechanically, but a
reasoning framework adapted from (with full attribution — see Licensing) the matching logic in
`education-agent-skills`' `formative-assessment-technique-selector`: what is actually being
checked (recall, comprehension, procedural construction, precise recall of exact wording), and
what response format that requires. This operates at two levels, not one: per-passage (which type
fits *this* concept) and whole-document (does the resulting quiz's type mixture actually reflect
what the document offered, or has every item defaulted to the same type regardless of what each
passage structurally called for). Concretely, this is where the skill encodes findings like:

- Multiple Choice / True-False test *recognition* — can the trainee identify the correct answer
  among given options — and are vulnerable to construct-irrelevant variance (length, extremity,
  grammatical mismatch between stem and options) if not actively guarded against.
- Cloze forces attention to exact wording within a specific passage, catching a trainee who would
  otherwise pattern-match an MC answer without absorbing the detail.
- Ordering tests whether a trainee can construct a correct procedure end-to-end, closer to
  planning an actual response than recognising one correct step among four.
- Short Answer's exact/wildcard string matching produces false negatives for benign spelling or
  formatting variation; Essay requires per-attempt human grading. Both real, statable tradeoffs
  the skill surfaces rather than either hiding or refusing to support.
- Calculated is appropriate when the learning goal is genuinely computational (apply a formula to
  varying inputs) rather than a static fact wrapped in a number.

`references/moodle-xml-formats.md` holds the mechanical reference: one worked XML template per
question type, in the same spirit as `moodle-mcq`'s own format-reference section but extended to
cover every type in scope here, not just `multichoice`.

## The mechanical/enforcement layer

Three small, focused, independently-testable Python modules — deliberately mirroring the pattern
already proven in the Nuyina Data Officer Training LMS's own `gift_format.py`/
`content_sanity_check.py` (a real prior success this project imitates for its own domain):

- **`scripts/moodle_xml.py`** — one dataclass per question type (`MultipleChoiceQuestion`,
  `TrueFalseQuestion`, `ClozeQuestion`, `OrderingQuestion`, `CalculatedQuestion`, etc.), each with
  a `to_xml()` method, plus a `write_moodle_xml(questions, path)` entry point mirroring
  `write_gift()`'s existing shape. All XML escaping/CDATA-wrapping lives here, once, not
  re-derived per question type.
- **`scripts/length_distribution.py`** — given a set of drafted Multiple-Choice-family questions,
  computes each one's shortest/longest/middle classification for the correct answer and checks
  the aggregate distribution against the 15/15/70 target (adapted from `moodle-mcq`, with
  attribution), returning actionable rebalancing feedback rather than a bare pass/fail.
- **`scripts/item_sanity_check.py`** — structural validation before anything is considered ready
  for import: well-formed XML, no placeholder/stub text (mirroring the existing
  `content_sanity_check.py` pattern), type-specific structural checks (e.g. a Cloze question's
  embedded-answer count matches its blank count, an Ordering question has at least 3 items).

The skill's own prose workflow never re-implements what these modules already check — it calls
them and acts on their output, the same discipline `content_sanity_check.py` already established
for this pattern's first outing.

## Licensing

`GarethManning/education-agent-skills` is CC BY-SA 4.0 — its share-alike clause means a work built
on its content, even a "fresh build informed by" rather than a literal fork, is a derivative work
requiring the same (or a compatible) license and clear attribution. `danielcregg/moodle-mcq` is
MIT, compatible with CC BY-SA as an input.

**Decision:** `assessment-item-forge` is licensed **CC BY-SA 4.0** in full. `ATTRIBUTION.md`
names both source projects explicitly, describing which specific ideas were adapted from each
(the length-distribution target from `moodle-mcq`; the type-selection reasoning skeleton and
evidence-source citations from `education-agent-skills`) rather than a generic "inspired by" note.

## Repo structure

```
assessment-item-forge/
  SKILL.md                       — orchestration + judgment: which type fits, how to frame it, tradeoff warnings
  references/
    pedagogy.md                   — Wiliam/Messick/Black-&-Wiliam grounding, type-selection rubric
    moodle-xml-formats.md          — one worked XML template per question type in scope
  scripts/
    moodle_xml.py                  — one dataclass per question type, all emit Moodle XML uniformly
    length_distribution.py          — 15/15/70 rule enforced as code, adapted from moodle-mcq
    item_sanity_check.py             — structural validation before anything touches Moodle
  tests/
    test_moodle_xml.py
    test_length_distribution.py
    test_item_sanity_check.py
  LICENSE                          — CC BY-SA 4.0 (full text)
  ATTRIBUTION.md                    — credits moodle-mcq and education-agent-skills, specifically
  README.md
```

## Testing / verification

Each Python module gets real unit tests (structural correctness, escaping edge cases, the
length-distribution algorithm's boundary behavior) — this is ordinary, testable code, not content
requiring live human judgment. The skill's own drafting workflow (pedagogical judgment,
question-type selection, actual question wording) is validated the way this pattern was already
validated once before: real use against real content, with a human reviewing the result — in this
case, drafting real Cloze/Ordering/Calculated questions for 1–2 Nuyina Data Officer Training LMS
modules as the first genuine test of the whole pipeline, once the underlying LMS integration
(tracked separately, see below) exists to receive them.

## Follow-on work (explicitly out of this project's scope)

Integrating `assessment-item-forge`'s output into the Nuyina Data Officer Training LMS's own
content-authoring pipeline — building an `import_xml.php` there (mirroring `import_gift.php`'s
existing direct-container-PHP pattern, driving Moodle's `qformat_xml` instead of `qformat_gift`)
so that repo can actually consume this project's XML output — is real work, tracked as Jira task
[NDO-611](https://ausantarctic.atlassian.net/browse/NDO-611) under Epic NDO-513 (the Data Officer
Training LMS's overarching epic), not part of this project's own implementation plan.
