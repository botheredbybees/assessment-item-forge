# scripts/smoke_test_live_moodle.py
"""Manual, one-off verification: generate one sample question of every type this
project supports, write them to a single Moodle XML file, and print instructions
for importing it into a real Moodle instance by hand.

Not part of the automated test suite -- this project has no live Moodle instance of
its own. Run this against any Moodle 4.x/5.x instance you have access to (e.g. the
Nuyina Data Officer Training LMS's dev-env Moodle) via Site administration ->
Question bank -> Import -> Moodle XML format, then confirm all of the questions
below import without error and preview correctly, especially the Calculated
question (see this plan's Global Constraints -- its schema was derived from source
reading, not a live round-trip, unlike most of the other types).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.moodle_xml import (
    MultipleChoiceQuestion, TrueFalseQuestion, NumericalQuestion, DescriptionQuestion,
    ShortAnswerQuestion, EssayQuestion, MatchingQuestion, ClozeBlank, ClozeQuestion,
    DragIntoTextQuestion, DragOntoImageQuestion, DragMarkersQuestion,
    SelectMissingWordsQuestion, OrderingQuestion, CalculatedWildcard, CalculatedQuestion,
    write_moodle_xml,
)

# A 1x1 transparent PNG, valid minimal image bytes for the two drag-onto-image types.
_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "0000004945454e44ae426082"
)

questions = [
    MultipleChoiceQuestion(name="Smoke MC", questiontext="What color is the sky?", correct="Blue", incorrect=["Green", "Red", "Purple"]),
    TrueFalseQuestion(name="Smoke TF", questiontext="The sky is blue.", answer=True),
    NumericalQuestion(name="Smoke Numerical", questiontext="What is 2 + 2?", answer=4.0),
    DescriptionQuestion(name="Smoke Description", text="This is informational only."),
    ShortAnswerQuestion(name="Smoke Short Answer", questiontext="Capital of France?", answer="Paris"),
    EssayQuestion(name="Smoke Essay", questiontext="Describe the water cycle."),
    MatchingQuestion(name="Smoke Matching", questiontext="Match country to capital.", pairs=[("France", "Paris"), ("Germany", "Berlin"), ("Italy", "Rome")]),
    ClozeQuestion(
        name="Smoke Cloze",
        template="The capital of France is {}.",
        blanks=[ClozeBlank(kind="SHORTANSWER", correct="Paris")],
    ),
    DragIntoTextQuestion(
        name="Smoke Drag Into Text",
        questiontext_with_blanks="The stage that writes raw files is [[1]].",
        drag_items=[("OpenRVDAS", 1)],
    ),
    DragOntoImageQuestion(
        name="Smoke Drag Onto Image",
        questiontext="Label the diagram.",
        image_bytes=_MINIMAL_PNG,
        image_filename="smoke.png",
        drags=[("A", 1)],
        drops=[(1, 10, 10)],
    ),
    DragMarkersQuestion(
        name="Smoke Drag Markers",
        questiontext="Mark the location.",
        image_bytes=_MINIMAL_PNG,
        image_filename="smoke.png",
        drags=["A"],
        drops=[(1, "circle", "10,10;5")],
    ),
    SelectMissingWordsQuestion(
        name="Smoke Select Missing Words",
        questiontext_with_blanks="The [[1]] sat on the mat.",
        options=[("cat", 1), ("dog", 1)],
    ),
    OrderingQuestion(name="Smoke Ordering", questiontext="Put in order.", items_in_order=["First", "Second", "Third"]),
    CalculatedQuestion(
        name="Smoke Calculated",
        questiontext_with_wildcards="What is {x} + {y}?",
        formula="{x}+{y}",
        wildcards=[CalculatedWildcard(name="x", minimum=1, maximum=10), CalculatedWildcard(name="y", minimum=1, maximum=10)],
    ),
]

output_path = "smoke_test_output.xml"
write_moodle_xml(questions, output_path)
print(f"Wrote {len(questions)} questions to {output_path}")
print("Import this file into a real Moodle instance: Site administration -> Question bank ->")
print(f"Import -> Moodle XML format -> upload this file. Confirm all {len(questions)} questions import")
print("with no errors and preview correctly in the question bank, especially the Calculated one.")
