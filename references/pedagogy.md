# Pedagogy: choosing question types and mixtures

Adapted, with attribution (see `ATTRIBUTION.md`), from `education-agent-skills`'
`curriculum-assessment/formative-assessment-technique-selector` and
`curriculum-assessment/assessment-validity-checker`.

## The core question, at two levels

**Per-passage:** what is actually being checked — recall of a fact, recognition among options,
comprehension of exact wording, procedural construction, or computation? Different question types
test different things structurally, not just by convention.

**Whole-document:** does the resulting quiz's *mixture* of types actually reflect what the source
document offered, or has every item defaulted to the same type regardless of what each passage
structurally called for? A document containing a sequential procedure, a passage whose precise
wording matters, and several standalone facts should produce a quiz using more than one type.

## Evidence foundation

- Black, P., & Wiliam, D. (1998). Assessment and Classroom Learning. *Assessment in Education*.
  Established formative assessment as high-leverage (effect size 0.4–0.7), but crucially defined
  it by function (evidence used to adapt teaching), not form.
- Wiliam, D. (2011). *Embedded Formative Assessment*. Operationalised formative assessment into
  five strategies: clarifying intentions, engineering discussions, providing feedback, activating
  peers as resources, activating learners as owners of their own learning.
- Wiliam, D. *Balancing dilemmas: Traditional theories and new applications*, drawing on Messick,
  S. (1989), *Validity in educational measurement: a unified validity framework*. Introduces
  construct-irrelevant variance — a feature of the item itself (length, extremity, grammatical
  mismatch between stem and options), unrelated to the knowledge being tested, that lets a
  test-wise respondent answer correctly without understanding. This is the framework behind
  `scripts/length_distribution.py`.
- Heritage, M. (2010). *Formative Assessment: making it happen in the classroom*. Distinguished
  planned (designed in advance) from interactive (responsive, in-the-moment) formative assessment.
- Bonner, S. M. (2009). Investigating teacher use of practice tests for formative purposes.
  *Journal of MultiDisciplinary Evaluation*, 6(12), 125–128. Formative, retakeable practice with
  real feedback shows learning gains sustained well beyond the assessment itself.

## Type-selection rubric

| What's being checked | Question type | Why |
|---|---|---|
| Recognition among given options | Multiple Choice, True/False | Fastest to answer and grade, but vulnerable to construct-irrelevant variance (length, extremity) if not actively guarded against — see `scripts/length_distribution.py`. |
| Exact wording within a specific passage | Cloze | Forces attention to precise phrasing, catching a respondent who would otherwise pattern-match an MC answer without absorbing the detail. |
| Constructing a correct procedure end-to-end | Ordering | Tests planning/sequencing, not recognition of one correct step among four given options. |
| A many-to-many factual mapping | Matching | Tests the mapping itself, not recall of one pair in isolation. |
| A numeric/computational relationship with varying inputs | Calculated | Appropriate when the learning goal is genuinely computational — applying a formula, not a static fact wrapped in a number. |
| Spatial/visual mapping | Drag-and-drop onto Image, Drag-and-drop Markers | Tests whether a respondent can locate/label something in a real spatial layout, not just name it in the abstract. |
| A short, unambiguous factual answer, exact spelling tolerable | Short Answer | Real tradeoff: exact/wildcard string matching produces false negatives for benign spelling/formatting variation. Steer toward Multiple Choice unless the exactness itself matters. |
| Extended, open-ended reasoning | Essay | Real tradeoff: requires a human to manually grade every attempt. Steer away from it for retakeable/self-directed formative use unless grading capacity genuinely exists. |
| Pure informational content, no question | Description | Not gradable — use only for section-introduction-style content within a quiz, never to fill a question count. |

## A worked example of the mixture judgment

A document describing a multi-stage pipeline (raw file → parser → database → dashboard), where
one stage's exact config field name matters and the overall sequence matters, should *not* produce
four Multiple Choice questions asking "which stage does X" four separate ways. A better mixture:
one Ordering question (sequence the four stages), one Cloze question (fill in the exact config
field name within a sentence quoting the real config), and one or two Multiple Choice questions
for standalone facts the document also covers. This is a judgment call the skill makes explicitly,
not a mechanical rule — see `SKILL.md`'s workflow.
