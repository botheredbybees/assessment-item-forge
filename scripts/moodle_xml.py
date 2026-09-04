import base64
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


def _plain_text(text: str, indent: str = "  ") -> str:
    """A bare <text>...</text> element with NO wrapping tag and NO format
    attribute -- the shape an <answer>'s own text child uses (the format
    attribute already lives on the parent <answer format="..."> element).
    Deliberately distinct from _text_block(), which always adds a format
    attribute on its wrapping tag -- do not use _text_block("text", ...) for
    this shape, it produces an incorrect nested <text><text>...</text></text>
    structure. Confirmed live against a running Moodle 5.0.2 instance.
    """
    return f'{indent}<text>{_cdata(text)}</text>'


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
                   f'{_plain_text(self.correct, indent="    ")}\n'
                   f'{_text_block("feedback", self.correct_feedback_text, indent="    ")}\n'
                   f'  </answer>']
        for opt in self.incorrect:
            answers.append(f'  <answer fraction="0" format="html">\n'
                            f'{_plain_text(opt, indent="    ")}\n'
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
            f'{_plain_text("true", indent="    ")}\n'
            f'{_text_block("feedback", true_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'  <answer fraction="{false_fraction}" format="html">\n'
            f'{_plain_text("false", indent="    ")}\n'
            f'{_text_block("feedback", false_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'</question>'
        )


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
            f'{_plain_text(str(self.answer), indent="    ")}\n'
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
            f'{_plain_text(self.answer, indent="    ")}\n'
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
                f'{_plain_text(prompt, indent="    ")}\n'
                f'    <answer>\n'
                f'{_plain_text(answer, indent="      ")}\n'
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


@dataclass
class DragIntoTextQuestion:
    """Confirmed by reading Moodle source directly (question/type/ddwtos/questiontype.php's
    export_to_xml) -- not verified via a live round-trip or shipped fixture, unlike most other
    types in this file. XML type "ddwtos". Blanks in questiontext are literal [[1]],
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
                f'{_plain_text(text, indent="    ")}\n'
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
    """Confirmed by reading Moodle source directly (question/type/ddimageortext/questiontype.php's
    export_to_xml) -- not verified via a live round-trip or shipped fixture, unlike most other
    types in this file. XML type "ddimageortext". The background image is embedded as a
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
                f'{_plain_text(text, indent="    ")}\n'
                f'    <draggroup>{draggroup}</draggroup>\n'
                f'  </drag>'
            )
        drops_xml = []
        for drag_no, xleft, ytop in self.drops:
            drops_xml.append(
                f'  <drop>\n'
                f'    <text></text>\n'
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
    """Confirmed by reading Moodle source directly (question/type/ddmarker/questiontype.php's
    export_to_xml) -- not verified via a live round-trip or shipped fixture, unlike most other
    types in this file. XML type "ddmarker". Drop zones are shapes, not points: <shape>
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
                f'{_plain_text(text, indent="    ")}\n'
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
            f'  <selectoption>\n{_plain_text(text, indent="    ")}\n    <group>{group}</group>\n  </selectoption>'
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
            f'  <answer fraction="{i}.0000000" format="html">\n{_plain_text(item, indent="    ")}\n  </answer>'
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
        # Note: status/name/distribution/minimum/maximum/decimals carry NO format
        # attribute in the verified schema (unlike questiontext/feedback-family
        # fields) -- each is a plain <tag><text>value</text></tag>, so _text_block
        # (which always adds format="...") is not used here.
        return (
            f'    <dataset_definition>\n'
            f'      <status>\n{_plain_text("private", indent="        ")}\n      </status>\n'
            f'      <name>\n{_plain_text(self.name, indent="        ")}\n      </name>\n'
            f'      <type>calculated</type>\n'
            f'      <distribution>\n{_plain_text("uniform", indent="        ")}\n      </distribution>\n'
            f'      <minimum>\n{_plain_text(str(self.minimum), indent="        ")}\n      </minimum>\n'
            f'      <maximum>\n{_plain_text(str(self.maximum), indent="        ")}\n      </maximum>\n'
            f'      <decimals>\n{_plain_text(str(self.decimals), indent="        ")}\n      </decimals>\n'
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
            f'{_plain_text(self.formula, indent="    ")}\n'
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


def write_moodle_xml(questions: list, path: str) -> None:
    """Writes a list of question dataclasses (each exposing .to_xml()) as one Moodle
    XML quiz file -- the whole document-to-quiz output of assessment-item-forge."""
    bodies = "\n\n".join(q.to_xml() for q in questions)
    xml_text = f'<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n{bodies}\n</quiz>\n'
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_text)
