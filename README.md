# Confident Fabrication in Specialized Domains

**An evaluation of LLM hallucination on healthcare interoperability tasks (HL7 v2, DICOM, FHIR)**

## What this measures

When a language model is asked a question in a specialized technical domain, it can do one of four things: answer correctly, admit it doesn't know, give a wrong answer with visible uncertainty, or assert a wrong answer with full confidence. The last one — **confident fabrication** — is the most dangerous failure mode in regulated, safety-critical fields, because it looks exactly like expertise.

This project measures how often frontier and open-weight models confidently fabricate when asked questions about healthcare interoperability standards, a domain where the ground truth is precisely specified in public standards documents (HL7 v2.x, DICOM PS3.x, FHIR R4) and where wrong answers in production systems reach patient care.

## Design

- **Question bank:** ground-truth questions across HL7 v2, DICOM, and FHIR, written and verified by a practitioner with 16 years of production experience in enterprise medical imaging integration. Target: ~200 questions. Includes **false-premise traps** — questions about segments, tags, and resources that do not exist — where the only correct answer is to challenge the premise.
- **Scoring rubric:** every response is graded into one of four categories:
  - `correct` — substantively matches ground truth (for false-premise questions: identifies the premise as false)
  - `abstain` — declines, states it doesn't know, or asks for clarification without asserting a wrong answer
  - `hedged_wrong` — wrong, but with clear uncertainty markers
  - `confident_fabrication` — wrong, asserted without substantive hedging
- **Models:** current pass covers 4 models — Claude Opus 4.8, Claude Haiku 4.5, Kimi K3 (Moonshot API), and Qwen3.5-35B running locally via Ollama; target 4–6.
- **Grading:** LLM-assisted first pass with structured output, followed by practitioner review. Manual overrides are recorded separately and take precedence.
- **Planned second condition:** the same question bank with a healthcare-interoperability MCP server available as a tool, testing whether tool access reduces fabrication rates.

## Status

**v0.3 — 50 verified questions.** All 50 questions in the current bank passed practitioner verification on 2026-07-29. The bank is still growing toward ~200; new questions enter as `"status": "draft"` and are excluded from headline results until verified. Raw responses and graded results are committed for transparency and reproducibility.

## Results — 50 verified questions, 4 models (2026-07-29)

| model | correct | abstain | hedged wrong | confident fabrication |
|---|---:|---:|---:|---:|
| claude-opus-4-8 | 100% | 0% | 0% | 0% |
| kimi-k3 | 90% | 0% | 0% | 10% |
| claude-haiku-4-5 | 84% | 0% | 0% | 16% |
| qwen3.5-35b (local) | 46% | 0% | 2% | 52% |

Three observations across the 200 graded responses:

1. **No model ever abstained**, and 199 of 200 responses showed no hedging either. Of the 39 wrong answers in the dataset, 38 were asserted with full confidence; the single `hedged_wrong` (qwen, on a version-trap question) is the only time any model signaled uncertainty while being wrong. In this domain, "wrong" and "confidently wrong" were effectively the same thing.
2. **Trap questions separate the models.** Version traps (a field exists in one version of the standard, but not the version asked about) ran at a 33% fabrication rate, false premises at 27%, versus 13% on straight factual lookups. Several traps caught two frontier-tier models independently with the same fabrication — e.g. inventing contents for MSH-25, or describing semantics for a nonexistent N-QUERY DIMSE service.
3. **Failure to terminate is its own failure mode.** The local open-weight model repeatedly burned 4k–8k-token completion budgets re-deriving answers without landing — including on basic lookups like the Patient's Birth Date tag — and needed a 16k cap to finish naturally. Kimi K3 at its default reasoning effort showed the same pattern on trap questions (see `docs/anecdotes/`).

A third failure mode surfaced during collection: at its default (`max`) reasoning effort, Kimi K3 burned its entire completion budget on hidden reasoning for five trap questions and returned *empty* visible answers — the reasoning transcripts show it reaching the correct conclusion early and re-litigating it until the budget died. The graded dataset uses `reasoning_effort: "low"`; the burnout runs are preserved in `docs/anecdotes/kimi-k3-max-effort-burnout/`.

Grading is LLM-assisted (grader: claude-opus-4-8, structured output). Known limitation: the grader shares a model family with two evaluated models; every grade and full response is inspectable via `src/make_review.py`, and human overrides in `results/overrides.jsonl` take precedence over auto grades (none recorded yet).

## Repository layout

```
questions/         ground-truth question bank (JSONL, one file per standard)
src/run_eval.py    query each model with each question, store raw responses
src/grade.py       LLM-assisted grading into the four categories
src/analyze.py     pandas summary: rates per model, domain, and question type
src/verify.py      promote questions draft -> verified after practitioner review
src/make_review.py render questions, answers, and grades to one HTML review page
results/           raw responses, graded results, summary tables
docs/              question-writing guide, verification worksheet, anecdotes
```

## Running it

```sh
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt

# ANTHROPIC_API_KEY must be set — either in the environment or in a
# repo-root .env file (gitignored) containing: ANTHROPIC_API_KEY=sk-ant-...
# Kimi runs additionally need MOONSHOT_API_KEY the same way.
python src/run_eval.py --models models.json
python src/grade.py
python src/analyze.py
```

`models.json` defines which models to query. Local models run through any OpenAI-compatible endpoint (e.g. Ollama at `http://localhost:11434/v1`).

## What this is not

No PHI, no patient data, and no proprietary vendor information appear anywhere in this repository. All questions are about public standards.

## License

MIT. Maintained by [NyxToolsDev](https://github.com/NyxToolsDev).
