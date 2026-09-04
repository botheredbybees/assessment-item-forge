"""Enforces the answer-length-distribution rule as code, not as an instruction a
model must remember while drafting -- adapted, with attribution, from
danielcregg/moodle-mcq's own length-balancing rule (see ATTRIBUTION.md). Target:
roughly 15% of correct answers are the shortest option in their question, 15% the
longest, 70% neither -- computed across a whole question set, which defeats even a
"the answer is never the extreme option" heuristic a test-wise trainee might learn.
"""

TARGET_DISTRIBUTION = {"shortest": 0.15, "longest": 0.15, "middle": 0.70}


def classify_position(correct_length: int, distractor_lengths: list) -> str:
    """Where does the correct answer's length rank among all options in one question?"""
    all_lengths = [correct_length] + list(distractor_lengths)
    lo, hi = min(all_lengths), max(all_lengths)
    if lo == hi:
        return "middle"
    if correct_length == lo:
        return "shortest"
    if correct_length == hi:
        return "longest"
    return "middle"


def check_distribution(items: list, tolerance: int = 1, min_questions: int = 5) -> dict:
    """Checks whether `items` (objects with .option_lengths() -> (correct_length,
    [distractor_lengths]) and a .name attribute) collectively approximate
    TARGET_DISTRIBUTION. Returns a report dict, never raises -- callers decide what
    to do with a "fail" status.
    """
    n = len(items)
    if n < min_questions:
        return {
            "status": "insufficient_data",
            "n": n,
            "min_questions": min_questions,
            "counts": {}, "target_counts": {}, "out_of_range_buckets": [], "suggestions": [],
        }

    counts = {"shortest": 0, "longest": 0, "middle": 0}
    classifications = []
    for item in items:
        correct_length, distractor_lengths = item.option_lengths()
        position = classify_position(correct_length, distractor_lengths)
        counts[position] += 1
        classifications.append((item.name, position))

    target_counts = {bucket: round(pct * n) for bucket, pct in TARGET_DISTRIBUTION.items()}
    out_of_range = []
    suggestions = []
    for bucket, target in target_counts.items():
        actual = counts[bucket]
        if abs(actual - target) > tolerance:
            out_of_range.append(bucket)
            if actual > target:
                offenders = [name for name, pos in classifications if pos == bucket]
                suggestions.append(
                    f"'{bucket}' has {actual} questions (target ~{target}) -- consider "
                    f"rebalancing some of: {', '.join(offenders[: target + tolerance + 1])}"
                )
            else:
                suggestions.append(
                    f"'{bucket}' has only {actual} questions (target ~{target}) -- "
                    f"rebalance a 'middle' question's options so its correct answer "
                    f"becomes the {bucket} one, without changing which answer is correct"
                )

    return {
        "status": "fail" if out_of_range else "pass",
        "n": n,
        "counts": counts,
        "target_counts": target_counts,
        "out_of_range_buckets": out_of_range,
        "suggestions": suggestions,
    }
