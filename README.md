# Assessment Item Forge

A Claude Skill that takes a whole source document — a lesson, a wiki page, a Confluence page's
content — and produces a whole Moodle quiz: a deliberate mixture of question types chosen by
pedagogical judgment, not just the mechanically-easiest type for each fact.

See `docs/superpowers/specs/2026-09-04-assessment-item-forge-design.md` for the full design, or
`howto.md` if you just want to install and use it.

## What it does

Given source text and a learning goal, the skill:

1. Identifies what in the document is worth testing.
2. Decides a considered *mixture* of question types across the whole document — informed by
   `references/pedagogy.md`'s evidence-grounded rubric — rather than defaulting every item to
   Multiple Choice.
3. Drafts each question via `scripts/moodle_xml.py`'s dataclasses.
4. Enforces mechanical correctness (`scripts/item_sanity_check.py`) and the answer-length
   distribution rule (`scripts/length_distribution.py`) as code, not as instructions a model has
   to remember while drafting.
5. Emits one Moodle XML file — the whole quiz — ready for import via Moodle's own XML question
   importer (Site administration → Question bank → Import → Moodle XML format).

## Question types supported

Multiple Choice, True/False, Numerical, Matching, Description, Short Answer, Essay, Cloze/Embedded
Answers, Drag-and-drop into Text, Drag-and-drop onto Image, Drag-and-drop Markers, Select Missing
Words, Ordering, Calculated.

## Development

```bash
pip install pytest
pytest tests/ -v
```

No external dependencies for the runtime code — only the standard library.

## License

CC BY-SA 4.0 — see `LICENSE` and `ATTRIBUTION.md`.
