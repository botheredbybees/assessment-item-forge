import re
import sys
import xml.etree.ElementTree as ET

_PLACEHOLDER_MARKERS = ["TODO", "TBD", "[fill in]", "FIXME", "<PLACEHOLDER>", "XXX"]
_CLOZE_BLANK_PATTERN = re.compile(r"\{\d+:(SHORTANSWER|NUMERICAL|MULTICHOICE)[A-Z_]*:")
_FILE_PAYLOAD = re.compile(r"(<file\b[^>]*>).*?(</file>)", re.DOTALL)


def check_well_formed_xml(xml_text: str) -> list:
    try:
        ET.fromstring(xml_text)
    except ET.ParseError as e:
        return [f"XML is not well-formed: {e}"]
    return []


def _strip_file_payloads(xml_text: str) -> str:
    """Base64 image content inside <file> elements can randomly contain
    placeholder-marker substrings (TBD, XXX, FIXME) by pure chance -- strip
    it before scanning for placeholders, since a false positive here has no
    fixable "problem" to act on. Well-formedness is still checked against
    the original, untouched text."""
    return _FILE_PAYLOAD.sub(r"\1\2", xml_text)


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

    well_formed_problems = check_well_formed_xml(xml_text)
    problems = list(well_formed_problems)
    problems += [f"{path}: {p}" for p in check_no_placeholders(_strip_file_payloads(xml_text))]

    if not well_formed_problems:
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
