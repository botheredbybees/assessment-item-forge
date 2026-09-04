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
                   f'    <text>{_cdata(self.correct)}</text>\n'
                   f'{_text_block("feedback", self.correct_feedback_text, indent="    ")}\n'
                   f'  </answer>']
        for opt in self.incorrect:
            answers.append(f'  <answer fraction="0" format="html">\n'
                            f'    <text>{_cdata(opt)}</text>\n'
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
            f'    <text>{_cdata("true")}</text>\n'
            f'{_text_block("feedback", true_feedback, indent="    ")}\n'
            f'  </answer>\n'
            f'  <answer fraction="{false_fraction}" format="html">\n'
            f'    <text>{_cdata("false")}</text>\n'
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
