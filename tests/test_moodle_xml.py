import xml.etree.ElementTree as ET

from scripts.moodle_xml import (
    MultipleChoiceQuestion,
    TrueFalseQuestion,
    NumericalQuestion,
    DescriptionQuestion,
    ShortAnswerQuestion,
    EssayQuestion,
    MatchingQuestion,
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
