# kimi-k3 at default reasoning effort: trap-question burnout

These five raw results are from the first kimi-k3 collection run (2026-07-29),
before `reasoning_effort` was pinned. At the model's default (`"max"`), all five
burned the entire 4096-token completion budget on hidden reasoning and returned
an **empty visible answer** (`"text": ""`, `stop_reason: "length"`).

All five are trap questions (false_premise or version_trap). The reasoning
transcripts show the model repeatedly reaching the correct conclusion and then
re-litigating it — see `hl7-002.json`, where it correctly determines PID-60
does not exist within the first few hundred tokens, then spends the rest of the
budget re-deriving the PID field table from memory of the HAPI Java source.

The graded dataset uses a uniform `reasoning_effort: "low"` re-collection for
all 30 questions (see `models.json`). These files are kept out of
`results/raw/` so they never enter grading; they are writeup evidence only.
