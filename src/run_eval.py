"""Query each configured model with the question bank and store raw responses.

Usage:
    python src/run_eval.py --models models.json [--include-drafts] [--force]
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
RAW_DIR = ROOT / "results" / "raw"

PROMPT_TEMPLATE = (
    "Answer the following question about healthcare interoperability standards.\n\n{question}"
)
MAX_TOKENS = 1024


def load_questions(include_drafts: bool) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for path in sorted(QUESTIONS_DIR.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            status = record.get("verification", {}).get("status")
            if status != "verified" and not include_drafts:
                continue
            questions.append(record)
    return questions


def ask_anthropic(client: anthropic.Anthropic, model: dict[str, Any], prompt: str) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": model["model_id"],
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    params.update(model.get("params", {}))
    response = client.messages.create(**params)
    text = "".join(block.text for block in response.content if block.type == "text")
    return {
        "text": text,
        "stop_reason": response.stop_reason,
        "resolved_model": response.model,
        "usage": response.usage.to_dict(),
        "request_params": {k: v for k, v in params.items() if k != "messages"},
    }


def ask_openai_compatible(model: dict[str, Any], prompt: str) -> dict[str, Any]:
    import os

    from openai import OpenAI

    api_key = os.environ.get(model.get("api_key_env", "OPENAI_API_KEY"), "not-needed")
    client = OpenAI(base_url=model.get("base_url"), api_key=api_key)
    params: dict[str, Any] = {
        "model": model["model_id"],
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    params.update(model.get("params", {}))
    response = client.chat.completions.create(**params)
    choice = response.choices[0]
    message_dump = choice.message.model_dump()
    reasoning = message_dump.get("reasoning") or message_dump.get("reasoning_content")
    return {
        "text": choice.message.content or "",
        "reasoning": reasoning,
        "stop_reason": choice.finish_reason,
        "resolved_model": response.model,
        "usage": response.usage.model_dump() if response.usage else None,
        "request_params": {k: v for k, v in params.items() if k != "messages"},
    }


def ask_ollama_native(model: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Ollama's native /api/chat — needed for `think: false`, which the
    OpenAI-compatible endpoint does not honor."""
    import urllib.request

    payload: dict[str, Any] = {
        "model": model["model_id"],
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": MAX_TOKENS},
    }
    payload.update(model.get("params", {}))
    request = urllib.request.Request(
        model.get("base_url", "http://localhost:11434").rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as resp:
        result = json.load(resp)
    message = result.get("message", {})
    return {
        "text": message.get("content") or "",
        "reasoning": message.get("thinking"),
        "stop_reason": result.get("done_reason"),
        "resolved_model": result.get("model"),
        "usage": {
            "prompt_tokens": result.get("prompt_eval_count"),
            "completion_tokens": result.get("eval_count"),
        },
        "request_params": {k: v for k, v in payload.items() if k != "messages"},
    }


def run_one(
    anthropic_client: anthropic.Anthropic,
    model: dict[str, Any],
    question: dict[str, Any],
) -> dict[str, Any]:
    prompt = PROMPT_TEMPLATE.format(question=question["question"])
    record: dict[str, Any] = {
        "question_id": question["id"],
        "model_name": model["name"],
        "provider": model["provider"],
        "verification_status": question.get("verification", {}).get("status"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if model["provider"] == "anthropic":
            record.update(ask_anthropic(anthropic_client, model, prompt))
        elif model["provider"] == "openai_compatible":
            record.update(ask_openai_compatible(model, prompt))
        elif model["provider"] == "ollama_native":
            record.update(ask_ollama_native(model, prompt))
        else:
            raise ValueError(f"unknown provider: {model['provider']}")
    except anthropic.RateLimitError as exc:
        record["error"] = f"rate_limited: {exc.message}"
    except anthropic.APIStatusError as exc:
        record["error"] = f"api_error {exc.status_code}: {exc.message}"
    except anthropic.APIConnectionError:
        record["error"] = "connection_error"
    except Exception as exc:  # openai-compatible errors and anything else
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=ROOT / "models.json")
    parser.add_argument("--include-drafts", action="store_true",
                        help="Run draft (unverified) questions too — pipeline testing only.")
    parser.add_argument("--force", action="store_true",
                        help="Re-run question/model pairs that already have a result file.")
    parser.add_argument("--only", type=str, default=None,
                        help="Run only the model with this name from models.json.")
    args = parser.parse_args()

    models = json.loads(args.models.read_text(encoding="utf-8"))
    if args.only:
        models = [m for m in models if m["name"] == args.only]
        if not models:
            parser.error(f"no model named {args.only!r} in {args.models}")
    questions = load_questions(include_drafts=args.include_drafts)
    if not questions:
        print("No questions to run. Verified questions: 0. "
              "Use --include-drafts to run the draft bank for pipeline testing.")
        return

    anthropic_client = anthropic.Anthropic()
    ran = skipped = failed = 0
    for model in models:
        out_dir = RAW_DIR / model["name"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for question in questions:
            out_path = out_dir / f"{question['id']}.json"
            if out_path.exists() and not args.force:
                skipped += 1
                continue
            record = run_one(anthropic_client, model, question)
            out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            if "error" in record:
                failed += 1
                print(f"[FAIL] {model['name']} / {question['id']}: {record['error']}")
            else:
                ran += 1
                print(f"[ok]   {model['name']} / {question['id']}")

    print(f"\nDone. {ran} responses collected, {skipped} skipped (existing), {failed} errors.")


if __name__ == "__main__":
    main()
