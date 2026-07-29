"""Promote questions from draft to verified after practitioner review.

Usage:
    python src/verify.py hl7-001 dicom-002 [...]
    python src/verify.py --revert hl7-001    # demote back to draft

This only flips the verification stamp. The actual check against the primary
source happens before you run this — see docs/verification-worksheet.md.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="+", help="Question ids to promote, e.g. hl7-001.")
    parser.add_argument("--revert", action="store_true",
                        help="Demote the given ids back to draft instead.")
    args = parser.parse_args()

    wanted = set(args.ids)
    changed: list[str] = []
    for path in sorted(QUESTIONS_DIR.glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        dirty = False
        for line in lines:
            if line.strip():
                record = json.loads(line)
                if record["id"] in wanted:
                    if args.revert:
                        record["verification"] = {"status": "draft", "verified_by": None, "date": None}
                    else:
                        record["verification"] = {
                            "status": "verified",
                            "verified_by": "practitioner",
                            "date": date.today().isoformat(),
                        }
                    line = json.dumps(record, ensure_ascii=False)
                    changed.append(record["id"])
                    dirty = True
            out_lines.append(line)
        if dirty:
            path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    missing = wanted - set(changed)
    if missing:
        raise SystemExit(f"unknown question ids: {', '.join(sorted(missing))}")
    verb = "reverted to draft" if args.revert else "verified"
    print(f"{len(changed)} question(s) {verb}: {', '.join(sorted(changed))}")


if __name__ == "__main__":
    main()
