from scripts.length_distribution import classify_position, check_distribution


def test_classify_position_shortest():
    assert classify_position(correct_length=20, distractor_lengths=[50, 60, 55]) == "shortest"


def test_classify_position_longest():
    assert classify_position(correct_length=90, distractor_lengths=[50, 20, 55]) == "longest"


def test_classify_position_middle():
    assert classify_position(correct_length=50, distractor_lengths=[20, 90, 55]) == "middle"


def test_classify_position_all_options_equal_length_is_middle():
    assert classify_position(correct_length=50, distractor_lengths=[50, 50, 50]) == "middle"


def test_classify_position_tied_for_shortest_still_counts_as_shortest():
    assert classify_position(correct_length=20, distractor_lengths=[20, 90, 55]) == "shortest"


class _FakeMCQ:
    def __init__(self, name, correct_length, distractor_lengths):
        self.name = name
        self._correct_length = correct_length
        self._distractor_lengths = distractor_lengths

    def option_lengths(self):
        return self._correct_length, self._distractor_lengths


def test_check_distribution_reports_insufficient_data_below_min_questions():
    items = [_FakeMCQ("Q1", 20, [50, 60])]
    report = check_distribution(items, min_questions=5)
    assert report["status"] == "insufficient_data"


def test_check_distribution_fails_when_every_correct_answer_is_longest():
    items = [_FakeMCQ(f"Q{i}", 90, [30, 40, 50]) for i in range(10)]
    report = check_distribution(items)
    assert report["status"] == "fail"
    assert "longest" in report["out_of_range_buckets"]
    assert len(report["suggestions"]) > 0


def test_check_distribution_passes_a_well_balanced_set():
    items = []
    for i in range(10):
        if i < 2:
            items.append(_FakeMCQ(f"Q{i}", 30, [80, 40, 50]))  # shortest
        elif i < 4:
            items.append(_FakeMCQ(f"Q{i}", 90, [30, 40, 50]))  # longest
        else:
            items.append(_FakeMCQ(f"Q{i}", 55, [30, 90, 40]))  # middle
    report = check_distribution(items)
    assert report["status"] == "pass"
    assert report["out_of_range_buckets"] == []


def test_check_distribution_within_tolerance_of_one_item_still_passes():
    # 20 questions: target_counts = {shortest: 3, longest: 3, middle: 14}. Give 4
    # "longest" (target 3, diff 1 -- within tolerance), 3 "shortest" (diff 0), and
    # 13 "middle" (target 14, diff 1 -- within tolerance) -- ALL THREE buckets must
    # independently be within tolerance for a "pass", not just the one bucket being
    # deliberately tested; a smaller n here previously left "shortest" at 0 against
    # a target of 2, which correctly failed on its own even though "longest" alone
    # was within tolerance -- that was a bug in this test, not in check_distribution.
    items = []
    for i in range(20):
        if i < 4:
            items.append(_FakeMCQ(f"Q{i}", 90, [30, 40, 50]))  # longest
        elif i < 7:
            items.append(_FakeMCQ(f"Q{i}", 20, [50, 60, 55]))  # shortest
        else:
            items.append(_FakeMCQ(f"Q{i}", 55, [30, 90, 40]))  # middle
    report = check_distribution(items, tolerance=1)
    assert report["status"] == "pass"
