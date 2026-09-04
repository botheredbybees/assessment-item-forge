# Assessment Item Forge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `assessment-item-forge` — a standalone Claude Skill that takes a whole source
document and produces a whole Moodle quiz (one XML file, a deliberate mixture of question types)
via evidence-grounded pedagogical judgment plus deterministic, tested Python code for every
mechanically-checkable correctness property.

**Architecture:** Thirteen question-type dataclasses in `scripts/moodle_xml.py`, each with a
`to_xml()` method built on small shared helpers (base question fields, combined-feedback block);
`scripts/length_distribution.py` enforces the answer-length distribution rule as code, not prose;
`scripts/item_sanity_check.py` validates structural correctness before anything is considered
"drafted." `SKILL.md` and `references/*.md` hold the pedagogical judgment layer that decides which
types to use and why. No live Moodle instance is required to develop or test this repo — every
XML shape below was verified against a real, running Moodle 5.0.2 instance during design (either
a live create-then-export round-trip, or Moodle's own shipped test fixtures / source code where a
round-trip wasn't practical), so tests assert structural correctness via XML parsing, not a live
import.

**Tech Stack:** Python 3.10+, `xml.etree.ElementTree` (parsing, in tests), pytest. No external
dependencies for the runtime code itself — the whole point is portability.

## Global Constraints

- **No AI-authorship commit trailers.** This repo is public on GitHub; keep commits clean.
- **Moodle XML only — no GIFT.** Every dataclass emits Moodle XML directly; nothing in this repo
  produces or parses GIFT.
- **Every question-level text field** (`questiontext`, `generalfeedback`, `feedback`, `name`) is
  wrapped in a CDATA section, never raw XML-escaped — confirmed acceptable across every type this
  session verified, and it sidesteps HTML/quote/ampersand escaping complexity entirely for content
  that will often contain HTML markup.
- **Base question fields present on every type regardless of qtype** (confirmed live against a
  running Moodle 5.0.2 instance, `bitnamilegacy/moodle:5.0.2`, via real `qformat_xml` exports):
  `<name>`, `<questiontext format="html">`, `<generalfeedback format="html">`, `<defaultgrade>`,
  `<penalty>`, `<hidden>0</hidden>`, `<idnumber></idnumber>`. `<defaultgrade>` is `"0.0000000"`
  for Description (ungraded) and `"1.0000000"` for everything else by default.
- **Combined-feedback block present on multichoice, matching, ddwtos, ddimageortext, ddmarker,
  gapselect, ordering, and calculated** (confirmed live or via Moodle's own shipped test fixtures):
  `<correctfeedback format="html">`, `<partiallycorrectfeedback format="html">`,
  `<incorrectfeedback format="html">`, optionally followed by a self-closing `<shownumcorrect/>`.
- **Two real naming traps, confirmed against live Moodle exports — do not use the qtype's internal
  name as the XML `type` attribute for these two:** the `multianswer` qtype's XML type is
  **`cloze`**; the `match` qtype's XML type is **`matching`**.
- **True/False feedback has no positional ambiguity in XML** (unlike GIFT's easily-reversed
  `{ANSWER#wrong#right}` convention — see the sibling Nuyina LMS project's own `gift_format.py`
  docstring for that trap): each `<answer>` element carries an explicit `fraction="100"` or
  `fraction="0"`, so map `correct_feedback`/`incorrect_feedback` fields onto those by value in
  `to_xml()` — get this right once, and there is nothing to misremember afterward.
- **Calculated needs a live-round-trip smoke test before being trusted**, not just the unit tests
  — its schema was derived from reading Moodle's `qformat_xml` source code directly (no shipped
  fixture existed to verify against), unlike every other type in scope, which either round-tripped
  live or matched a real Moodle-shipped fixture. This is called out explicitly in Task 9.

---

### Task 1: Repo scaffolding — LICENSE, ATTRIBUTION, README

**Files:**
- Create: `LICENSE`
- Create: `ATTRIBUTION.md`
- Create: `README.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing later tasks import — this is documentation/legal scaffolding only.

This task has no code and is not TDD-shaped.

- [ ] **Step 1: Fetch the real, complete CC BY-SA 4.0 legal text**

```bash
curl -sL https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt -o LICENSE
wc -l LICENSE
```

Expected: `LICENSE` now contains the complete, verbatim legal code (428 lines as of 2026-09-04;
a version-independent check is easier — confirm it starts with "Attribution-ShareAlike 4.0
International" and ends with "Creative Commons may be contacted at creativecommons.org."). Do not
hand-type or summarize this text — always fetch the real document.

- [ ] **Step 2: Write `ATTRIBUTION.md`**

```markdown
# Attribution

This project is licensed under CC BY-SA 4.0 (see `LICENSE`). It is a fresh build — not a fork —
informed by two existing projects, credited here for the specific ideas adapted from each, per
CC BY-SA 4.0's attribution requirement.

## danielcregg/moodle-mcq (MIT License)

https://github.com/danielcregg/claude-code-skill-moodle-mcq

The answer-length-distribution target this project enforces in `scripts/length_distribution.py`
— aiming for roughly 15% of correct answers being the shortest option, 15% the longest, and 70%
neither, across a whole question set — is adapted from this project's own length-balancing rule.
MIT is compatible as an input to a CC BY-SA 4.0 work; this credit is given because it's the right
thing to do, not because MIT requires it.

## GarethManning/education-agent-skills (CC BY-SA 4.0)

https://github.com/GarethManning/education-agent-skills

The pedagogical reasoning structure in `references/pedagogy.md` — matching an assessment
technique to what is actually being checked, when, and under what constraints — is adapted from
the `curriculum-assessment/formative-assessment-technique-selector` skill in this library. The
construct-validity framing behind the answer-length-distribution rule (construct-irrelevant
variance) draws on the same Messick (1989) validity framework cited by this library's
`curriculum-assessment/assessment-validity-checker` skill. Both skills are themselves grounded in
Black & Wiliam (1998), Wiliam (2011), and Messick (1989) — see `references/pedagogy.md` for full
citations. This project's CC BY-SA 4.0 license is required by this source's share-alike terms.
```

- [ ] **Step 3: Write `README.md`**

```markdown
# Assessment Item Forge

A Claude Skill that takes a whole source document — a lesson, a wiki page, a Confluence page's
content — and produces a whole Moodle quiz: a deliberate mixture of question types chosen by
pedagogical judgment, not just the mechanically-easiest type for each fact.

See `docs/superpowers/specs/2026-09-04-assessment-item-forge-design.md` for the full design.

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
```

- [ ] **Step 4: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
.venv/
```

- [ ] **Step 5: Commit**

```bash
git add LICENSE ATTRIBUTION.md README.md .gitignore
git commit -m "docs: repo scaffolding, CC BY-SA 4.0 license, attribution"
```

---

### Task 2: Core XML infrastructure, Multiple Choice, True/False

**Files:**
- Create: `scripts/__init__.py` (empty)
- Create: `scripts/moodle_xml.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `_cdata(text: str) -> str`, `_text_block(tag: str, text: str, fmt: str = "html") -> str`,
  `_name_block(name: str) -> str`, `_base_question_fields(name: str, questiontext: str,
  defaultgrade: str = "1.0000000", penalty: str = "0.3333333", general_feedback: str = "") -> str`,
  `_combined_feedback(correct: str = "Correct.", partial: str = "Partially correct.", incorrect:
  str = "Incorrect.", show_num_correct: bool = False) -> str` — every later task in this plan uses
  these four helpers, never re-implementing base-field or combined-feedback XML by hand.
  `MultipleChoiceQuestion(name, questiontext, correct, incorrect, single=True,
  shuffle_answers=True, correct_feedback="Correct.", incorrect_feedback="Incorrect.")` with
  `.to_xml() -> str`, `.option_lengths() -> tuple[int, list[int]]` (returns `(correct_length,
  [distractor_lengths])` — this is the interface Task 10's `length_distribution.py` consumes from
  every multiple-choice-family type). `TrueFalseQuestion(name, questiontext, answer: bool,
  correct_feedback="Correct.", incorrect_feedback="Incorrect.")` with `.to_xml() -> str`.
  `write_moodle_xml(questions: list, path: str) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle_xml.py
import xml.etree.ElementTree as ET

from scripts.moodle_xml import (
    MultipleChoiceQuestion,
    TrueFalseQuestion,
    write_moodle_xml,
    _cdata,
    _text_block,
)


def test_cdata_wraps_text():
    assert _cdata("hello") == "<![CDATA[hello]]>"


def test_cdata_escapes_literal_cdata_close_sequence():
    # A literal "]]>" inside the text would prematurely close the CDATA section if
    # not handled -- split it into two adjacent CDATA sections instead.
    result = _cdata("before]]>after")
    assert result == "before]]]]><![CDATA[>after".join(["<![CDATA[", "]]>"])
    # Simpler equivalent check: the raw "]]>" must not appear unescaped mid-content.
    inner = result[len("<![CDATA["):-len("]]>")]
    assert "]]>" not in inner or inner.count("]]>") == 0


def test_text_block_shape():
    block = _text_block("questiontext", "What color is the sky?")
    assert '<questiontext format="html">' in block
    assert "<![CDATA[What color is the sky?]]>" in block
    assert block.strip().endswith("</questiontext>")


def test_multiple_choice_to_xml_has_correct_type_and_structure():
    q = MultipleChoiceQuestion(
        name="Sample MC",
        questiontext="What color is the sky?",
        correct="Blue",
        incorrect=["Green", "Red", "Purple"],
    )
    xml_text = q.to_xml()
    root = ET.fromstring(f"<quiz>{xml_text}</quiz>")
    question = root.find("question")
    assert question.get("type") == "multichoice"
    assert question.find("name/text").text == "Sample MC"
    answers = question.findall("answer")
    assert len(answers) == 4
    correct_answers = [a for a in answers if a.get("fraction") == "100"]
    assert len(correct_answers) == 1
    assert correct_answers[0].find("text").text == "Blue"
    wrong_fractions = {a.get("fraction") for a in answers if a.get("fraction") != "100"}
    assert wrong_fractions == {"0"}
    assert question.find("single").text == "true"
    assert question.find("shuffleanswers").text == "true"
    assert question.find("correctfeedback") is not None
    assert question.find("defaultgrade").text == "1.0000000"
    assert question.find("hidden").text == "0"


def test_multiple_choice_option_lengths_identifies_correct_index():
    q = MultipleChoiceQuestion(
        name="Q", questiontext="?", correct="short", incorrect=["much longer distractor", "medium one"],
    )
    correct_len, distractor_lens = q.option_lengths()
    assert correct_len == len("short")
    assert distractor_lens == [len("much longer distractor"), len("medium one")]


def test_true_false_to_xml_maps_feedback_by_fraction_not_position():
    # The correct answer is TRUE. correct_feedback must land on the fraction="100"
    # answer (text "true"), incorrect_feedback on fraction="0" (text "false") --
    # regardless of any GIFT-style positional convention (see Global Constraints).
    q = TrueFalseQuestion(
        name="Sample TF",
        questiontext="The sky is blue.",
        answer=True,
        correct_feedback="Yes, exactly.",
        incorrect_feedback="No, that's wrong.",
    )
    xml_text = q.to_xml()
    root = ET.fromstring(f"<quiz>{xml_text}</quiz>")
    question = root.find("question")
    assert question.get("type") == "truefalse"
    answers = {a.find("text").text: a for a in question.findall("answer")}
    assert answers["true"].get("fraction") == "100"
    assert answers["true"].find("feedback/text").text == "Yes, exactly."
    assert answers["false"].get("fraction") == "0"
    assert answers["false"].find("feedback/text").text == "No, that's wrong."


def test_true_false_answer_false_flips_which_fraction_is_100():
    q = TrueFalseQuestion(name="Q", questiontext="?", answer=False)
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    answers = {a.find("text").text: a.get("fraction") for a in root.find("question").findall("answer")}
    assert answers["false"] == "100"
    assert answers["true"] == "0"


def test_write_moodle_xml_wraps_questions_in_quiz_root(tmp_path):
    q1 = MultipleChoiceQuestion(name="Q1", questiontext="?", correct="A", incorrect=["B", "C", "D"])
    q2 = TrueFalseQuestion(name="Q2", questiontext="?", answer=True)
    out = tmp_path / "quiz.xml"
    write_moodle_xml([q1, q2], str(out))

    tree = ET.parse(out)
    root = tree.getroot()
    assert root.tag == "quiz"
    questions = root.findall("question")
    assert len(questions) == 2
    assert questions[0].get("type") == "multichoice"
    assert questions[1].get("type") == "truefalse"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_moodle_xml.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.moodle_xml'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/moodle_xml.py
from dataclasses import dataclass, field


def _cdata(text: str) -> str:
    """Wrap text in a CDATA section. A literal "]]>" inside the text would otherwise
    prematurely close the section -- split it into two adjacent CDATA blocks instead,
    the standard escape for this case.
    """
    safe = text.replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[{safe}]]>"


def _text_block(tag: str, text: str, fmt: str = "html", indent: str = "  ") -> str:
    """A <tag format="..."><text>...</text></tag> block -- the shape every question-level
    text field (questiontext, generalfeedback, per-answer feedback) uses across every
    Moodle XML question type, confirmed live against a running Moodle 5.0.2 instance
    (bitnamilegacy/moodle:5.0.2) via real qformat_xml exports during this project's design.
    """
    return (
        f'{indent}<{tag} format="{fmt}">\n'
        f'{indent}  <text>{_cdata(text)}</text>\n'
        f'{indent}</{tag}>'
    )


def _name_block(name: str, indent: str = "  ") -> str:
    """<name><text>...</text></name> -- unlike questiontext/generalfeedback, the <name>
    element's <text> child carries no format attribute, confirmed in every verified export."""
    return f'{indent}<name>\n{indent}  <text>{_cdata(name)}</text>\n{indent}</name>'


def _base_question_fields(name: str, questiontext: str, defaultgrade: str = "1.0000000",
                           penalty: str = "0.3333333", general_feedback: str = "") -> str:
    """Fields present on every question type regardless of qtype -- confirmed live:
    name, questiontext, generalfeedback, defaultgrade, penalty, hidden, idnumber.
    Pass defaultgrade="0.0000000" for ungraded types (Description).
    """
    return (
        f'{_name_block(name)}\n'
        f'{_text_block("questiontext", questiontext)}\n'
        f'{_text_block("generalfeedback", general_feedback)}\n'
        f'  <defaultgrade>{defaultgrade}</defaultgrade>\n'
        f'  <penalty>{penalty}</penalty>\n'
        f'  <hidden>0</hidden>\n'
        f'  <idnumber></idnumber>'
    )


def _combined_feedback(correct: str = "Correct.", partial: str = "Partially correct.",
                        incorrect: str = "Incorrect.", show_num_correct: bool = False) -> str:
    """The correctfeedback/partiallycorrectfeedback/incorrectfeedback block shared by
    multichoice, matching, ddwtos, ddimageortext, ddmarker, gapselect, ordering, and
    calculated -- confirmed live or via Moodle's own shipped test fixtures for each type.
    """
    block = (
        f'{_text_block("correctfeedback", correct)}\n'
        f'{_text_block("partiallycorrectfeedback", partial)}\n'
        f'{_text_block("incorrectfeedback", incorrect)}'
    )
    if show_num_correct:
        block += '\n  <shownumcorrect/>'
    return block


@dataclass
class MultipleChoiceQuestion:
    """A single-answer multiple choice question.

    Confirmed live against a running Moodle 5.0.2 instance via a real qformat_xml
    export: XML type "multichoice", requires <single>, <shuffleanswers>,
    <answernumbering>, the combined-feedback block, and one <answer> per option with
    an explicit fraction (100 for correct, 0 for every distractor -- no partial credit
    in this dataclass; multichoice supports weighted fractions but that's out of scope
    here).
    """

    name: str
    questiontext: str
    correct: str
    incorrect: list[str]
    single: bool = True
    shuffle_answers: bool = True
    correct_feedback_text: str = "Correct."
    incorrect_feedback_text: str = "Incorrect."

    def option_lengths(self) -> tuple[int, list[int]]:
        """(correct answer's display length, [each distractor's display length]) --
        consumed by scripts/length_distribution.py to check the answer-length
        distribution rule across a whole question set."""
        return len(self.correct), [len(opt) for opt in self.incorrect]

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        answers = [f'  <answer fraction="100" format="html">\n'
                   f'{_text_block("text", self.correct, indent="    ")}\n'
                   f'{_text_block("feedback", self.correct_feedback_text, indent="    ")}\n'
                   f'  </answer>']
        for opt in self.incorrect:
            answers.append(f'  <answer fraction="0" format="html">\n'
                            f'{_text_block("text", opt, indent="    ")}\n'
                            f'{_text_block("feedback", self.incorrect_feedback_text, indent="    ")}\n'
                            f'  </answer>')
        answers_xml = "\n".join(answers)
        return (
            f'<question type="multichoice">\n'
            f'{base}\n'
            f'  <single>{"true" if self.single else "false"}</single>\n'
            f'  <shuffleanswers>{"true" if self.shuffle_answers else "false"}</shuffleanswers>\n'
            f'  <answernumbering>abc</answernumbering>\n'
            f'{_combined_feedback()}\n'
            f'{answers_xml}\n'
            f'</question>'
        )


@dataclass
class TrueFalseQuestion:
    """A true/false question.

    Confirmed live: XML type "truefalse", two <answer> elements with text "true"/
    "false", fraction 100 on whichever matches `answer`. Feedback is mapped by
    fraction value here, not by any positional convention -- see this plan's Global
    Constraints for why that matters (GIFT's own {ANSWER#wrong#right} convention is
    a real, easily-reversed trap that doesn't apply to XML generated this way).
    """

    name: str
    questiontext: str
    answer: bool
    correct_feedback: str = "Correct."
    incorrect_feedback: str = "Incorrect."

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        true_fraction = "100" if self.answer else "0"
        false_fraction = "0" if self.answer else "100"
        true_feedback = self.correct_feedback if self.answer else self.incorrect_feedback
        false_feedback = self.incorrect_feedback if self.answer else self.correct_feedback
        return (
            f'<question type="truefalse">\n'
            f'{base}\n'
            f'  <answer fraction="{true_fraction}" format="html">\n'
            f'{_text_block("text", "true", indent="    ")}\n'
            f'{_text_block("feedback", true_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'  <answer fraction="{false_fraction}" format="html">\n'
            f'{_text_block("text", "false", indent="    ")}\n'
            f'{_text_block("feedback", false_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'</question>'
        )


def write_moodle_xml(questions: list, path: str) -> None:
    """Writes a list of question dataclasses (each exposing .to_xml()) as one Moodle
    XML quiz file -- the whole document-to-quiz output of assessment-item-forge."""
    bodies = "\n\n".join(q.to_xml() for q in questions)
    xml_text = f'<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n{bodies}\n</quiz>\n'
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_text)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_moodle_xml.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/moodle_xml.py tests/__init__.py tests/test_moodle_xml.py
git commit -m "feat: core XML infrastructure, Multiple Choice, True/False"
```

---

### Task 3: Numerical, Description, Short Answer, Essay

**Files:**
- Modify: `scripts/moodle_xml.py`
- Modify: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: `_base_question_fields`, `_text_block` (Task 2).
- Produces: `NumericalQuestion(name, questiontext, answer: float, tolerance: float = 0.01,
  correct_feedback="Correct.")` with `.to_xml() -> str`. `DescriptionQuestion(name, text)` with
  `.to_xml() -> str`. `ShortAnswerQuestion(name, questiontext, answer: str, use_case: bool = False,
  correct_feedback="Correct.")` with `.to_xml() -> str`. `EssayQuestion(name, questiontext,
  response_field_lines: int = 15)` with `.to_xml() -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle_xml.py -- add these

from scripts.moodle_xml import NumericalQuestion, DescriptionQuestion, ShortAnswerQuestion, EssayQuestion


def test_numerical_to_xml_has_tolerance_and_unit_fields():
    q = NumericalQuestion(name="Sample Numerical", questiontext="What is 2 + 2?", answer=4.0)
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "numerical"
    answer = question.find("answer")
    assert answer.get("fraction") == "100"
    assert answer.find("text").text == "4.0"
    assert answer.find("tolerance").text == "0.01"
    assert question.find("unitgradingtype").text == "0"
    assert question.find("unitsleft").text == "0"


def test_description_to_xml_has_no_answers_and_zero_grade():
    q = DescriptionQuestion(name="Sample Description", text="This is informational only.")
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "description"
    assert question.findall("answer") == []
    assert question.find("defaultgrade").text == "0.0000000"


def test_short_answer_to_xml_has_usecase_and_answer():
    q = ShortAnswerQuestion(name="SA Sample", questiontext="What is the capital of France?", answer="Paris")
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "shortanswer"
    assert question.find("usecase").text == "0"
    answer = question.find("answer")
    assert answer.get("fraction") == "100"
    assert answer.find("text").text == "Paris"


def test_short_answer_use_case_true_sets_usecase_1():
    q = ShortAnswerQuestion(name="Q", questiontext="?", answer="X", use_case=True)
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    assert root.find("question/usecase").text == "1"


def test_essay_to_xml_has_required_response_fields():
    q = EssayQuestion(name="Essay Sample", questiontext="Describe the water cycle.")
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "essay"
    assert question.find("responseformat").text == "editor"
    assert question.find("responserequired").text == "1"
    assert question.find("responsefieldlines").text == "15"
    assert question.find("attachments").text == "0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k "numerical or description or short_answer or essay"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add the implementations to `scripts/moodle_xml.py`**

```python
@dataclass
class NumericalQuestion:
    """Confirmed live: XML type "numerical". A single <answer> with <tolerance>, plus
    top-level unitgradingtype/unitpenalty/showunits/unitsleft fields that must be
    present even when no units are configured (showunits=3 means "no units used")."""

    name: str
    questiontext: str
    answer: float
    tolerance: float = 0.01
    correct_feedback: str = "Correct."

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        return (
            f'<question type="numerical">\n'
            f'{base}\n'
            f'  <answer fraction="100" format="html">\n'
            f'{_text_block("text", str(self.answer), indent="    ")}\n'
            f'{_text_block("feedback", self.correct_feedback, indent="    ")}\n'
            f'    <tolerance>{self.tolerance}</tolerance>\n'
            f'  </answer>\n'
            f'  <unitgradingtype>0</unitgradingtype>\n'
            f'  <unitpenalty>1.0000000</unitpenalty>\n'
            f'  <showunits>3</showunits>\n'
            f'  <unitsleft>0</unitsleft>\n'
            f'</question>'
        )


@dataclass
class DescriptionQuestion:
    """Confirmed live: XML type "description". No <answer> elements at all;
    defaultgrade="0.0000000" is the tell that it's ungraded, informational content."""

    name: str
    text: str

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.text, defaultgrade="0.0000000")
        return f'<question type="description">\n{base}\n</question>'


@dataclass
class ShortAnswerQuestion:
    """Confirmed live: XML type "shortanswer". Requires <usecase> (case-sensitivity
    flag) even for a single accepted answer.

    Per this repo's own content-authoring guidance (see references/pedagogy.md):
    Short Answer's exact/wildcard string matching produces false negatives for benign
    spelling or formatting variation -- the skill steers authors toward other types by
    default. This dataclass exists to support it when a user judges the tradeoff
    acceptable, not to encourage it.
    """

    name: str
    questiontext: str
    answer: str
    use_case: bool = False
    correct_feedback: str = "Correct."

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        return (
            f'<question type="shortanswer">\n'
            f'{base}\n'
            f'  <usecase>{"1" if self.use_case else "0"}</usecase>\n'
            f'  <answer fraction="100" format="html">\n'
            f'{_text_block("text", self.answer, indent="    ")}\n'
            f'{_text_block("feedback", self.correct_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'</question>'
        )


@dataclass
class EssayQuestion:
    """Confirmed live: XML type "essay". Requires responseformat/responserequired/
    responsefieldlines plus several empty-but-present fields (minwordlimit,
    maxwordlimit, attachments, attachmentsrequired, maxbytes, filetypeslist,
    graderinfo, responsetemplate) -- Moodle emits all of these even when unset.

    Per this repo's own content-authoring guidance (see references/pedagogy.md):
    Essay requires a human to manually grade every attempt, which doesn't fit a
    retakeable/self-directed formative model. Supported for when a user judges the
    grading-burden tradeoff acceptable, not encouraged by default.
    """

    name: str
    questiontext: str
    response_field_lines: int = 15

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        return (
            f'<question type="essay">\n'
            f'{base}\n'
            f'  <responseformat>editor</responseformat>\n'
            f'  <responserequired>1</responserequired>\n'
            f'  <responsefieldlines>{self.response_field_lines}</responsefieldlines>\n'
            f'  <minwordlimit></minwordlimit>\n'
            f'  <maxwordlimit></maxwordlimit>\n'
            f'  <attachments>0</attachments>\n'
            f'  <attachmentsrequired>0</attachmentsrequired>\n'
            f'  <maxbytes>0</maxbytes>\n'
            f'  <filetypeslist></filetypeslist>\n'
            f'{_text_block("graderinfo", "")}\n'
            f'{_text_block("responsetemplate", "")}\n'
            f'</question>'
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_moodle_xml.py -v`
Expected: PASS (14 tests total)

- [ ] **Step 5: Commit**

```bash
git add scripts/moodle_xml.py tests/test_moodle_xml.py
git commit -m "feat: Numerical, Description, Short Answer, Essay question types"
```

---

### Task 4: Matching

**Files:**
- Modify: `scripts/moodle_xml.py`
- Modify: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: `_base_question_fields`, `_text_block`, `_combined_feedback` (Task 2).
- Produces: `MatchingQuestion(name, questiontext, pairs: list[tuple[str, str]],
  shuffle_answers: bool = True)` with `.to_xml() -> str` — `pairs` is `[(subquestion_text,
  answer_text), ...]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_moodle_xml.py -- add this

from scripts.moodle_xml import MatchingQuestion


def test_matching_to_xml_uses_matching_type_not_match():
    # Real naming trap confirmed live: the qtype's internal name is "match", but the
    # XML type attribute is "matching" -- see this plan's Global Constraints.
    q = MatchingQuestion(
        name="Match Sample",
        questiontext="Match the country to its capital.",
        pairs=[("France", "Paris"), ("Germany", "Berlin"), ("Italy", "Rome")],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "matching"
    subquestions = question.findall("subquestion")
    assert len(subquestions) == 3
    assert subquestions[0].find("text").text == "France"
    assert subquestions[0].find("answer/text").text == "Paris"
    assert question.find("shuffleanswers").text == "true"
    assert question.find("correctfeedback") is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k matching`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add the implementation**

```python
@dataclass
class MatchingQuestion:
    """Confirmed live: XML type "matching" (NOT "match" -- see Global Constraints).
    A flat list of <subquestion>/<answer> text pairs -- correctness is pairing by
    document order, not by any explicit ID/key field."""

    name: str
    questiontext: str
    pairs: list[tuple[str, str]]
    shuffle_answers: bool = True

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        subquestions = []
        for prompt, answer in self.pairs:
            subquestions.append(
                f'  <subquestion format="html">\n'
                f'{_text_block("text", prompt, indent="    ")}\n'
                f'    <answer>\n'
                f'{_text_block("text", answer, indent="      ")}\n'
                f'    </answer>\n'
                f'  </subquestion>'
            )
        subquestions_xml = "\n".join(subquestions)
        return (
            f'<question type="matching">\n'
            f'{base}\n'
            f'  <shuffleanswers>{"true" if self.shuffle_answers else "false"}</shuffleanswers>\n'
            f'{_combined_feedback()}\n'
            f'{subquestions_xml}\n'
            f'</question>'
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k matching`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/moodle_xml.py tests/test_moodle_xml.py
git commit -m "feat: Matching question type"
```

---

### Task 5: Cloze / Embedded Answers

**Files:**
- Modify: `scripts/moodle_xml.py`
- Modify: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: `_base_question_fields`, `_text_block` (Task 2).
- Produces: `ClozeBlank` (a small helper class representing one embedded sub-answer):
  `ClozeBlank(kind: str, correct: str, wrong: list[str] = [], weight: int = 1)` where `kind` is
  one of `"SHORTANSWER"`, `"NUMERICAL"`, `"MULTICHOICE"`, with `.to_embedded_text() -> str`
  producing the `{weight:KIND:=correct~wrong1~wrong2}` mini-language fragment.
  `ClozeQuestion(name, template: str, blanks: list[ClozeBlank])` with `.to_xml() -> str` — `template`
  is the surrounding passage text with `{}` placeholders marking where each blank goes, filled in
  order from `blanks`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle_xml.py -- add these

from scripts.moodle_xml import ClozeBlank, ClozeQuestion


def test_cloze_blank_shortanswer_embedded_text():
    blank = ClozeBlank(kind="SHORTANSWER", correct="Paris")
    assert blank.to_embedded_text() == "{1:SHORTANSWER:=Paris}"


def test_cloze_blank_numerical_embedded_text_includes_tolerance_as_wrong_entry():
    # Moodle's Cloze NUMERICAL sub-answer syntax is {weight:NUMERICAL:=answer:tolerance}
    blank = ClozeBlank(kind="NUMERICAL", correct="2100000:100000")
    assert blank.to_embedded_text() == "{1:NUMERICAL:=2100000:100000}"


def test_cloze_blank_multichoice_embedded_text_includes_distractors():
    blank = ClozeBlank(kind="MULTICHOICE", correct="Eiffel Tower", wrong=["Big Ben", "Colosseum"])
    assert blank.to_embedded_text() == "{1:MULTICHOICE:=Eiffel Tower~Big Ben~Colosseum}"


def test_cloze_question_to_xml_uses_cloze_type_not_multianswer():
    # Real naming trap confirmed live: the qtype's internal name is "multianswer", but
    # the XML type attribute is "cloze" -- see this plan's Global Constraints.
    q = ClozeQuestion(
        name="Capital of France",
        template="The capital of France is {}. It has a population of about {} people, and its most famous landmark is the {}.",
        blanks=[
            ClozeBlank(kind="SHORTANSWER", correct="Paris"),
            ClozeBlank(kind="NUMERICAL", correct="2100000:100000"),
            ClozeBlank(kind="MULTICHOICE", correct="Eiffel Tower", wrong=["Big Ben", "Colosseum"]),
        ],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "cloze"
    questiontext = question.find("questiontext/text").text
    assert "{1:SHORTANSWER:=Paris}" in questiontext
    assert "{1:NUMERICAL:=2100000:100000}" in questiontext
    assert "{1:MULTICHOICE:=Eiffel Tower~Big Ben~Colosseum}" in questiontext
    # Cloze's complexity lives entirely in the embedded text -- no <answer> elements
    # at the parent-question level, confirmed live.
    assert question.findall("answer") == []


def test_cloze_question_requires_matching_blank_and_placeholder_count():
    with pytest.raises(ValueError, match="placeholder"):
        ClozeQuestion(
            name="Q",
            template="Only one blank here: {}.",
            blanks=[ClozeBlank(kind="SHORTANSWER", correct="A"), ClozeBlank(kind="SHORTANSWER", correct="B")],
        )
```

Add `import pytest` at the top of `tests/test_moodle_xml.py` if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k cloze`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add the implementation**

```python
@dataclass
class ClozeBlank:
    """One embedded sub-answer inside a Cloze (multianswer) question's questiontext.

    Confirmed live: a Cloze question's entire complexity lives in this embedded
    mini-language string sitting inside <questiontext><text> -- there is no separate
    child-question or per-answer XML structure at the parent-question level at all.
    """

    kind: str  # "SHORTANSWER", "NUMERICAL", or "MULTICHOICE"
    correct: str
    wrong: list[str] = field(default_factory=list)
    weight: int = 1

    def to_embedded_text(self) -> str:
        parts = [self.correct] + list(self.wrong)
        joined = "~".join(parts) if self.kind == "MULTICHOICE" else self.correct
        return f"{{{self.weight}:{self.kind}:={joined}}}"


@dataclass
class ClozeQuestion:
    """Confirmed live: XML type "cloze" (NOT "multianswer" -- see Global Constraints).
    `template` uses `{}` as a placeholder marker (Python str.format-style, but filled
    manually here rather than via .format() to avoid clashing with any literal `{`/`}`
    the surrounding prose might contain) -- filled in order from `blanks`.
    """

    name: str
    template: str
    blanks: list

    def __post_init__(self):
        placeholder_count = self.template.count("{}")
        if placeholder_count != len(self.blanks):
            raise ValueError(
                f"template has {placeholder_count} placeholder(s) but {len(self.blanks)} "
                f"blank(s) were given -- these must match"
            )

    def _rendered_text(self) -> str:
        text = self.template
        for blank in self.blanks:
            text = text.replace("{}", blank.to_embedded_text(), 1)
        return text

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self._rendered_text())
        return f'<question type="cloze">\n{base}\n</question>'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k cloze`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/moodle_xml.py tests/test_moodle_xml.py
git commit -m "feat: Cloze/Embedded Answers question type"
```

---

### Task 6: Drag-and-drop family (into text, onto image, markers)

**Files:**
- Modify: `scripts/moodle_xml.py`
- Modify: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: `_base_question_fields`, `_text_block`, `_combined_feedback` (Task 2).
- Produces: `DragIntoTextQuestion(name, questiontext_with_blanks: str, drag_items: list[tuple[str,
  int]])` with `.to_xml() -> str` — `questiontext_with_blanks` contains literal `[[1]]`, `[[2]]`
  etc. markers; `drag_items` is `[(text, group), ...]`, one per draggable word, matched to blanks
  by group. `DragOntoImageQuestion(name, questiontext, image_bytes: bytes, image_filename: str,
  drags: list[tuple[str, int]], drops: list[tuple[int, int, int]])` with `.to_xml() -> str` —
  `drags` is `[(text, draggroup), ...]` (1-indexed by position for `<no>`), `drops` is
  `[(drag_no, xleft, ytop), ...]`. `DragMarkersQuestion(name, questiontext, image_bytes: bytes,
  image_filename: str, drags: list[str], drops: list[tuple[int, str, str]])` with `.to_xml() ->
  str` — `drops` is `[(drag_no, shape, coords), ...]` where `shape` is `"circle"`, `"poly"`, or
  `"rectangle"` and `coords` matches that shape's format (e.g. `"150,200;40"` for a circle).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle_xml.py -- add these

import base64

from scripts.moodle_xml import DragIntoTextQuestion, DragOntoImageQuestion, DragMarkersQuestion


def test_drag_into_text_to_xml_has_dragboxes_and_blanks():
    q = DragIntoTextQuestion(
        name="Sample drag-into-text",
        questiontext_with_blanks="The stage that writes raw files is [[1]], and the stage that parses them is [[2]].",
        drag_items=[("OpenRVDAS", 1), ("fluentd", 1)],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "ddwtos"
    assert "[[1]]" in question.find("questiontext/text").text
    dragboxes = question.findall("dragbox")
    assert len(dragboxes) == 2
    assert dragboxes[0].find("text").text == "OpenRVDAS"
    assert dragboxes[0].find("group").text == "1"
    assert question.find("shuffleanswers") is not None
    assert question.find("correctfeedback") is not None


def test_drag_onto_image_to_xml_embeds_base64_image_and_drop_coords():
    q = DragOntoImageQuestion(
        name="Sample drag-onto-image",
        questiontext="Label the pipeline diagram.",
        image_bytes=b"fake-png-bytes",
        image_filename="diagram.png",
        drags=[("OpenRVDAS", 1), ("fluentd", 1)],
        drops=[(1, 120, 80), (2, 300, 80)],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "ddimageortext"
    file_el = question.find("file")
    assert file_el.get("name") == "diagram.png"
    assert file_el.get("encoding") == "base64"
    assert base64.b64decode(file_el.text) == b"fake-png-bytes"
    drags = question.findall("drag")
    assert len(drags) == 2
    assert drags[0].find("no").text == "1"
    assert drags[0].find("text").text == "OpenRVDAS"
    drops = question.findall("drop")
    assert len(drops) == 2
    assert drops[0].find("choice").text == "1"
    assert drops[0].find("xleft").text == "120"
    assert drops[0].find("ytop").text == "80"


def test_drag_markers_to_xml_has_shape_and_coords():
    q = DragMarkersQuestion(
        name="Sample drag-marker",
        questiontext="Mark each instrument's location.",
        image_bytes=b"fake-png-bytes",
        image_filename="ship-diagram.png",
        drags=["CTD"],
        drops=[(1, "circle", "150,200;40")],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "ddmarker"
    drags = question.findall("drag")
    assert drags[0].find("text").text == "CTD"
    drops = question.findall("drop")
    assert drops[0].find("shape").text == "circle"
    assert drops[0].find("coords").text == "150,200;40"
    assert drops[0].find("choice").text == "1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k "drag"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add the implementations**

```python
import base64


@dataclass
class DragIntoTextQuestion:
    """Confirmed live (Moodle source: question/type/ddwtos/questiontype.php's
    export_to_xml): XML type "ddwtos". Blanks in questiontext are literal [[1]],
    [[2]] markers; draggable words are <dragbox> elements with <text>/<group>
    (a blank only accepts drag items from a matching group)."""

    name: str
    questiontext_with_blanks: str
    drag_items: list  # [(text, group), ...]
    shuffle_answers: bool = True

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext_with_blanks)
        dragboxes = []
        for text, group in self.drag_items:
            dragboxes.append(
                f'  <dragbox>\n'
                f'{_text_block("text", text, indent="    ")}\n'
                f'    <group>{group}</group>\n'
                f'  </dragbox>'
            )
        dragboxes_xml = "\n".join(dragboxes)
        return (
            f'<question type="ddwtos">\n'
            f'{base}\n'
            f'  <shuffleanswers>{1 if self.shuffle_answers else 0}</shuffleanswers>\n'
            f'{_combined_feedback(show_num_correct=True)}\n'
            f'{dragboxes_xml}\n'
            f'</question>'
        )


@dataclass
class DragOntoImageQuestion:
    """Confirmed live (Moodle source: question/type/ddimageortext/questiontype.php's
    export_to_xml): XML type "ddimageortext". The background image is embedded as a
    base64 <file> element. <drag> items are top-level (1-indexed via <no>); <drop>
    zones reference the correct drag via <choice> (matching a drag's <no>) and give
    pixel coordinates via <xleft>/<ytop>."""

    name: str
    questiontext: str
    image_bytes: bytes
    image_filename: str
    drags: list  # [(text, draggroup), ...], 1-indexed by position
    drops: list  # [(drag_no, xleft, ytop), ...]
    shuffle_answers: bool = True

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        image_b64 = base64.b64encode(self.image_bytes).decode("ascii")
        drags_xml = []
        for i, (text, draggroup) in enumerate(self.drags, start=1):
            drags_xml.append(
                f'  <drag>\n'
                f'    <no>{i}</no>\n'
                f'{_text_block("text", text, indent="    ")}\n'
                f'    <draggroup>{draggroup}</draggroup>\n'
                f'  </drag>'
            )
        drops_xml = []
        for drag_no, xleft, ytop in self.drops:
            drops_xml.append(
                f'  <drop>\n'
                f'{_text_block("text", "", indent="    ")}\n'
                f'    <no>{drag_no}</no>\n'
                f'    <choice>{drag_no}</choice>\n'
                f'    <xleft>{xleft}</xleft>\n'
                f'    <ytop>{ytop}</ytop>\n'
                f'  </drop>'
            )
        return (
            f'<question type="ddimageortext">\n'
            f'{base}\n'
            f'  <shuffleanswers>{1 if self.shuffle_answers else 0}</shuffleanswers>\n'
            f'{_combined_feedback()}\n'
            f'  <file name="{self.image_filename}" path="/" encoding="base64">{image_b64}</file>\n'
            f'{chr(10).join(drags_xml)}\n'
            f'{chr(10).join(drops_xml)}\n'
            f'</question>'
        )


@dataclass
class DragMarkersQuestion:
    """Confirmed live (Moodle source: question/type/ddmarker/questiontype.php's
    export_to_xml): XML type "ddmarker". Drop zones are shapes, not points: <shape>
    is "circle" (coords "x,y;radius"), "poly" (coords "x1,y1;x2,y2;..."), or
    "rectangle" (coords "x,y;width,height")."""

    name: str
    questiontext: str
    image_bytes: bytes
    image_filename: str
    drags: list  # [text, ...], 1-indexed by position
    drops: list  # [(drag_no, shape, coords), ...]
    shuffle_answers: bool = True

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        image_b64 = base64.b64encode(self.image_bytes).decode("ascii")
        drags_xml = []
        for i, text in enumerate(self.drags, start=1):
            drags_xml.append(
                f'  <drag>\n'
                f'    <no>{i}</no>\n'
                f'{_text_block("text", text, indent="    ")}\n'
                f'    <noofdrags>1</noofdrags>\n'
                f'  </drag>'
            )
        drops_xml = []
        for drag_no, shape, coords in self.drops:
            drops_xml.append(
                f'  <drop>\n'
                f'    <no>{drag_no}</no>\n'
                f'    <shape>{shape}</shape>\n'
                f'    <coords>{coords}</coords>\n'
                f'    <choice>{drag_no}</choice>\n'
                f'  </drop>'
            )
        return (
            f'<question type="ddmarker">\n'
            f'{base}\n'
            f'  <shuffleanswers>{1 if self.shuffle_answers else 0}</shuffleanswers>\n'
            f'  <showmisplaced/>\n'
            f'{_combined_feedback()}\n'
            f'  <file name="{self.image_filename}" path="/" encoding="base64">{image_b64}</file>\n'
            f'{chr(10).join(drags_xml)}\n'
            f'{chr(10).join(drops_xml)}\n'
            f'</question>'
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k "drag"`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/moodle_xml.py tests/test_moodle_xml.py
git commit -m "feat: drag-and-drop family (into text, onto image, markers)"
```

---

### Task 7: Select Missing Words, Ordering

**Files:**
- Modify: `scripts/moodle_xml.py`
- Modify: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: `_base_question_fields`, `_text_block`, `_combined_feedback` (Task 2).
- Produces: `SelectMissingWordsQuestion(name, questiontext_with_blanks: str, options: list[tuple[str,
  int]])` with `.to_xml() -> str` — `options` is `[(text, group), ...]` (a `<selectoption>` list,
  NOT generic `<answer>` elements — see Global Constraints). `OrderingQuestion(name, questiontext,
  items_in_order: list[str], layout: str = "VERTICAL")` with `.to_xml() -> str` — items must be
  supplied already in their correct order; the dataclass raises if fewer than 3 are given (an
  ordering task with 1-2 items isn't a meaningful sequencing test).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle_xml.py -- add these

from scripts.moodle_xml import SelectMissingWordsQuestion, OrderingQuestion


def test_select_missing_words_uses_selectoption_not_answer():
    # Real structural fact confirmed against Moodle's own shipped test fixture
    # (question/type/gapselect/tests/fixtures/testquestion.moodle.xml): choices use
    # <selectoption> with <text>/<group> children, NOT the generic <answer> block.
    q = SelectMissingWordsQuestion(
        name="Sample gapselect",
        questiontext_with_blanks="The [[1]] [[2]] on the [[3]].",
        options=[("cat", 1), ("sat", 1), ("mat", 1), ("dog", 1), ("table", 1)],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "gapselect"
    assert question.findall("answer") == []
    options = question.findall("selectoption")
    assert len(options) == 5
    assert options[0].find("text").text == "cat"
    assert options[0].find("group").text == "1"


def test_ordering_to_xml_uses_answer_fraction_as_sequence_position():
    # Confirmed against Moodle's own shipped test fixture
    # (question/type/ordering/tests/fixtures/testquestion.moodle.xml): items are
    # <answer> blocks in correct order; fraction holds the sequence POSITION here,
    # not a percentage-correct weight like every other type that uses <answer>.
    q = OrderingQuestion(
        name="Sample ordering",
        questiontext="Put these pipeline stages in order.",
        items_in_order=["OpenRVDAS", "fluentd", "InfluxDB", "Grafana"],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "ordering"
    answers = question.findall("answer")
    assert [a.find("text").text for a in answers] == ["OpenRVDAS", "fluentd", "InfluxDB", "Grafana"]
    assert answers[0].get("fraction") == "1.0000000"
    assert answers[3].get("fraction") == "4.0000000"
    assert question.find("layouttype").text == "VERTICAL"
    assert question.find("gradingtype").text == "ABSOLUTE_POSITION"


def test_ordering_requires_at_least_three_items():
    with pytest.raises(ValueError, match="at least 3"):
        OrderingQuestion(name="Q", questiontext="?", items_in_order=["A", "B"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k "select_missing_words or ordering"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add the implementations**

```python
@dataclass
class SelectMissingWordsQuestion:
    """Confirmed against Moodle's own shipped test fixture
    (question/type/gapselect/tests/fixtures/testquestion.moodle.xml): XML type
    "gapselect". Blanks are literal [[1]], [[2]] markers in questiontext (same
    convention as ddwtos); choices are <selectoption> elements with <text>/<group>
    -- NOT the generic <answer> block other types use."""

    name: str
    questiontext_with_blanks: str
    options: list  # [(text, group), ...]
    shuffle_answers: bool = False

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext_with_blanks)
        options_xml = "\n".join(
            f'  <selectoption>\n{_text_block("text", text, indent="    ")}\n    <group>{group}</group>\n  </selectoption>'
            for text, group in self.options
        )
        return (
            f'<question type="gapselect">\n'
            f'{base}\n'
            f'  <shuffleanswers>{1 if self.shuffle_answers else 0}</shuffleanswers>\n'
            f'{_combined_feedback(show_num_correct=True)}\n'
            f'{options_xml}\n'
            f'</question>'
        )


@dataclass
class OrderingQuestion:
    """Confirmed against Moodle's own shipped test fixture
    (question/type/ordering/tests/fixtures/testquestion.moodle.xml): XML type
    "ordering". `items_in_order` must already be in the correct sequence -- each
    becomes an <answer> block whose `fraction` holds its 1-indexed sequence
    POSITION (not a percentage-correct weight, unlike every other type that uses
    <answer>). Requires at least 3 items: fewer isn't a meaningful sequencing task.
    """

    name: str
    questiontext: str
    items_in_order: list
    layout: str = "VERTICAL"

    def __post_init__(self):
        if len(self.items_in_order) < 3:
            raise ValueError("Ordering needs at least 3 items to be a meaningful sequencing task")

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext)
        answers_xml = "\n".join(
            f'  <answer fraction="{i}.0000000" format="html">\n{_text_block("text", item, indent="    ")}\n  </answer>'
            for i, item in enumerate(self.items_in_order, start=1)
        )
        return (
            f'<question type="ordering">\n'
            f'{base}\n'
            f'  <layouttype>{self.layout}</layouttype>\n'
            f'  <selecttype>ALL</selecttype>\n'
            f'  <selectcount>{len(self.items_in_order)}</selectcount>\n'
            f'  <gradingtype>ABSOLUTE_POSITION</gradingtype>\n'
            f'  <showgrading>SHOW</showgrading>\n'
            f'{_combined_feedback(show_num_correct=True)}\n'
            f'{answers_xml}\n'
            f'</question>'
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k "select_missing_words or ordering"`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/moodle_xml.py tests/test_moodle_xml.py
git commit -m "feat: Select Missing Words and Ordering question types"
```

---

### Task 8: Calculated

**Files:**
- Modify: `scripts/moodle_xml.py`
- Modify: `tests/test_moodle_xml.py`

**Interfaces:**
- Consumes: `_base_question_fields`, `_text_block`, `_combined_feedback` (Task 2).
- Produces: `CalculatedWildcard(name: str, minimum: float, maximum: float, decimals: int = 0)` and
  `CalculatedQuestion(name, questiontext_with_wildcards: str, formula: str, wildcards:
  list[CalculatedWildcard], tolerance: float = 0.01)` with `.to_xml() -> str`.

This type's schema was derived from reading Moodle's `qformat_xml` source directly (no shipped
fixture existed to verify against) — Task 9 adds a live-round-trip smoke test specifically for
this type before it's trusted for real use.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_moodle_xml.py -- add these

from scripts.moodle_xml import CalculatedWildcard, CalculatedQuestion


def test_calculated_to_xml_has_dataset_definitions_per_wildcard():
    q = CalculatedQuestion(
        name="Sum of two numbers",
        questiontext_with_wildcards="What is {x} + {y}?",
        formula="{x}+{y}",
        wildcards=[
            CalculatedWildcard(name="x", minimum=1, maximum=10),
            CalculatedWildcard(name="y", minimum=1, maximum=10),
        ],
    )
    root = ET.fromstring(f"<quiz>{q.to_xml()}</quiz>")
    question = root.find("question")
    assert question.get("type") == "calculated"
    assert "{x}" in question.find("questiontext/text").text
    answer = question.find("answer")
    assert answer.get("fraction") == "100"
    assert answer.find("text").text == "{x}+{y}"
    assert answer.find("tolerance").text == "0.01"
    definitions = question.findall("dataset_definitions/dataset_definition")
    assert len(definitions) == 2
    assert definitions[0].find("name/text").text == "x"
    assert definitions[0].find("minimum/text").text == "1"
    assert definitions[0].find("maximum/text").text == "10"
    assert definitions[0].find("distribution/text").text == "uniform"
    assert question.find("unitgradingtype").text == "0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k calculated`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add the implementation**

```python
@dataclass
class CalculatedWildcard:
    """One dataset_definition -- a wildcard variable in a Calculated question's
    formula, e.g. {x} in "What is {x} + {y}?". Derived from reading
    question/format/xml/format.php's writequestion() 'calculated' case directly
    (no shipped Moodle fixture existed to verify this type against live -- see this
    plan's Global Constraints and Task 9's live-round-trip smoke test)."""

    name: str
    minimum: float
    maximum: float
    decimals: int = 0

    def to_xml(self) -> str:
        return (
            f'    <dataset_definition>\n'
            f'{_text_block("status", "private", indent="      ")}\n'
            f'{_text_block("name", self.name, indent="      ")}\n'
            f'      <type>calculated</type>\n'
            f'{_text_block("distribution", "uniform", indent="      ")}\n'
            f'{_text_block("minimum", str(self.minimum), indent="      ")}\n'
            f'{_text_block("maximum", str(self.maximum), indent="      ")}\n'
            f'{_text_block("decimals", str(self.decimals), indent="      ")}\n'
            f'      <itemcount>1</itemcount>\n'
            f'      <dataset_items>\n'
            f'        <dataset_item>\n'
            f'          <number>1</number>\n'
            f'          <value>{self.minimum}</value>\n'
            f'        </dataset_item>\n'
            f'      </dataset_items>\n'
            f'      <number_of_items>1</number_of_items>\n'
            f'    </dataset_definition>'
        )


@dataclass
class CalculatedQuestion:
    """Confirmed via direct reading of Moodle's qformat_xml source (no shipped
    fixture existed -- see Task 9's live-round-trip smoke test): XML type
    "calculated". Wildcards like {x} appear in both questiontext and the answer's
    formula text, resolved from <dataset_definitions> at attempt time."""

    name: str
    questiontext_with_wildcards: str
    formula: str
    wildcards: list
    tolerance: float = 0.01
    correct_feedback: str = "Correct."

    def to_xml(self) -> str:
        base = _base_question_fields(self.name, self.questiontext_with_wildcards)
        definitions_xml = "\n".join(w.to_xml() for w in self.wildcards)
        return (
            f'<question type="calculated">\n'
            f'{base}\n'
            f'  <synchronize>0</synchronize>\n'
            f'  <single>true</single>\n'
            f'  <answernumbering>abc</answernumbering>\n'
            f'  <shuffleanswers>0</shuffleanswers>\n'
            f'{_combined_feedback()}\n'
            f'  <answer fraction="100" format="html">\n'
            f'{_text_block("text", self.formula, indent="    ")}\n'
            f'    <tolerance>{self.tolerance}</tolerance>\n'
            f'    <tolerancetype>1</tolerancetype>\n'
            f'    <correctanswerformat>1</correctanswerformat>\n'
            f'    <correctanswerlength>2</correctanswerlength>\n'
            f'{_text_block("feedback", self.correct_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'  <unitgradingtype>0</unitgradingtype>\n'
            f'  <unitpenalty>0.1</unitpenalty>\n'
            f'  <showunits>3</showunits>\n'
            f'  <unitsleft>0</unitsleft>\n'
            f'  <dataset_definitions>\n'
            f'{definitions_xml}\n'
            f'  </dataset_definitions>\n'
            f'</question>'
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_moodle_xml.py -v -k calculated`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/moodle_xml.py tests/test_moodle_xml.py
git commit -m "feat: Calculated question type"
```

---

### Task 9: Live-round-trip smoke test for all 13 types

**Files:**
- Create: `scripts/smoke_test_live_moodle.py`

**Interfaces:**
- Consumes: every dataclass from Tasks 2-8, `write_moodle_xml`.
- Produces: a manual verification script, not imported by anything else.

Unlike every other task in this plan, this one requires a live Moodle instance — it is not part
of the `pytest` suite and is not run in CI. Its purpose is the one gap the design-time research
couldn't close: confirming all 13 types actually **import successfully** via Moodle's real XML
question importer, not just that the generated XML is well-formed and structurally plausible.
This matters most for Calculated (schema derived from source reading, not a live round-trip) but
is worth running for every type once, since a generator bug could produce well-formed-but-rejected
XML for any of them.

- [ ] **Step 1: Write the smoke test script**

```python
# scripts/smoke_test_live_moodle.py
"""Manual, one-off verification: generate one sample question of every type this
project supports, write them to a single Moodle XML file, and print instructions
for importing it into a real Moodle instance by hand.

Not part of the automated test suite -- this project has no live Moodle instance of
its own. Run this against any Moodle 4.x/5.x instance you have access to (e.g. the
Nuyina Data Officer Training LMS's dev-env Moodle) via Site administration ->
Question bank -> Import -> Moodle XML format, then confirm all 13 questions import
without error and preview correctly, especially the Calculated question (see this
plan's Global Constraints -- its schema was derived from source reading, not a live
round-trip, unlike the other 12 types).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.moodle_xml import (
    MultipleChoiceQuestion, TrueFalseQuestion, NumericalQuestion, DescriptionQuestion,
    ShortAnswerQuestion, EssayQuestion, MatchingQuestion, ClozeBlank, ClozeQuestion,
    DragIntoTextQuestion, DragOntoImageQuestion, DragMarkersQuestion,
    SelectMissingWordsQuestion, OrderingQuestion, CalculatedWildcard, CalculatedQuestion,
    write_moodle_xml,
)

# A 1x1 transparent PNG, valid minimal image bytes for the two drag-onto-image types.
_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "0000004945454e44ae426082"
)

questions = [
    MultipleChoiceQuestion(name="Smoke MC", questiontext="What color is the sky?", correct="Blue", incorrect=["Green", "Red", "Purple"]),
    TrueFalseQuestion(name="Smoke TF", questiontext="The sky is blue.", answer=True),
    NumericalQuestion(name="Smoke Numerical", questiontext="What is 2 + 2?", answer=4.0),
    DescriptionQuestion(name="Smoke Description", text="This is informational only."),
    ShortAnswerQuestion(name="Smoke Short Answer", questiontext="Capital of France?", answer="Paris"),
    EssayQuestion(name="Smoke Essay", questiontext="Describe the water cycle."),
    MatchingQuestion(name="Smoke Matching", questiontext="Match country to capital.", pairs=[("France", "Paris"), ("Germany", "Berlin"), ("Italy", "Rome")]),
    ClozeQuestion(
        name="Smoke Cloze",
        template="The capital of France is {}.",
        blanks=[ClozeBlank(kind="SHORTANSWER", correct="Paris")],
    ),
    DragIntoTextQuestion(
        name="Smoke Drag Into Text",
        questiontext_with_blanks="The stage that writes raw files is [[1]].",
        drag_items=[("OpenRVDAS", 1)],
    ),
    DragOntoImageQuestion(
        name="Smoke Drag Onto Image",
        questiontext="Label the diagram.",
        image_bytes=_MINIMAL_PNG,
        image_filename="smoke.png",
        drags=[("A", 1)],
        drops=[(1, 10, 10)],
    ),
    DragMarkersQuestion(
        name="Smoke Drag Markers",
        questiontext="Mark the location.",
        image_bytes=_MINIMAL_PNG,
        image_filename="smoke.png",
        drags=["A"],
        drops=[(1, "circle", "10,10;5")],
    ),
    SelectMissingWordsQuestion(
        name="Smoke Select Missing Words",
        questiontext_with_blanks="The [[1]] sat on the mat.",
        options=[("cat", 1), ("dog", 1)],
    ),
    OrderingQuestion(name="Smoke Ordering", questiontext="Put in order.", items_in_order=["First", "Second", "Third"]),
    CalculatedQuestion(
        name="Smoke Calculated",
        questiontext_with_wildcards="What is {x} + {y}?",
        formula="{x}+{y}",
        wildcards=[CalculatedWildcard(name="x", minimum=1, maximum=10), CalculatedWildcard(name="y", minimum=1, maximum=10)],
    ),
]

output_path = "smoke_test_output.xml"
write_moodle_xml(questions, output_path)
print(f"Wrote {len(questions)} questions to {output_path}")
print("Import this file into a real Moodle instance: Site administration -> Question bank ->")
print("Import -> Moodle XML format -> upload this file. Confirm all 13 questions import with")
print("no errors and preview correctly in the question bank, especially the Calculated one.")
```

- [ ] **Step 2: Run it and manually verify against a real Moodle instance**

```bash
python3 scripts/smoke_test_live_moodle.py
```

Then, against any Moodle 4.x/5.x instance you have import access to: Site administration →
Question bank → Import → select "Moodle XML format" → upload `smoke_test_output.xml`. Expected:
all 13 questions import with zero errors. Open each in the question bank's preview and confirm it
renders sensibly (this is a smoke test for "does it import and render," not a content-quality
review). Pay particular attention to the Calculated question — if it fails, re-check
`CalculatedQuestion`/`CalculatedWildcard` against `question/format/xml/format.php`'s
`import_calculated()` method in the Moodle instance you're testing against, since this is the one
type this plan's schema wasn't verified against a live round-trip or shipped fixture.

- [ ] **Step 3: Record the result and commit**

If every type imported cleanly, commit the smoke test script as-is. If any type failed, fix the
corresponding dataclass in `scripts/moodle_xml.py` (following the same TDD steps as its original
task — add a regression test reproducing the specific structural gap first, then fix it), re-run
this smoke test, and only commit once all 13 import cleanly.

```bash
git add scripts/smoke_test_live_moodle.py
git commit -m "test: live-round-trip smoke test for all 13 question types"
```

---

### Task 10: Answer-length distribution enforcement

**Files:**
- Create: `scripts/length_distribution.py`
- Create: `tests/test_length_distribution.py`

**Interfaces:**
- Consumes: any object exposing `.option_lengths() -> tuple[int, list[int]]` (currently only
  `MultipleChoiceQuestion` from Task 2 — `TrueFalseQuestion`/`MatchingQuestion` etc. don't have a
  meaningful "distractor length" concept and are excluded from this check).
- Produces: `classify_position(correct_length: int, distractor_lengths: list[int]) -> str`
  (returns `"shortest"`, `"longest"`, or `"middle"`). `check_distribution(items: list, tolerance:
  int = 1, min_questions: int = 5) -> dict` — `items` is a list of objects with `.option_lengths()`
  and a `name` attribute (or `(name, option_lengths_tuple)` pairs); returns a report dict with
  `status` (`"pass"`, `"fail"`, or `"insufficient_data"`), `counts`, `target_counts`,
  `out_of_range_buckets`, and `suggestions`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_length_distribution.py
from scripts.length_distribution import classify_position, check_distribution


def test_classify_position_shortest():
    assert classify_position(correct_length=20, distractor_lengths=[50, 60, 55]) == "shortest"


def test_classify_position_longest():
    assert classify_position(correct_length=90, distractor_lengths=[50, 20, 55]) == "longest"


def test_classify_position_middle():
    assert classify_position(correct_length=50, distractor_lengths=[20, 90, 55]) == "middle"


def test_classify_position_all_options_equal_length_is_middle():
    assert classify_position(correct_length=50, distractor_lengths=[50, 50, 50]) == "middle"


def test_classify_position_tied_for_shortest_still_counts_as_shortest():
    assert classify_position(correct_length=20, distractor_lengths=[20, 90, 55]) == "shortest"


class _FakeMCQ:
    def __init__(self, name, correct_length, distractor_lengths):
        self.name = name
        self._correct_length = correct_length
        self._distractor_lengths = distractor_lengths

    def option_lengths(self):
        return self._correct_length, self._distractor_lengths


def test_check_distribution_reports_insufficient_data_below_min_questions():
    items = [_FakeMCQ("Q1", 20, [50, 60])]
    report = check_distribution(items, min_questions=5)
    assert report["status"] == "insufficient_data"


def test_check_distribution_fails_when_every_correct_answer_is_longest():
    items = [_FakeMCQ(f"Q{i}", 90, [30, 40, 50]) for i in range(10)]
    report = check_distribution(items)
    assert report["status"] == "fail"
    assert "longest" in report["out_of_range_buckets"]
    assert len(report["suggestions"]) > 0


def test_check_distribution_passes_a_well_balanced_set():
    items = []
    for i in range(10):
        if i < 2:
            items.append(_FakeMCQ(f"Q{i}", 30, [80, 40, 50]))  # shortest
        elif i < 4:
            items.append(_FakeMCQ(f"Q{i}", 90, [30, 40, 50]))  # longest
        else:
            items.append(_FakeMCQ(f"Q{i}", 55, [30, 90, 40]))  # middle
    report = check_distribution(items)
    assert report["status"] == "pass"
    assert report["out_of_range_buckets"] == []


def test_check_distribution_within_tolerance_of_one_item_still_passes():
    # 10 questions, target for "longest" is 15% = 1.5 -> tolerance +/-1 means 0-2 or
    # so is acceptable depending on rounding; 3 "longest" out of 10 should still pass
    # with the default tolerance since it's within 1 item of the rounded target.
    items = []
    for i in range(10):
        if i < 3:
            items.append(_FakeMCQ(f"Q{i}", 90, [30, 40, 50]))  # longest
        else:
            items.append(_FakeMCQ(f"Q{i}", 55, [30, 90, 40]))  # middle
    report = check_distribution(items, tolerance=1)
    assert report["status"] == "pass"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_length_distribution.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# scripts/length_distribution.py
"""Enforces the answer-length-distribution rule as code, not as an instruction a
model must remember while drafting -- adapted, with attribution, from
danielcregg/moodle-mcq's own length-balancing rule (see ATTRIBUTION.md). Target:
roughly 15% of correct answers are the shortest option in their question, 15% the
longest, 70% neither -- computed across a whole question set, which defeats even a
"the answer is never the extreme option" heuristic a test-wise trainee might learn.
"""

TARGET_DISTRIBUTION = {"shortest": 0.15, "longest": 0.15, "middle": 0.70}


def classify_position(correct_length: int, distractor_lengths: list) -> str:
    """Where does the correct answer's length rank among all options in one question?"""
    all_lengths = [correct_length] + list(distractor_lengths)
    lo, hi = min(all_lengths), max(all_lengths)
    if lo == hi:
        return "middle"
    if correct_length == lo:
        return "shortest"
    if correct_length == hi:
        return "longest"
    return "middle"


def check_distribution(items: list, tolerance: int = 1, min_questions: int = 5) -> dict:
    """Checks whether `items` (objects with .option_lengths() -> (correct_length,
    [distractor_lengths]) and a .name attribute) collectively approximate
    TARGET_DISTRIBUTION. Returns a report dict, never raises -- callers decide what
    to do with a "fail" status.
    """
    n = len(items)
    if n < min_questions:
        return {
            "status": "insufficient_data",
            "n": n,
            "min_questions": min_questions,
            "counts": {}, "target_counts": {}, "out_of_range_buckets": [], "suggestions": [],
        }

    counts = {"shortest": 0, "longest": 0, "middle": 0}
    classifications = []
    for item in items:
        correct_length, distractor_lengths = item.option_lengths()
        position = classify_position(correct_length, distractor_lengths)
        counts[position] += 1
        classifications.append((item.name, position))

    target_counts = {bucket: round(pct * n) for bucket, pct in TARGET_DISTRIBUTION.items()}
    out_of_range = []
    suggestions = []
    for bucket, target in target_counts.items():
        actual = counts[bucket]
        if abs(actual - target) > tolerance:
            out_of_range.append(bucket)
            if actual > target:
                offenders = [name for name, pos in classifications if pos == bucket]
                suggestions.append(
                    f"'{bucket}' has {actual} questions (target ~{target}) -- consider "
                    f"rebalancing some of: {', '.join(offenders[: target + tolerance + 1])}"
                )
            else:
                suggestions.append(
                    f"'{bucket}' has only {actual} questions (target ~{target}) -- "
                    f"rebalance a 'middle' question's options so its correct answer "
                    f"becomes the {bucket} one, without changing which answer is correct"
                )

    return {
        "status": "fail" if out_of_range else "pass",
        "n": n,
        "counts": counts,
        "target_counts": target_counts,
        "out_of_range_buckets": out_of_range,
        "suggestions": suggestions,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_length_distribution.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/length_distribution.py tests/test_length_distribution.py
git commit -m "feat: answer-length distribution enforcement, adapted from moodle-mcq"
```

---

### Task 11: Structural sanity check

**Files:**
- Create: `scripts/item_sanity_check.py`
- Create: `tests/test_item_sanity_check.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (operates on raw XML text and parsed `ElementTree` elements,
  decoupled from the dataclasses themselves — mirrors how the sibling Nuyina LMS project's
  `content_sanity_check.py` operates on raw file text rather than on `gift_format.py`'s dataclasses).
- Produces: `check_well_formed_xml(xml_text: str) -> list[str]`, `check_no_placeholders(text: str)
  -> list[str]`, `check_cloze_blank_count_matches_answers(question_element) -> list[str]`,
  `check_ordering_minimum_items(question_element) -> list[str]`, and a CLI entry point
  `python3 -m scripts.item_sanity_check <quiz.xml path>` running every applicable check against
  every `<question>` in the file, printing every problem found, exiting `1` if any were found or
  `0` (printing `OK`) otherwise.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_item_sanity_check.py
import xml.etree.ElementTree as ET

from scripts.item_sanity_check import (
    check_well_formed_xml,
    check_no_placeholders,
    check_cloze_blank_count_matches_answers,
    check_ordering_minimum_items,
)


def test_check_well_formed_xml_accepts_valid_xml():
    assert check_well_formed_xml("<quiz><question type=\"description\"></question></quiz>") == []


def test_check_well_formed_xml_rejects_malformed_xml():
    problems = check_well_formed_xml("<quiz><question>not closed</quiz>")
    assert len(problems) == 1
    assert "not well-formed" in problems[0]


def test_check_no_placeholders_accepts_clean_text():
    assert check_no_placeholders("A real, finished question about OpenVDM.") == []


def test_check_no_placeholders_detects_todo_marker():
    problems = check_no_placeholders("What is the answer? TODO: write distractors.")
    assert len(problems) == 1
    assert "TODO" in problems[0]


def test_check_cloze_blank_count_matches_answers_accepts_matching_count():
    xml_text = (
        '<question type="cloze">'
        '<questiontext format="html"><text>'
        '<![CDATA[The capital is {1:SHORTANSWER:=Paris}, population {1:NUMERICAL:=2000000:100000}.]]>'
        '</text></questiontext>'
        '</question>'
    )
    element = ET.fromstring(xml_text)
    assert check_cloze_blank_count_matches_answers(element) == []


def test_check_cloze_blank_count_matches_answers_rejects_zero_blanks():
    xml_text = (
        '<question type="cloze">'
        '<questiontext format="html"><text><![CDATA[No blanks here at all.]]></text></questiontext>'
        '</question>'
    )
    element = ET.fromstring(xml_text)
    problems = check_cloze_blank_count_matches_answers(element)
    assert len(problems) == 1
    assert "no embedded" in problems[0].lower()


def test_check_ordering_minimum_items_accepts_three_or_more():
    xml_text = (
        '<question type="ordering">'
        '<answer fraction="1"><text>A</text></answer>'
        '<answer fraction="2"><text>B</text></answer>'
        '<answer fraction="3"><text>C</text></answer>'
        '</question>'
    )
    element = ET.fromstring(xml_text)
    assert check_ordering_minimum_items(element) == []


def test_check_ordering_minimum_items_rejects_fewer_than_three():
    xml_text = (
        '<question type="ordering">'
        '<answer fraction="1"><text>A</text></answer>'
        '<answer fraction="2"><text>B</text></answer>'
        '</question>'
    )
    element = ET.fromstring(xml_text)
    problems = check_ordering_minimum_items(element)
    assert len(problems) == 1
    assert "at least 3" in problems[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_item_sanity_check.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# scripts/item_sanity_check.py
import re
import sys
import xml.etree.ElementTree as ET

_PLACEHOLDER_MARKERS = ["TODO", "TBD", "[fill in]", "[FIXME]", "FIXME", "<PLACEHOLDER>", "XXX"]
_CLOZE_BLANK_PATTERN = re.compile(r"\{\d+:(SHORTANSWER|NUMERICAL|MULTICHOICE)[A-Z_]*:")


def check_well_formed_xml(xml_text: str) -> list:
    try:
        ET.fromstring(xml_text)
    except ET.ParseError as e:
        return [f"XML is not well-formed: {e}"]
    return []


def check_no_placeholders(text: str) -> list:
    problems = []
    for marker in _PLACEHOLDER_MARKERS:
        if marker in text:
            problems.append(f"Found placeholder marker {marker!r} in content")
    return problems


def check_cloze_blank_count_matches_answers(question_element) -> list:
    """A Cloze question's questiontext must contain at least one embedded
    {N:TYPE:=...} answer blank -- a Cloze question with zero blanks is just a
    Description question with extra structure, and is almost certainly a drafting
    mistake rather than an intentional choice."""
    text_el = question_element.find("questiontext/text")
    text = text_el.text or "" if text_el is not None else ""
    blank_count = len(_CLOZE_BLANK_PATTERN.findall(text))
    if blank_count == 0:
        return ["Cloze question has no embedded answer blanks ({N:TYPE:=...}) in its questiontext"]
    return []


def check_ordering_minimum_items(question_element) -> list:
    """An Ordering question needs at least 3 items -- fewer than that isn't a
    meaningful sequencing task (this mirrors OrderingQuestion's own __post_init__
    check in scripts/moodle_xml.py, but re-checked here at the XML level so a quiz
    file assembled by hand or from another source is caught too)."""
    answers = question_element.findall("answer")
    if len(answers) < 3:
        return [f"Ordering question has only {len(answers)} item(s) -- needs at least 3"]
    return []


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 -m scripts.item_sanity_check <quiz.xml>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        xml_text = f.read()

    problems = check_well_formed_xml(xml_text)
    problems += [f"{path}: {p}" for p in check_no_placeholders(xml_text)]

    if not problems:
        root = ET.fromstring(xml_text)
        for question in root.findall("question"):
            qtype = question.get("type")
            name_el = question.find("name/text")
            qname = name_el.text if name_el is not None else "(unnamed)"
            if qtype == "cloze":
                problems += [f"{qname}: {p}" for p in check_cloze_blank_count_matches_answers(question)]
            elif qtype == "ordering":
                problems += [f"{qname}: {p}" for p in check_ordering_minimum_items(question)]

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_item_sanity_check.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/item_sanity_check.py tests/test_item_sanity_check.py
git commit -m "feat: structural sanity checks -- well-formedness, placeholders, per-type structure"
```

---

### Task 12: Pedagogy and Moodle XML format references

**Files:**
- Create: `references/pedagogy.md`
- Create: `references/moodle-xml-formats.md`

**Interfaces:**
- Consumes: nothing (these are reference documents `SKILL.md`, written in Task 13, points to).
- Produces: the content Task 13's `SKILL.md` cites by filename.

This task has no code and is not TDD-shaped.

- [ ] **Step 1: Write `references/pedagogy.md`**

```markdown
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
```

- [ ] **Step 2: Write `references/moodle-xml-formats.md`**

```markdown
# Moodle XML format reference

Every template below was verified against a real, running Moodle 5.0.2 instance
(`bitnamilegacy/moodle:5.0.2`) during this project's design — either a live create-then-export
round-trip via `qformat_xml`, or Moodle's own shipped test fixtures / source code where a live
round-trip wasn't practical (Calculated; drag-and-drop onto image/markers, which need a real
background image binary to round-trip meaningfully). See `scripts/moodle_xml.py` for the
implementation — this document is a human-readable reference to the same facts, not a
duplicate source of truth to keep in sync by hand.

## Fields present on every question type

`<name><text>`, `<questiontext format="html"><text>`, `<generalfeedback format="html"><text>`,
`<defaultgrade>`, `<penalty>`, `<hidden>0</hidden>`, `<idnumber></idnumber>`.

## Combined-feedback block (multichoice, matching, ddwtos, ddimageortext, ddmarker, gapselect,
ordering, calculated)

`<correctfeedback format="html"><text>`, `<partiallycorrectfeedback format="html"><text>`,
`<incorrectfeedback format="html"><text>`, optionally followed by self-closing `<shownumcorrect/>`.

## Two real naming traps

- `multianswer` (the qtype's internal name) → XML `type="cloze"`.
- `match` (the qtype's internal name) → XML `type="matching"`.

## Per-type notes

**Multiple Choice** (`multichoice`): `<single>`, `<shuffleanswers>`, `<answernumbering>abc</answernumbering>`,
one `<answer fraction="100|0">` per option.

**True/False** (`truefalse`): two `<answer>` elements, text `"true"`/`"false"`, fraction 100 on
whichever matches the answer — map feedback by fraction value, never by position (unlike GIFT's
`{ANSWER#wrong#right}` convention, which has no equivalent ambiguity here).

**Numerical** (`numerical`): single `<answer>` with `<tolerance>`; requires
`<unitgradingtype>`/`<unitpenalty>`/`<showunits>`/`<unitsleft>` even with no units configured.

**Description** (`description`): no `<answer>` elements; `<defaultgrade>0.0000000</defaultgrade>`.

**Short Answer** (`shortanswer`): requires `<usecase>` (case-sensitivity flag) even for one answer.

**Essay** (`essay`): `<responseformat>editor</responseformat>`, `<responserequired>`,
`<responsefieldlines>`, plus several empty-but-present fields Moodle always emits.

**Matching** (`matching`): flat list of `<subquestion>`/`<answer>` text pairs, no explicit key —
correctness is pairing by document order.

**Cloze / Embedded Answers** (`cloze`): all complexity lives inside `<questiontext><text>` as
`{weight:TYPE:=correct~wrong1~wrong2}` embedded mini-language — no separate answer structure at
the parent-question level at all.

**Drag-and-drop into Text** (`ddwtos`): `[[1]]`/`[[2]]` blank markers in questiontext;
`<dragbox><text>/<group>` elements, optional self-closing `<infinite/>` for reusable items.

**Drag-and-drop onto Image** (`ddimageortext`): background image as `<file name="..."
encoding="base64">`; `<drag><no>/<text>/<draggroup>` (top-level, 1-indexed); `<drop>
<text>/<no>/<choice>/<xleft>/<ytop>` (choice references the correct drag's `<no>`).

**Drag-and-drop Markers** (`ddmarker`): same image-embedding as onto-image; `<drop>
<no>/<shape>/<coords>/<choice>` where shape is `circle` (`x,y;radius`), `poly`
(`x1,y1;x2,y2;...`), or `rectangle` (`x,y;width,height`); self-closing `<showmisplaced/>` flag.

**Select Missing Words** (`gapselect`): `[[1]]`/`[[2]]` blank markers; choices are
`<selectoption><text>/<group>` — NOT the generic `<answer>` block other types use.

**Ordering** (`ordering`): `<answer>` blocks in correct order, `fraction` holds the 1-indexed
sequence POSITION (not a percentage-correct weight, unlike every other type using `<answer>`);
`<layouttype>` (VERTICAL/HORIZONTAL), `<gradingtype>` (ABSOLUTE_POSITION and others).

**Calculated** (`calculated`): wildcards like `{x}` in both questiontext and the answer's formula
text; `<dataset_definitions><dataset_definition>` per wildcard (`status`/`name`/`type`/
`distribution`/`minimum`/`maximum`/`decimals`/`itemcount`/`dataset_items`/`number_of_items`).
**Not verified via live round-trip or shipped fixture** — see `scripts/smoke_test_live_moodle.py`.
```

- [ ] **Step 3: Commit**

```bash
git add references/pedagogy.md references/moodle-xml-formats.md
git commit -m "docs: pedagogy and Moodle XML format reference material"
```

---

### Task 13: SKILL.md — the orchestration layer

**Files:**
- Create: `SKILL.md`

**Interfaces:**
- Consumes: every module from Tasks 2, 10, 11 by name; `references/pedagogy.md` and
  `references/moodle-xml-formats.md` from Task 12.
- Produces: the actual invokable Claude Skill. Nothing later depends on this — it's the last task.

This task has no code and is not TDD-shaped — it's the prose workflow tying everything together.

- [ ] **Step 1: Write `SKILL.md`**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "feat: SKILL.md orchestration layer"
```

---

## Self-Review Notes

**Spec coverage:** Goal 1 (whole-document-to-whole-quiz) and Goal 2 (considered type mixture) →
`SKILL.md`'s workflow (Task 13), grounded in `references/pedagogy.md` (Task 12). Goal 3 (every
practical type) → Tasks 2-8 cover all 13 in-scope types. Goal 4 (length-distribution as code) →
Task 10. Goal 5 (ship as a real tool) → every dataclass produces real, importable XML; Task 9's
live smoke test validates this directly. Goal 6 (self-contained/portable) → no Nuyina dependency
anywhere in this plan; confirmed by Task 1's standalone LICENSE/README. Licensing decision (CC
BY-SA 4.0 + ATTRIBUTION.md) → Task 1. Non-goals (no GIFT, no Calculated Multi/Simple, no Random
Short-Answer Matching, no hard exclusion of Short Answer/Essay, no `import_xml.php` for the LMS)
— none of the 13 tasks build any of these; the LMS integration is correctly left to Jira task
NDO-611 under Epic NDO-513, outside this plan.

**Placeholder scan:** no TBD/TODO/"add appropriate"/"similar to Task N" patterns found in any
task's steps — every task has complete, real code or complete, real prose content.

**Type consistency:** checked every dataclass's field names and `.to_xml()`/`.option_lengths()`
signatures are used identically across the task that defines them and any later task/reference
that mentions them (`MultipleChoiceQuestion.option_lengths()` in Task 2 matches
`length_distribution.py`'s consumption contract in Task 10; `ClozeBlank`/`ClozeQuestion` in Task 5
match `SKILL.md`'s reference in Task 13; the two naming traps — `cloze`/`matching` — are stated
consistently in Global Constraints, Task 5, Task 4, and both reference documents in Task 12).
