#!/usr/bin/env python3
"""Invoke an external GPT-5.6 reviewer through the OpenAI Responses API.

This program is the only governed transport for semantic and logic reviews in the
reversible topic-audit workflow. It deliberately runs outside the Codex reasoning
thread and records response evidence that can be live-verified later.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

API_URL = "https://api.openai.com/v1/responses"
REQUESTED_MODEL = "gpt-5.6"
REASONING_EFFORT = "high"
PROVIDER = "openai_responses_api"
EXECUTOR = "tools/governance/invoke_external_gpt_reviewer.py"

SEMANTIC_FILE_KEYS = {
    "artifact_yaml": "artifact.yaml",
    "corrected_tex": "corrected.tex",
    "source_patch": "source.patch",
    "validation_yaml": "validation.yaml",
    "source_map_yaml": "source-map.yaml",
    "registry_needs_yaml": "registry-needs.yaml",
    "formalization_links_yaml": "formalization-links.yaml",
    "proof_vault_links_yaml": "proof-vault-links.yaml",
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def extract_output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ValueError("Responses API result contained no output_text")
    return text


def post_response(payload: dict[str, Any], api_key: str) -> tuple[dict[str, Any], str | None]:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            body = json.loads(response.read().decode("utf-8"))
            request_id = response.headers.get("x-request-id")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API returned HTTP {exc.code}: {detail}") from exc
    if not isinstance(body, dict):
        raise ValueError("OpenAI response root was not an object")
    return body, request_id


def semantic_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["result", "blocking_issues", *SEMANTIC_FILE_KEYS],
        "properties": {
            "result": {"enum": ["reviewed", "blocked"]},
            "blocking_issues": {"type": "array", "items": {"type": "string"}},
            **{
                key: {"type": "string", "minLength": 1}
                for key in SEMANTIC_FILE_KEYS
            },
        },
    }


def logic_schema() -> dict[str, Any]:
    check_names = [
        "binder_scope",
        "language_level",
        "assumptions_and_conclusion",
        "statement_shape",
        "quantifier_order",
        "witness_dependencies",
        "negation",
        "normalization_assumptions",
        "contrapositive",
        "applicability_failure",
        "order_strength",
        "predicate_signatures",
        "failure_modes",
        "yaml_tex_equivalence",
    ]
    check = {
        "type": "object",
        "additionalProperties": False,
        "required": ["result", "notes"],
        "properties": {
            "result": {"enum": ["pass", "warning", "fail", "not_applicable", "blocked"]},
            "notes": {"type": ["string", "null"]},
        },
    }
    finding = {
        "type": "object",
        "additionalProperties": False,
        "required": ["code", "severity", "message", "field"],
        "properties": {
            "code": {"type": "string", "pattern": "^[A-Z0-9_]+$"},
            "severity": {"enum": ["info", "warning", "error", "blocking"]},
            "message": {"type": "string", "minLength": 1},
            "field": {"type": ["string", "null"]},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["result", "checks", "findings"],
        "properties": {
            "result": {"enum": ["pass", "pass_with_warnings", "fail", "blocked"]},
            "checks": {
                "type": "object",
                "additionalProperties": False,
                "required": check_names,
                "properties": {name: check for name in check_names},
            },
            "findings": {"type": "array", "items": finding},
        },
    }


def evidence(
    *,
    role: str,
    response: dict[str, Any],
    request_id: str | None,
    prompt_path: Path,
    input_text: str,
    output_text: str,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    response_id = response.get("id")
    resolved_model = response.get("model")
    if not isinstance(response_id, str) or not response_id.startswith("resp_"):
        raise ValueError(f"unexpected Responses API id: {response_id!r}")
    if not isinstance(resolved_model, str) or not resolved_model.startswith("gpt-5.6-sol"):
        raise ValueError(
            f"requested {REQUESTED_MODEL}, but API resolved unexpected model {resolved_model!r}"
        )
    return {
        "provider": PROVIDER,
        "role": role,
        "requested_model": REQUESTED_MODEL,
        "resolved_model": resolved_model,
        "reasoning_effort": REASONING_EFFORT,
        "response_id": response_id,
        "request_id": request_id,
        "prompt": prompt_path.as_posix(),
        "executor": EXECUTOR,
        "input_sha256": sha256_text(input_text),
        "output_sha256": sha256_text(output_text),
        "started_at": started_at,
        "completed_at": completed_at,
        "self_review": False,
    }


def request_payload(prompt_text: str, packet: dict[str, Any], role: str) -> tuple[dict[str, Any], str]:
    input_text = (
        f"ROLE: {role}\n\n"
        "Follow the governed prompt below. Return only the requested JSON object.\n\n"
        f"GOVERNED PROMPT:\n{prompt_text}\n\n"
        "INPUT PACKET:\n"
        + json.dumps(packet, indent=2, ensure_ascii=False)
    )
    schema = semantic_schema() if role == "semantic_reviewer" else logic_schema()
    payload = {
        "model": REQUESTED_MODEL,
        "reasoning": {"effort": REASONING_EFFORT},
        "store": True,
        "input": input_text,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "lra_semantic_review" if role == "semantic_reviewer" else "lra_logic_review",
                "strict": True,
                "schema": schema,
            }
        },
    }
    return payload, input_text


def write_receipt(path: Path, reviewer: dict[str, Any], result: str, blockers: list[str]) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "lra.external-review-receipt/1.0",
                "reviewer": reviewer,
                "result": result,
                "blocking_issues": blockers,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def run_semantic(args: argparse.Namespace, packet: dict[str, Any], api_key: str) -> int:
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = load_prompt(args.prompt)
    payload, input_text = request_payload(prompt, packet, "semantic_reviewer")
    started_at = now_utc()
    response, request_id = post_response(payload, api_key)
    completed_at = now_utc()
    output_text = extract_output_text(response)
    result = json.loads(output_text)
    if not isinstance(result, dict):
        raise ValueError("semantic reviewer output was not an object")
    reviewer = evidence(
        role="semantic_reviewer",
        response=response,
        request_id=request_id,
        prompt_path=args.prompt,
        input_text=input_text,
        output_text=output_text,
        started_at=started_at,
        completed_at=completed_at,
    )
    blockers = [str(item) for item in result.get("blocking_issues", [])]
    review_result = str(result.get("result") or "")
    if review_result not in {"reviewed", "blocked"}:
        raise ValueError(f"unexpected semantic result: {review_result!r}")
    if review_result == "blocked" and not blockers:
        raise ValueError("blocked semantic review must identify at least one blocking issue")
    write_receipt(output_dir / "external-review-receipt.yaml", reviewer, review_result, blockers)

    for key, filename in SEMANTIC_FILE_KEYS.items():
        content = result.get(key)
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"semantic reviewer omitted {key}")
        (output_dir / filename).write_text(content.rstrip() + "\n", encoding="utf-8")

    source = packet.get("source") or {}
    governance = packet.get("governance") or {}
    artifact = yaml.safe_load((output_dir / "artifact.yaml").read_text(encoding="utf-8")) or {}
    label = str((artifact.get("identity") or {}).get("label") or source.get("label") or "")
    files = {
        "artifact": "artifact.yaml",
        "corrected_tex": "corrected.tex",
        "source_patch": "source.patch",
        "validation": "validation.yaml",
        "source_map": "source-map.yaml",
        "registry_needs": "registry-needs.yaml",
        "formalization_links": "formalization-links.yaml",
        "proof_vault_links": "proof-vault-links.yaml",
    }
    package = {
        "schema_version": "lra.semantic-artifact-package/1.0",
        "artifact_label": label,
        "created_at": completed_at,
        "source": {
            "repository": source.get("repository"),
            "commit": source.get("commit"),
            "file": source.get("file"),
            "source_hash": source.get("source_hash"),
        },
        "governance": {
            "repository": "wsollers/lra-governance",
            "commit": governance.get("commit"),
            "artifact_schema": "constitution/schema/semantic-artifact.schema.json",
            "package_schema": "constitution/schema/semantic-artifact-package.schema.json",
        },
        "review": {
            "status": "reviewed" if review_result == "reviewed" else "rejected",
            "reviewer": reviewer,
            "notes": None if review_result == "reviewed" else "; ".join(blockers),
        },
        "files": {
            key: {"path": filename, "sha256": file_sha256(output_dir / filename)}
            for key, filename in files.items()
        },
    }
    (output_dir / "package.yaml").write_text(
        yaml.safe_dump(package, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    if review_result == "blocked":
        print(f"external semantic review blocked: {reviewer['response_id']}")
        return 3
    print(f"external semantic review completed: {reviewer['response_id']}")
    return 0


def run_logic(args: argparse.Namespace, packet: dict[str, Any], api_key: str) -> int:
    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = load_prompt(args.prompt)
    payload, input_text = request_payload(prompt, packet, "logic_validator")
    started_at = now_utc()
    response, request_id = post_response(payload, api_key)
    completed_at = now_utc()
    output_text = extract_output_text(response)
    result = json.loads(output_text)
    if not isinstance(result, dict):
        raise ValueError("logic reviewer output was not an object")
    reviewer = evidence(
        role="logic_validator",
        response=response,
        request_id=request_id,
        prompt_path=args.prompt,
        input_text=input_text,
        output_text=output_text,
        started_at=started_at,
        completed_at=completed_at,
    )
    record = {
        "result": result.get("result"),
        "reviewer": reviewer,
        "checks": result.get("checks"),
        "findings": result.get("findings"),
    }
    output_path.write_text(
        yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    print(f"external logic validation completed: {reviewer['response_id']}")
    return 0 if result.get("result") in {"pass", "pass_with_warnings"} else 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("semantic", "logic"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(
            f"ERROR: {args.api_key_env} is not set; external GPT-5.6 review cannot run",
            file=sys.stderr,
        )
        return 2
    try:
        packet = load_json(args.input)
        return run_semantic(args, packet, api_key) if args.role == "semantic" else run_logic(args, packet, api_key)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
