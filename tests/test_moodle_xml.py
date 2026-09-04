import base64
import xml.etree.ElementTree as ET
import pytest

from scripts.moodle_xml import (
    MultipleChoiceQuestion,
    TrueFalseQuestion,
    NumericalQuestion,
    DescriptionQuestion,
    ShortAnswerQuestion,
    EssayQuestion,
    MatchingQuestion,
    ClozeBlank,
    ClozeQuestion,
    DragIntoTextQuestion,
    DragOntoImageQuestion,
    DragMarkersQuestion,
    SelectMissingWordsQuestion,
    OrderingQuestion,
    CalculatedWildcard,
    CalculatedQuestion,
    write_moodle_xml,
    _cdata,
    _text_block,
)


def test_cdata_wraps_text():
    assert _cdata("hello") == "<![CDATA[hello]]>"


def test_cdata_escapes_literal_cdata_close_sequence():
    # A literal "]]>" inside the text would prematurely close the CDATA section if
    # not handled -- split it into two adjacent CDATA sections instead, the standard
    # escape for this case.
    result = _cdata("before]]>after")
    assert result == "<![CDATA[before]]]]><![CDATA[>after]]>"


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
