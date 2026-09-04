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
