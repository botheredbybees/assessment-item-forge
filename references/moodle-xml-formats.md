# Moodle XML format reference

Every template below was checked against Moodle 5.0.2 during this project's design, but not all
to the same degree of confidence -- there are three distinct verification tiers, and it matters
which one a given type falls into:

- **(a) Live round-trip verified**: created via a real, running Moodle 5.0.2 instance
  (`bitnamilegacy/moodle:5.0.2`), then exported back out via `qformat_xml` and compared. The
  strongest tier -- confirms the whole pipeline actually works, not just that the XML shape looks
  right on paper. Applies to: Multiple Choice, True/False, Numerical, Description, Short Answer,
  Essay, Matching, Cloze.
- **(b) Verified against Moodle's own shipped test fixtures**: no live round-trip, but checked
  against a real `.moodle.xml` fixture file shipped in Moodle's own source tree
  (`question/type/<qtype>/tests/fixtures/`). Applies to: Select Missing Words (`gapselect`),
  Ordering.
- **(c) Derived from reading Moodle source code only, not independently verified against a
  running instance**: the XML shape comes from reading the qtype's own `export_to_xml`/
  `qformat_xml` implementation, with no live round-trip and no shipped fixture used. The weakest
  tier -- correct only insofar as the source reading was accurate. Applies to: Drag-and-drop into
  Text (`ddwtos`), Drag-and-drop onto Image (`ddimageortext`), Drag-and-drop Markers (`ddmarker`)
  — a live round-trip wasn't practical for these three since they need a real background image
  binary to round-trip meaningfully — and Calculated (`calculated`), for which no shipped fixture
  existed either.

See `scripts/moodle_xml.py` for the implementation — this document is a human-readable reference
to the same facts, not a duplicate source of truth to keep in sync by hand.

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
