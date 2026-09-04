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
