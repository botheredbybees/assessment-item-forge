---
name: assessment-item-forge
description: Given a whole source document (a lesson, a wiki page, exported Confluence content), produces a whole Moodle quiz -- a deliberate mixture of question types chosen by pedagogical judgment, drafted via tested Python code, validated before anything is considered finished. Use when asked to write quiz questions, a test, or an assessment from a piece of content, especially for a Moodle course.
---

# Assessment Item Forge

## What this does

Takes a whole document and produces a whole quiz: one Moodle XML file containing a deliberately
mixed set of question types, chosen because they fit what the document actually offers — not
because Multiple Choice is the easiest type to default to.

## Workflow

1. **Read the source document in full.** It's handed to you as plain text — a pasted lesson, a
   wiki page body, exported Confluence content. This skill does not fetch content itself.

2. **Identify what's worth testing.** Look for: standalone facts (candidates for Multiple
   Choice/True-False), passages where exact wording matters (candidates for Cloze), sequential
   procedures (candidates for Ordering), many-to-many factual mappings (candidates for Matching),
   numeric/computational relationships (candidates for Calculated), and anything spatial/visual if
   the document describes a diagram or layout (candidates for the drag-and-drop family).

3. **Decide the type mixture for the whole document before drafting any single question.** Read
   `references/pedagogy.md`'s rubric and worked example. A document offering a sequence, a precise
   term, and several facts should produce a quiz using more than one type — the mixture itself is
   a judgment call, not an afterthought once each item's type is already picked independently.

4. **Draft each question using the dataclasses in `scripts/moodle_xml.py`.** See
   `references/moodle-xml-formats.md` for what each type actually requires. Never hand-write
   Moodle XML directly — always go through a dataclass's `.to_xml()`.

5. **Run the length-distribution check** (`scripts/length_distribution.py`'s `check_distribution()`)
   against every Multiple-Choice-family question drafted so far, once there are at least 5 of
   them. If it reports `"fail"`, act on its `suggestions` before continuing — this is a mechanical
   check, not a suggestion to override with your own judgment about "this one's fine."

6. **Run the structural sanity check**:
   ```bash
   python3 -m scripts.item_sanity_check <quiz.xml>
   ```
   Fix any reported problem and re-run until it prints `OK`. Do not consider a quiz finished while
   this reports problems.

7. **Assemble and write the final file** via `scripts/moodle_xml.py`'s `write_moodle_xml()`.

8. **Tell the user what to do next**: import the resulting XML file into their Moodle instance via
   Site administration → Question bank → Import → Moodle XML format, then link the imported
   questions into a real Quiz activity (this skill produces question-bank content, matching every
   other Moodle-XML-import workflow — it does not create Quiz activities or course structure
   itself, since that's specific to each Moodle instance's own course setup).

## What this skill will not do without being asked

Default to Short Answer or Essay. Both are supported (see `references/pedagogy.md` for the
tradeoffs) but this skill actively steers toward other types unless the tradeoff is explicitly
accepted for the case at hand.

## Reference material

- `references/pedagogy.md` — the evidence-grounded rubric for which type(s) fit a given piece of
  content, and for judging a whole quiz's type mixture.
- `references/moodle-xml-formats.md` — the mechanical XML shape of every supported question type.
