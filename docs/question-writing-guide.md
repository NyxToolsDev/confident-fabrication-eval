# Question-Writing Guide

The value of this eval rests entirely on the ground truth being right. These rules keep it that way.

## The verification bar

A question is `verified` only when the author has checked the ground truth against the primary source named in `source` — the standard document itself, not a vendor manual, not a wiki, not a model's answer. If you can't cite chapter and section, the question stays `draft`.

## Writing good factual questions

- One well-defined answer. If reasonable practitioners could argue, cut it or tighten it.
- Name the standard version in the question text whenever the answer is version-dependent ("In HL7 v2.5.1, ...").
- Prefer questions a working integrator actually asks. The point is realism, not trivia.
- Fill `acceptable_answers` with the short forms a terse-but-correct response might use.

## Writing good false-premise traps

- The nonexistent element should be *plausible* — adjacent to real numbering (PID-60, not PID-9000), following real naming patterns (PatientContact, not FlurbResource). A trap that looks fake measures nothing.
- Confirm nonexistence across the version named in the question, and note in `premise_note` if the element exists in a *different* version (that makes it a `version_trap` instead).
- `ground_truth` describes what a correct challenge looks like, so the grader has an anchor.

## Difficulty labels

- `basic` — any junior integration analyst should know it cold.
- `intermediate` — a working interface analyst knows it or finds it in under a minute.
- `expert` — requires real production scar tissue or careful reading of the standard.

## Things that disqualify a question

- Any PHI or realistic patient data, even synthetic-looking. Use obviously structural examples only.
- Vendor-proprietary behavior (product quirks, private tags in vendor ranges as "the answer").
- Ambiguity between standard versions without naming the version.
- Editing a question after any model has answered it — retire the id, mint a new one.
