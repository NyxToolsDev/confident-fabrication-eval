"""Summarize graded results: category rates per model, domain, and question type.

Manual overrides in results/overrides.jsonl take precedence over auto grades.
Headline tables use verified questions only unless --include-drafts is passed.

Usage:
    python src/analyze.py [--include-drafts]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
GRADED_PATH = ROOT / "results" / "graded.jsonl"
OVERRIDES_PATH = ROOT / "results" / "overrides.jsonl"
SUMMARY_PATH = ROOT / "results" / "summary.csv"

CATEGORIES = ["correct", "abstain", "hedged_wrong", "confident_fabrication"]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def apply_overrides(df: pd.DataFrame, overrides: list[dict]) -> pd.DataFrame:
    for override in overrides:
        mask = (df["model_name"] == override["model_name"]) & (df["question_id"] == override["question_id"])
        df.loc[mask, "category"] = override["category"]
        df.loc[mask, "review_status"] = "human"
    return df


def rate_table(df: pd.DataFrame, by: str) -> pd.DataFrame:
    counts = df.groupby([by, "category"]).size().unstack(fill_value=0)
    for category in CATEGORIES:
        if category not in counts.columns:
            counts[category] = 0
    counts = counts[CATEGORIES]
    rates = counts.div(counts.sum(axis=1), axis=0).round(3)
    rates["n"] = counts.sum(axis=1)
    return rates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-drafts", action="store_true")
    args = parser.parse_args()

    records = load_jsonl(GRADED_PATH)
    if not records:
        print("No graded results found. Run grade.py first.")
        return

    df = pd.DataFrame(records)
    df = apply_overrides(df, load_jsonl(OVERRIDES_PATH))

    if not args.include_drafts:
        df = df[df["verification_status"] == "verified"]
        if df.empty:
            print("No verified questions in the graded set yet. "
                  "Headline results require practitioner-verified ground truth; "
                  "use --include-drafts to preview pipeline output.")
            return

    print("\n=== Category rates by model ===")
    by_model = rate_table(df, "model_name")
    print(by_model.to_markdown())

    print("\n=== Category rates by question type ===")
    print(rate_table(df, "type").to_markdown())

    print("\n=== Confident fabrication rate on false-premise questions, by model ===")
    traps = df[df["type"] == "false_premise"]
    if traps.empty:
        print("(no false-premise questions in this set)")
    else:
        print(rate_table(traps, "model_name")[["confident_fabrication", "n"]].to_markdown())

    reviewed = (df["review_status"] == "human").mean()
    print(f"\nHuman-reviewed grades: {reviewed:.0%} of {len(df)} results.")

    by_model.to_csv(SUMMARY_PATH)
    print(f"Summary written to {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
