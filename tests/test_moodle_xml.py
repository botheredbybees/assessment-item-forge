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
