"""Render questions, model answers, and grades into one readable HTML page.

Usage:
    python src/make_review.py          # writes results/review.html

Re-run any time questions, raw results, grades, or overrides change. The page
is derived output and is gitignored; the JSONL files stay the source of truth.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
RAW_DIR = ROOT / "results" / "raw"
GRADED_PATH = ROOT / "results" / "graded.jsonl"
OVERRIDES_PATH = ROOT / "results" / "overrides.jsonl"
OUT_PATH = ROOT / "results" / "review.html"

CATEGORY_LABELS = {
    "correct": "correct",
    "abstain": "abstain",
    "hedged_wrong": "hedged wrong",
    "confident_fabrication": "confident fabrication",
}

STYLE = """
:root {
  --ink: #1c1917; --paper: #faf9f7; --card: #ffffff; --line: #e4e0da;
  --muted: #78716c; --accent: #7c2d12;
  --ok: #1a7f37; --ok-bg: #e6f4ea; --bad: #b91c1c; --bad-bg: #fdeaea;
  --abstain: #1d4ed8; --abstain-bg: #e8edfb; --hedge: #b45309; --hedge-bg: #fdf3e2;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e7e5e4; --paper: #171412; --card: #201c19; --line: #38322d;
    --muted: #a8a29e; --accent: #fdba74;
    --ok: #4ade80; --ok-bg: #14261a; --bad: #f87171; --bad-bg: #2c1616;
    --abstain: #93b4f8; --abstain-bg: #16203a; --hedge: #fbbf24; --hedge-bg: #2c2210;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font: 17px/1.55 Georgia, 'Iowan Old Style', 'Times New Roman', serif; }
main { max-width: 54rem; margin: 0 auto; padding: 2rem 1.25rem 6rem; }
h1 { font-size: 2.4rem; font-weight: 400; margin: 0 0 .25rem; letter-spacing: -.02em; }
h1 + p { color: var(--muted); margin-top: 0; }
h2 { font-size: 1.05rem; text-transform: uppercase; letter-spacing: .14em;
  color: var(--accent); margin: 3rem 0 1rem; font-weight: 700; }
code, .mono { font-family: 'Cascadia Code', Consolas, monospace; font-size: .82em; }
.toc { display: grid; grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
  gap: .4rem; margin: 1.5rem 0; padding: 0; list-style: none; }
.toc a { display: flex; justify-content: space-between; gap: .5rem; padding: .35rem .6rem;
  border: 1px solid var(--line); border-radius: .4rem; text-decoration: none;
  color: var(--ink); background: var(--card); font-family: Consolas, monospace; font-size: .8rem; }
.toc a:hover { border-color: var(--accent); }
.dots { letter-spacing: .1em; }
.q { background: var(--card); border: 1px solid var(--line); border-radius: .6rem;
  padding: 1.4rem 1.6rem; margin: 1.2rem 0; }
.q-head { display: flex; flex-wrap: wrap; gap: .5rem; align-items: baseline; margin-bottom: .8rem; }
.q-head .id { font-family: Consolas, monospace; font-weight: 700; font-size: 1.05rem; }
.tag { font-family: Consolas, monospace; font-size: .72rem; padding: .1rem .5rem;
  border-radius: 1rem; border: 1px solid var(--line); color: var(--muted); }
.tag.draft { color: var(--hedge); border-color: var(--hedge); }
.tag.verified { color: var(--ok); border-color: var(--ok); }
.q-text { font-size: 1.15rem; margin: 0 0 1rem; }
.truth { border-left: 3px solid var(--ok); padding: .5rem .9rem; margin: 0 0 .6rem;
  background: var(--ok-bg); border-radius: 0 .4rem .4rem 0; }
.truth b { font-variant: small-caps; letter-spacing: .05em; }
.meta { color: var(--muted); font-size: .85rem; margin: .3rem 0 1rem; }
.verify-cmd { color: var(--muted); font-size: .8rem; margin-top: 1rem; }
.model { border-top: 1px dashed var(--line); padding-top: .8rem; margin-top: .8rem; }
.model-head { display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; }
.model-name { font-family: Consolas, monospace; font-size: .85rem; font-weight: 700; }
.grade { font-family: Consolas, monospace; font-size: .75rem; font-weight: 700;
  padding: .15rem .6rem; border-radius: 1rem; }
.grade.correct { color: var(--ok); background: var(--ok-bg); }
.grade.confident_fabrication { color: var(--bad); background: var(--bad-bg); }
.grade.abstain { color: var(--abstain); background: var(--abstain-bg); }
.grade.hedged_wrong { color: var(--hedge); background: var(--hedge-bg); }
.grade.ungraded { color: var(--muted); background: transparent; border: 1px dashed var(--line); }
.rationale { font-size: .92rem; color: var(--muted); margin: .4rem 0 0; }
details { margin-top: .5rem; }
summary { cursor: pointer; color: var(--accent); font-size: .85rem; }
.answer { white-space: pre-wrap; overflow-x: auto; background: var(--paper);
  border: 1px solid var(--line); border-radius: .4rem; padding: .8rem 1rem;
  font-family: 'Cascadia Code', Consolas, monospace; font-size: .78rem; line-height: 1.5; }
"""

DOT = {"correct": ("●", "var(--ok)"), "confident_fabrication": ("●", "var(--bad)"),
       "abstain": ("●", "var(--abstain)"), "hedged_wrong": ("●", "var(--hedge)"),
       None: ("○", "var(--muted)")}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def esc(value: object) -> str:
    return html.escape(str(value))


def main() -> None:
    questions = sorted(
        (q for f in QUESTIONS_DIR.glob("*.jsonl") for q in load_jsonl(f)),
        key=lambda q: q["id"],
    )
    grades = {(g["model_name"], g["question_id"]): g for g in load_jsonl(GRADED_PATH)}
    for o in load_jsonl(OVERRIDES_PATH):
        key = (o["model_name"], o["question_id"])
        if key in grades:
            grades[key] = {**grades[key], "category": o["category"], "review_status": "human"}
    models = sorted(d.name for d in RAW_DIR.iterdir() if d.is_dir())

    toc, sections = [], []
    for q in questions:
        qid = q["id"]
        dots = "".join(
            f'<span style="color:{DOT[c][1]}">{DOT[c][0]}</span>'
            for m in models
            for c in [grades.get((m, qid), {}).get("category")]
        )
        toc.append(f'<li><a href="#{qid}"><span>{qid}</span><span class="dots">{dots}</span></a></li>')

        status = q["verification"]["status"]
        parts = [
            f'<section class="q" id="{qid}">',
            '<div class="q-head">',
            f'<span class="id">{esc(qid)}</span>',
            f'<span class="tag">{esc(q["type"])}</span>',
            f'<span class="tag">{esc(q.get("difficulty", ""))}</span>',
            f'<span class="tag {status}">{esc(status)}</span>',
            "</div>",
            f'<p class="q-text">{esc(q["question"])}</p>',
            f'<div class="truth"><b>ground truth</b> — {esc(q["ground_truth"])}</div>',
        ]
        if q.get("acceptable_answers"):
            parts.append(f'<div class="meta">accepts: <code>{esc(" · ".join(q["acceptable_answers"]))}</code></div>')
        if q.get("premise_note"):
            parts.append(f'<div class="meta">premise note: {esc(q["premise_note"])}</div>')
        parts.append(f'<div class="meta">source: {esc(q.get("source", "—"))}</div>')

        for m in models:
            raw_path = RAW_DIR / m / f"{qid}.json"
            raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else None
            grade = grades.get((m, qid))
            cat = grade["category"] if grade else "ungraded"
            label = CATEGORY_LABELS.get(cat, cat)
            if grade and grade.get("review_status") == "human":
                label += " (human override)"
            parts.append('<div class="model"><div class="model-head">')
            parts.append(f'<span class="model-name">{esc(m)}</span>')
            parts.append(f'<span class="grade {esc(cat)}">{esc(label)}</span>')
            parts.append("</div>")
            if grade:
                parts.append(f'<p class="rationale">grader: {esc(grade["rationale"])}</p>')
            if raw is None:
                parts.append('<p class="rationale">no response collected yet</p>')
            elif "error" in raw:
                parts.append(f'<p class="rationale">collection error: {esc(raw["error"])}</p>')
            else:
                trunc = " — TRUNCATED" if raw.get("stop_reason") in ("length", "max_tokens") else ""
                parts.append(f"<details><summary>full response ({esc(raw.get('stop_reason'))}{trunc})</summary>")
                parts.append(f'<div class="answer">{esc(raw["text"])}</div></details>')
            parts.append("</div>")

        parts.append(f'<p class="verify-cmd">checks out? → <code>python src/verify.py {esc(qid)}</code></p>')
        parts.append("</section>")
        sections.append("\n".join(parts))

    graded_n = len(grades)
    verified_n = sum(q["verification"]["status"] == "verified" for q in questions)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eval review — confident-fabrication-eval</title>
<style>{STYLE}</style></head><body><main>
<h1>Eval review</h1>
<p>{len(questions)} questions ({verified_n} verified) · {len(models)} models · {graded_n} graded pairs.
Worksheet: <code>docs/verification-worksheet.md</code> · regenerate: <code>python src/make_review.py</code></p>
<ul class="toc">{"".join(toc)}</ul>
{"".join(sections)}
</main></body></html>"""
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH} — {len(questions)} questions, {len(models)} models, {graded_n} graded pairs.")


if __name__ == "__main__":
    main()
