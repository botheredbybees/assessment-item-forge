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
- Eysenck, M. W., & Keane, M. T. (2015). *Cognitive Psychology: A Student's Handbook*. Taylor &
  Francis Group. The testing effect and retrieval practice: the act of recalling information,
  not just re-reading it, is what strengthens the memory trace. This is the memory-science
  mechanism underneath Bonner's empirical finding above — it's *why* a retakeable quiz outperforms
  passive review, not just evidence that it does.
- Krieglstein, F., Beege, M., Rey, G. D., Ginns, P., Krell, M., & Schneider, S. (2022). A
  systematic meta-analysis of the reliability and validity of subjective cognitive load
  questionnaires in experimental multimedia learning research. *Educational Psychology Review*,
  34(4), 2485–2541. Cognitive Load Theory's three-part split — intrinsic (the material's own
  complexity), extraneous (complexity added by how it's presented), germane (effort spent
  building understanding) — is distinct from construct-irrelevant variance above but related: a
  cluttered stem or an option padded with irrelevant detail adds extraneous load on top of
  whatever construct-irrelevant cue it introduces. Keep stems and options as plain as the content
  allows; every word that isn't carrying the question's actual content is a tax on both.
- Remesal, A., Corral, M. J., García-Mínguez, P., Domínguez, J., SanMiguel, I., Macsotay, T., &
  Suárez, E. (2023). Certainty-based self-assessment: a chance for enhanced learning engagement in
  higher education. In D. Guralnick (Ed.), *Creative Approaches to Technology-Enhanced Learning
  for the Workplace and Higher Education* (pp. 689–696). Springer Nature Switzerland AG.
  Certainty-Based Marking pairs an answer with a confidence rating so a confident-but-wrong answer
  is scored differently from an unsure-but-wrong one — the two are not the same failure. This
  skill doesn't implement CBM mechanically (Moodle's native question types don't support a
  confidence sub-response), but it motivates the distractor-design guidance immediately below:
  a distractor a confident respondent would pick is a more serious design flaw than one nobody
  would ever choose.
- Zascerinska, J., Scheepers, J., & Kühn, M. (2024). Multi-Sided Evaluation of Needs of TVET
  Students in Problem-Solving Skills in South Africa. In M. Gessler et al. (Eds.), *Expanding
  Horizons, Internationale Berufsbildungsforschung* (pp. 119–126). Springer Fachmedien Wiesbaden.
  A concrete technique for scenario-style questions: name the specific problem-solving skill an
  item is meant to test *before* drafting it, then write the question to test that named skill —
  rather than writing a plausible-sounding scenario first and only discovering afterward what it
  actually measures.

## Scenario and troubleshooting-style questions

A question that drops the respondent into a situation ("the sensor is reading zero", "the build
failed with this error") is testing diagnostic judgment, not fact recall — and it needs different
distractor design from a standalone-fact Multiple Choice item.

- **Name the skill before drafting the question.** Per Zascerinska et al. (2024) above: decide
  what specific diagnostic or procedural judgment the item tests, in one sentence, before writing
  the scenario. If that sentence is hard to write, the scenario probably isn't ready to become a
  question yet.
- **Distractors should be plausible misdiagnoses, not filler.** A distractor nobody would pick
  under real conditions tests nothing — it just shortens the effective option count. The
  distractor that matters is the one a competent-but-hasty respondent would actually reach for:
  the adjacent wrong cause, the step that looks right but is one stage too early or too late, the
  answer that would have been correct under slightly different circumstances than the ones stated.
  A confidently-wrong diagnosis is the real-world failure mode worth testing for — see the
  certainty-based-marking citation above.

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
