import subprocess
import sys
import xml.etree.ElementTree as ET

from scripts.item_sanity_check import (
    check_well_formed_xml,
    check_no_placeholders,
    check_cloze_blank_count_matches_answers,
    check_ordering_minimum_items,
    _strip_file_payloads,
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


def test_strip_file_payloads_removes_placeholder_marker_inside_file_element():
    # A base64 image payload can randomly contain placeholder-marker substrings
    # (e.g. "TBD") by pure chance -- this is not a hand-authored placeholder and
    # has no fixable "problem" to act on, so it must not survive into the
    # placeholder scan.
    xml_text = (
        '<quiz><question type="ddimageortext">'
        '<file name="diagram.png" path="/" encoding="base64">aaaaTBDbbbbXXXcccc</file>'
        '</question></quiz>'
    )
    stripped = _strip_file_payloads(xml_text)
    assert "TBD" not in stripped
    assert "XXX" not in stripped
    assert check_no_placeholders(stripped) == []
    # Sanity check: without stripping, the same content would have triggered
    # both markers -- confirms the test payload really does contain them.
    unstripped_problems = check_no_placeholders(xml_text)
    assert len(unstripped_problems) == 2


def test_strip_file_payloads_preserves_placeholder_markers_outside_file_element():
    xml_text = (
        '<quiz><question type="description">'
        '<questiontext><text>TODO: write this question</text></questiontext>'
        '<file name="diagram.png" path="/" encoding="base64">aaaaTBDbbbb</file>'
        '</question></quiz>'
    )
    stripped = _strip_file_payloads(xml_text)
    assert "TODO" in stripped
    assert "TBD" not in stripped
    problems = check_no_placeholders(stripped)
    assert len(problems) == 1
    assert "TODO" in problems[0]


def test_placeholder_markers_list_has_no_fixme_double_count():
    xml_text = "Please replace this [FIXME] before shipping."
    problems = check_no_placeholders(xml_text)
    assert len(problems) == 1


def _run_item_sanity_check(tmp_path, xml_text):
    quiz_path = tmp_path / "quiz.xml"
    quiz_path.write_text(xml_text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.item_sanity_check", str(quiz_path)],
        capture_output=True,
        text=True,
    )
    return result


def test_main_reports_placeholder_and_structural_problems_together(tmp_path):
    # A quiz with BOTH a placeholder marker AND a broken Ordering question must
    # report both problems in one pass, not just the placeholder.
    xml_text = (
        '<quiz>'
        '<question type="description">'
        '<questiontext><text>TODO: finish this</text></questiontext>'
        '</question>'
        '<question type="ordering">'
        '<name><text>Broken Ordering</text></name>'
        '<answer fraction="1"><text>A</text></answer>'
        '<answer fraction="2"><text>B</text></answer>'
        '</question>'
        '</quiz>'
    )
    result = _run_item_sanity_check(tmp_path, xml_text)
    assert result.returncode == 1
    assert "TODO" in result.stderr
    assert "at least 3" in result.stderr
