#!/usr/bin/env python3
"""Validate and optionally live-verify external GPT-5.6 review evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROVIDER = "openai_responses_api"
REQUESTED_MODEL = "gpt-5.6"
REASONING_EFFORT = "high"
FORBIDDEN_PROVIDERS = {
    "codex",
    "codex_subagent",
    "codex-subagent",
    "self",
    "local_model",
    "chatgpt_workspace_agent_trigger",
}
API_BASE = "https://api.openai.com/v1/responses"


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors


def load_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                chunks.append(content["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ValueError("retrieved response contains no output_text")
    return text


def retrieve_response(response_id: str, api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{API_BASE}/{response_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI retrieve response returned HTTP {exc.code}: {detail}") from exc
    if not isinstance(body, dict):
        raise ValueError("retrieved response root is not an object")
    return body


def validate_evidence(
    evidence: Any,
    *,
    expected_role: str,
    path: str,
    live: bool,
    api_key: str | None,
    result: Result,
) -> str | None:
    if not isinstance(evidence, dict):
        result.errors.append(f"{path}: reviewer evidence must be an object")
        return None
    provider = str(evidence.get("provider") or "")
    if provider.lower() in FORBIDDEN_PROVIDERS:
        result.errors.append(f"{path}.provider: Codex/self-review provider {provider!r} is forbidden")
    if provider != PROVIDER:
        result.errors.append(f"{path}.provider: expected {PROVIDER!r}, found {provider!r}")
    if evidence.get("role") != expected_role:
        result.errors.append(f"{path}.role: expected {expected_role!r}")
    if evidence.get("requested_model") != REQUESTED_MODEL:
        result.errors.append(f"{path}.requested_model: must be {REQUESTED_MODEL!r}")
    resolved = str(evidence.get("resolved_model") or "")
    if not resolved.startswith("gpt-5.6-sol"):
        result.errors.append(f"{path}.resolved_model: expected GPT-5.6 Sol, found {resolved!r}")
    if evidence.get("reasoning_effort") != REASONING_EFFORT:
        result.errors.append(f"{path}.reasoning_effort: must be {REASONING_EFFORT!r}")
    if evidence.get("self_review") is not False:
        result.errors.append(f"{path}.self_review: must be false")
    response_id = evidence.get("response_id")
    if not isinstance(response_id, str) or not response_id.startswith("resp_"):
        result.errors.append(f"{path}.response_id: missing valid Responses API id")
        return None
    for key in ("input_sha256", "output_sha256"):
        value = evidence.get(key)
        if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
            result.errors.append(f"{path}.{key}: missing SHA-256 evidence")
    for key in ("prompt", "executor", "started_at", "completed_at"):
        if not evidence.get(key):
            result.errors.append(f"{path}.{key}: required")

    if live:
        if not api_key:
            result.errors.append("live verification requested but OPENAI_API_KEY is unavailable")
        else:
            try:
                remote = retrieve_response(response_id, api_key)
                if remote.get("id") != response_id:
                    result.errors.append(f"{path}.response_id: retrieved id mismatch")
                remote_model = str(remote.get("model") or "")
                if not remote_model.startswith("gpt-5.6-sol"):
                    result.errors.append(
                        f"{path}.resolved_model: retrieved response used {remote_model!r}"
                    )
                if remote_model != resolved:
                    result.errors.append(
                        f"{path}.resolved_model: receipt {resolved!r} differs from retrieved {remote_model!r}"
                    )
                if remote.get("status") not in {None, "completed"}:
                    result.errors.append(f"{path}.response_id: response status is {remote.get('status')!r}")
                remote_text = output_text(remote)
                remote_hash = "sha256:" + hashlib.sha256(remote_text.encode("utf-8")).hexdigest()
                if remote_hash != evidence.get("output_sha256"):
                    result.errors.append(f"{path}.output_sha256: does not match retrieved response")
            except Exception as exc:
                result.errors.append(f"{path}.response_id: live verification failed: {exc}")
    return response_id


def validate_package(path: Path, live: bool, api_key: str | None, result: Result) -> str | None:
    package = load_mapping(path)
    package_evidence = (package.get("review") or {}).get("reviewer")
    response_id = validate_evidence(
        package_evidence,
        expected_role="semantic_reviewer",
        path=f"{path}:review.reviewer",
        live=live,
        api_key=api_key,
        result=result,
    )
    receipt_path = path.parent / "external-review-receipt.yaml"
    if not receipt_path.exists():
        result.errors.append(f"{path}: missing external-review-receipt.yaml")
        return response_id
    receipt = load_mapping(receipt_path)
    receipt_evidence = receipt.get("reviewer")
    receipt_id = validate_evidence(
        receipt_evidence,
        expected_role="semantic_reviewer",
        path=f"{receipt_path}:reviewer",
        live=False,
        api_key=None,
        result=result,
    )
    if response_id and receipt_id and response_id != receipt_id:
        result.errors.append(f"{path}: package and receipt response ids differ")
    if package_evidence != receipt_evidence:
        result.errors.append(f"{path}: package and receipt reviewer evidence differ")
    return response_id


def validate_audit(path: Path, live: bool, api_key: str | None, result: Result) -> tuple[str | None, str | None]:
    audit = load_mapping(path)
    review = audit.get("review_package") or {}
    semantic_id = validate_evidence(
        review.get("reviewer"),
        expected_role="semantic_reviewer",
        path=f"{path}:review_package.reviewer",
        live=live,
        api_key=api_key,
        result=result,
    )
    logic_id = validate_evidence(
        (audit.get("logic_validation") or {}).get("reviewer"),
        expected_role="logic_validator",
        path=f"{path}:logic_validation.reviewer",
        live=live,
        api_key=api_key,
        result=result,
    )
    if semantic_id and logic_id and semantic_id == logic_id:
        result.errors.append(f"{path}: semantic and logic reviews must use distinct response ids")
    for finding in review.get("findings", []) or []:
        if isinstance(finding, dict) and finding.get("code") == "REVIEW_PACKAGE_NOT_PRODUCED":
            result.errors.append(
                f"{path}: REVIEW_PACKAGE_NOT_PRODUCED is incomplete work, not a terminal blocker"
            )
    return semantic_id, logic_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path)
    parser.add_argument("--audit-record", type=Path)
    parser.add_argument("--topic-manifest", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--verify-live", action="store_true")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not any((args.package, args.audit_record, args.topic_manifest)):
        print("ERROR: provide --package, --audit-record, or --topic-manifest", file=sys.stderr)
        return 2
    api_key = os.environ.get(args.api_key_env)
    result = Result()
    try:
        if args.package:
            validate_package(args.package, args.verify_live, api_key, result)
        if args.audit_record:
            validate_audit(args.audit_record, args.verify_live, api_key, result)
        if args.topic_manifest:
            manifest = load_mapping(args.topic_manifest)
            repo_root = args.repo_root.resolve() if args.repo_root else None
            if repo_root is None:
                result.errors.append("--repo-root is required with --topic-manifest")
            else:
                for index, entry in enumerate(manifest.get("artifacts", []) or [], start=1):
                    if not isinstance(entry, dict) or entry.get("status") == "queued":
                        continue
                    audit_rel = Path(str(entry.get("audit_validation_file") or ""))
                    audit_path = repo_root / audit_rel
                    if not audit_path.exists():
                        result.errors.append(f"artifacts[{index}]: missing audit record {audit_path}")
                        continue
                    semantic_id, _ = validate_audit(audit_path, args.verify_live, api_key, result)
                    package_path = repo_root / Path(str(entry.get("review_directory") or "")) / "package.yaml"
                    if not package_path.exists():
                        result.errors.append(f"artifacts[{index}]: missing package {package_path}")
                    else:
                        package_id = validate_package(package_path, args.verify_live, api_key, result)
                        if semantic_id and package_id and semantic_id != package_id:
                            result.errors.append(
                                f"artifacts[{index}]: audit and package semantic response ids differ"
                            )
    except Exception as exc:
        result.errors.append(str(exc))

    payload = {"clean": result.clean, "errors": result.errors, "warnings": result.warnings}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("# External GPT Reviewer Evidence")
        print(f"Result: {'PASS' if result.clean else 'FAIL'}")
        print("\n## Errors")
        print("\n".join(f"- {item}" for item in result.errors) or "_None._")
        print("\n## Warnings")
        print("\n".join(f"- {item}" for item in result.warnings) or "_None._")
    return 0 if result.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
