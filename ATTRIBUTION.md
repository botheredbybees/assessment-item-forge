# Attribution

This project is licensed under CC BY-SA 4.0 (see `LICENSE`). It is a fresh build — not a fork —
informed by two existing projects, credited here for the specific ideas adapted from each, per
CC BY-SA 4.0's attribution requirement.

## danielcregg/moodle-mcq (MIT License)

https://github.com/danielcregg/claude-code-skill-moodle-mcq

The answer-length-distribution target this project enforces in `scripts/length_distribution.py`
— aiming for roughly 15% of correct answers being the shortest option, 15% the longest, and 70%
neither, across a whole question set — is adapted from this project's own length-balancing rule.
MIT is compatible as an input to a CC BY-SA 4.0 work; this credit is given because it's the right
thing to do, not because MIT requires it.

## GarethManning/education-agent-skills (CC BY-SA 4.0)

https://github.com/GarethManning/education-agent-skills

The pedagogical reasoning structure in `references/pedagogy.md` — matching an assessment
technique to what is actually being checked, when, and under what constraints — is adapted from
the `curriculum-assessment/formative-assessment-technique-selector` skill in this library. The
construct-validity framing behind the answer-length-distribution rule (construct-irrelevant
variance) draws on the same Messick (1989) validity framework cited by this library's
`curriculum-assessment/assessment-validity-checker` skill. Both skills are themselves grounded in
Black & Wiliam (1998), Wiliam (2011), and Messick (1989) — see `references/pedagogy.md` for full
citations. This project's CC BY-SA 4.0 license is required by this source's share-alike terms.
