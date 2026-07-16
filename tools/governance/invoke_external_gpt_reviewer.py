#!/usr/bin/env python3
"""Invoke an external GPT-5.6 reviewer through the OpenAI Responses API.

The executor owns four invariants that must not be delegated to Codex:

1. build and embed the canonical governance authority bundle;
2. run stored Responses API requests in background mode and poll to completion;
3. validate semantic packages before publishing them;
4. route validator failures to a new external repair response rather than repairing
   reviewer output locally.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

API_URL = "https://api.openai.com/v1/responses"
REQUESTED_MODEL = "gpt-5.6"
REASONING_EFFORT = "high"
PROVIDER = "openai_responses_api"
EXECUTOR = "tools/governance/invoke_external_gpt_reviewer.py"
IN_PROGRESS_STATUSES = {"queued", "in_progress"}
SUCCESS_STATUS = "completed"

# These files are loaded by the executor itself. The calling Codex thread cannot
# omit, summarize, or replace them.
AUTHORITY_PATHS = (
    "constitution/schema/semantic-artifact.schema.json",
    "constitution/schema/semantic-artifact-package.schema.json",
    "constitution/schema/semantic-artifact-support.schema.json",
    "constitution/schema/external-review-receipt.schema.json",
    "constitution/schema/artifact-audit-validation.schema.json",
    "constitution/schema/topic-semantic-audit.schema.json",
    "constitution/schema/lean-crosswalk.schema.json",
    "constitution/schema/artifact-matrix.yaml",
    "constitution/schema/block-registry.yaml",
    "constitution/schema/examples/semantic-artifact.example.yaml",
    "predicates.yaml",
    "semantic-aliases.yaml",
    "lean-crosswalk.yaml",
    "structures.yaml",
    "notation.yaml",
    "relations.yaml",
    "docs/architecture/semantic-artifact-record.md",
    "docs/workflows/semantic-artifact-calibration.md",
)

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

PUBLISHED_FILES = (
    "package.yaml",
    "external-review-receipt.yaml",
    *SEMANTIC_FILE_KEYS.values(),
)


@dataclass(frozen=True)
class ValidationRun:
    returncode: int
    stdout: str
    stderr: str
    commands: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class AuthorityBundle:
    files: tuple[dict[str, str], ...]
    sha256: str

    def as_json(self) -> dict[str, Any]:
        return {
            "schema_version": "lra.governance-authority-bundle/1.0",
            "sha256": self.sha256,
            "files": list(self.files),
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


def build_authority_bundle(governance_root: Path) -> AuthorityBundle:
    files: list[dict[str, str]] = []
    for relative in AUTHORITY_PATHS:
        path = governance_root / relative
        if not path.exists():
            raise FileNotFoundError(f"required governance authority file is missing: {path}")
        content = path.read_text(encoding="utf-8")
        files.append(
            {
                "path": relative,
                "sha256": sha256_text(content),
                "content": content,
            }
        )
    canonical = json.dumps(files, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return AuthorityBundle(tuple(files), sha256_text(canonical))


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


def request_json(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 60.0,
) -> tuple[dict[str, Any], str | None]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            request_id = response.headers.get("x-request-id")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI Responses API transport failed: {exc}") from exc
    if not isinstance(body, dict):
        raise ValueError("OpenAI response root was not an object")
    return body, request_id


def submit_background_response(
    payload: dict[str, Any],
    api_key: str,
    *,
    poll_interval: float,
    poll_timeout: float,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> tuple[dict[str, Any], str | None]:
    request_payload = dict(payload)
    request_payload["background"] = True
    response, request_id = request_json("POST", API_URL, api_key, request_payload)
    response_id = response.get("id")
    if not isinstance(response_id, str) or not response_id.startswith("resp_"):
        raise ValueError(f"background response did not return a valid id: {response_id!r}")

    deadline = monotonic() + poll_timeout
    while response.get("status") in IN_PROGRESS_STATUSES:
        if monotonic() >= deadline:
            raise TimeoutError(
                f"background response {response_id} did not complete within {poll_timeout:g} seconds"
            )
        sleep(max(0.0, poll_interval))
        response, _ = request_json("GET", f"{API_URL}/{response_id}", api_key)

    status = response.get("status")
    if status != SUCCESS_STATUS:
        error = response.get("error") or response.get("incomplete_details") or "no details"
        raise RuntimeError(f"background response {response_id} ended with status {status!r}: {error}")
    return response, request_id


def semantic_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["result", "blocking_issues", *SEMANTIC_FILE_KEYS],
        "properties": {
            "result": {"enum": ["reviewed", "blocked"]},
            "blocking_issues": {"type": "array", "items": {"type": "string"}},
            **{key: {"type": "string", "minLength": 1} for key in SEMANTIC_FILE_KEYS},
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


def request_payload(
    prompt_text: str,
    packet: dict[str, Any],
    role: str,
    authority: AuthorityBundle,
    repair_context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    sections = [
        f"ROLE: {role}",
        "Follow the governed prompt and canonical authority files below. Return only the requested JSON object.",
        "The authority bundle is complete and controlling. Do not invent illustrative schema shapes or registry entries.",
        f"GOVERNED PROMPT:\n{prompt_text}",
        "CANONICAL GOVERNANCE AUTHORITY BUNDLE:\n"
        + json.dumps(authority.as_json(), indent=2, ensure_ascii=False),
        "INPUT PACKET:\n" + json.dumps(packet, indent=2, ensure_ascii=False),
    ]
    if repair_context is not None:
        sections.append(
            "EXTERNAL REPAIR REQUEST:\n"
            "A prior external response failed deterministic validation. Produce a complete replacement package; do not omit any required file.\n"
            + json.dumps(repair_context, indent=2, ensure_ascii=False)
        )
    input_text = "\n\n".join(sections)
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


def stage_semantic_attempt(
    attempt_dir: Path,
    result: dict[str, Any],
    reviewer: dict[str, Any],
    packet: dict[str, Any],
    completed_at: str,
) -> str:
    attempt_dir.mkdir(parents=True, exist_ok=True)
    blockers = [str(item) for item in result.get("blocking_issues", [])]
    review_result = str(result.get("result") or "")
    if review_result not in {"reviewed", "blocked"}:
        raise ValueError(f"unexpected semantic result: {review_result!r}")
    if review_result == "blocked" and not blockers:
        raise ValueError("blocked semantic review must identify at least one blocking issue")

    write_receipt(attempt_dir / "external-review-receipt.yaml", reviewer, review_result, blockers)
    for key, filename in SEMANTIC_FILE_KEYS.items():
        content = result.get(key)
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"semantic reviewer omitted {key}")
        (attempt_dir / filename).write_text(content.rstrip() + "\n", encoding="utf-8")

    source = packet.get("source") or {}
    governance = packet.get("governance") or {}
    artifact = yaml.safe_load((attempt_dir / "artifact.yaml").read_text(encoding="utf-8")) or {}
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
            key: {"path": filename, "sha256": file_sha256(attempt_dir / filename)}
            for key, filename in files.items()
        },
    }
    (attempt_dir / "package.yaml").write_text(
        yaml.safe_dump(package, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return review_result


def run_semantic_validation(
    attempt_dir: Path,
    governance_root: Path,
    repos_root: Path | None,
) -> ValidationRun:
    commands: list[str] = []
    semantic_cmd = [
        sys.executable,
        str(governance_root / "tools/governance/validate_semantic_artifact.py"),
        "--artifact",
        str(attempt_dir / "artifact.yaml"),
        "--package-dir",
        str(attempt_dir),
        "--governance-root",
        str(governance_root),
        "--strict",
    ]
    if repos_root is not None:
        semantic_cmd.extend(["--repos-root", str(repos_root)])
    commands.append(subprocess.list2cmdline(semantic_cmd))
    first = subprocess.run(semantic_cmd, capture_output=True, text=True)
    stdout = first.stdout
    stderr = first.stderr
    if first.returncode != 0:
        return ValidationRun(first.returncode, stdout, stderr, tuple(commands))

    evidence_cmd = [
        sys.executable,
        str(governance_root / "tools/governance/validate_external_reviewer_evidence.py"),
        "--package",
        str(attempt_dir / "package.yaml"),
    ]
    commands.append(subprocess.list2cmdline(evidence_cmd))
    second = subprocess.run(evidence_cmd, capture_output=True, text=True)
    return ValidationRun(
        second.returncode,
        stdout + second.stdout,
        stderr + second.stderr,
        tuple(commands),
    )


def write_attempt_diagnostics(
    diagnostics_dir: Path,
    attempt: int,
    *,
    response: dict[str, Any] | None,
    output_text: str | None,
    validation: ValidationRun | None,
    error: str | None,
) -> None:
    folder = diagnostics_dir / f"attempt-{attempt:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    if response is not None:
        (folder / "response.json").write_text(
            json.dumps(response, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if output_text is not None:
        (folder / "output.txt").write_text(output_text + "\n", encoding="utf-8")
    if validation is not None:
        (folder / "validator.json").write_text(
            json.dumps(
                {
                    "returncode": validation.returncode,
                    "commands": list(validation.commands),
                    "stdout": validation.stdout,
                    "stderr": validation.stderr,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if error is not None:
        (folder / "error.txt").write_text(error + "\n", encoding="utf-8")


def publish_attempt(attempt_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in PUBLISHED_FILES:
        target = output_dir / filename
        if target.exists():
            target.unlink()
        shutil.copy2(attempt_dir / filename, target)


def run_semantic(args: argparse.Namespace, packet: dict[str, Any], api_key: str) -> int:
    output_dir: Path = args.output
    diagnostics_dir: Path = args.diagnostics_dir or (
        output_dir.parent / ".external-review-diagnostics" / output_dir.name
    )
    authority = build_authority_bundle(args.governance_root)
    prompt = load_prompt(args.prompt)
    repair_context: dict[str, Any] | None = None
    total_attempts = args.max_repair_attempts + 1

    for attempt in range(1, total_attempts + 1):
        payload, input_text = request_payload(
            prompt,
            packet,
            "semantic_reviewer",
            authority,
            repair_context,
        )
        started_at = now_utc()
        response: dict[str, Any] | None = None
        output_text: str | None = None
        validation: ValidationRun | None = None
        try:
            response, request_id = submit_background_response(
                payload,
                api_key,
                poll_interval=args.poll_interval,
                poll_timeout=args.poll_timeout,
            )
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
            with tempfile.TemporaryDirectory(prefix=f"lra-review-attempt-{attempt}-") as temp:
                attempt_dir = Path(temp)
                review_result = stage_semantic_attempt(
                    attempt_dir,
                    result,
                    reviewer,
                    packet,
                    completed_at,
                )
                if review_result == "blocked":
                    publish_attempt(attempt_dir, output_dir)
                    write_attempt_diagnostics(
                        diagnostics_dir,
                        attempt,
                        response=response,
                        output_text=output_text,
                        validation=None,
                        error=None,
                    )
                    print(f"external semantic review blocked: {reviewer['response_id']}")
                    return 3

                validation = run_semantic_validation(
                    attempt_dir,
                    args.governance_root,
                    args.repos_root,
                )
                write_attempt_diagnostics(
                    diagnostics_dir,
                    attempt,
                    response=response,
                    output_text=output_text,
                    validation=validation,
                    error=None,
                )
                if validation.clean:
                    publish_attempt(attempt_dir, output_dir)
                    print(f"external semantic review completed: {reviewer['response_id']}")
                    return 0

            repair_context = {
                "attempt": attempt,
                "prior_response_id": response.get("id"),
                "prior_reviewer_output": result,
                "validator": {
                    "returncode": validation.returncode if validation else None,
                    "commands": list(validation.commands) if validation else [],
                    "stdout": validation.stdout if validation else "",
                    "stderr": validation.stderr if validation else "",
                },
                "required_action": (
                    "Return a complete replacement package conforming exactly to the embedded canonical schemas and registries. "
                    "Correct every validator finding. Do not omit any required file string."
                ),
            }
        except Exception as exc:
            message = str(exc)
            write_attempt_diagnostics(
                diagnostics_dir,
                attempt,
                response=response,
                output_text=output_text,
                validation=validation,
                error=message,
            )
            repair_context = {
                "attempt": attempt,
                "prior_response_id": response.get("id") if response else None,
                "prior_output_text": output_text,
                "transport_or_shape_error": message,
                "required_action": (
                    "Produce a fresh, complete semantic package using the embedded authority bundle. "
                    "Return every required file string."
                ),
            }

        if attempt < total_attempts:
            print(f"external semantic attempt {attempt} failed validation; requesting external repair")

    raise RuntimeError(
        f"external semantic review failed after {total_attempts} attempts; diagnostics: {diagnostics_dir}"
    )


def run_logic(args: argparse.Namespace, packet: dict[str, Any], api_key: str) -> int:
    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    authority = build_authority_bundle(args.governance_root)
    prompt = load_prompt(args.prompt)
    payload, input_text = request_payload(
        prompt,
        packet,
        "logic_validator",
        authority,
    )
    started_at = now_utc()
    response, request_id = submit_background_response(
        payload,
        api_key,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
    )
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


def run_local_logic(args: argparse.Namespace, packet: dict[str, Any]) -> int:
    artifact_path = args.artifact or Path(
        str((packet.get("semantic_review") or {}).get("artifact_path") or "")
    )
    corrected_path = args.corrected_tex or Path(
        str((packet.get("semantic_review") or {}).get("corrected_tex_path") or "")
    )
    if not artifact_path or str(artifact_path) == ".":
        raise ValueError("local logic validation requires --artifact")
    if not corrected_path or str(corrected_path) == ".":
        raise ValueError("local logic validation requires --corrected-tex")

    output_path: Path = args.output
    cmd = [
        sys.executable,
        str(args.governance_root / "tools/governance/validate_semantic_logic.py"),
        "--artifact",
        str(artifact_path),
        "--corrected-tex",
        str(corrected_path),
        "--output",
        str(output_path),
    ]
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.stdout:
        print(run.stdout, end="")
    if run.stderr:
        print(run.stderr, end="", file=sys.stderr)
    return run.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("semantic", "logic"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument(
        "--logic-reviewer",
        choices=("local", "external"),
        default="local",
        help="Logic validation defaults to the local Python verifier; use external to call OpenAI.",
    )
    parser.add_argument("--use-openai", action="store_true", help="Alias for --logic-reviewer external.")
    parser.add_argument("--artifact", type=Path, help="Artifact YAML for local logic validation.")
    parser.add_argument("--corrected-tex", type=Path, help="Corrected TeX for local logic validation.")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument(
        "--governance-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--diagnostics-dir", type=Path)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--poll-timeout", type=float, default=1800.0)
    parser.add_argument("--max-repair-attempts", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_repair_attempts < 0:
        print("ERROR: --max-repair-attempts must be nonnegative", file=sys.stderr)
        return 2
    if args.use_openai:
        args.logic_reviewer = "external"
    if args.role == "semantic" and not args.prompt:
        print("ERROR: semantic review requires --prompt", file=sys.stderr)
        return 2
    if args.role == "logic" and args.logic_reviewer == "external" and not args.prompt:
        print("ERROR: external logic review requires --prompt", file=sys.stderr)
        return 2
    api_key = os.environ.get(args.api_key_env)
    if (args.role == "semantic" or args.logic_reviewer == "external") and not api_key:
        print(
            f"ERROR: {args.api_key_env} is not set; external GPT-5.6 review cannot run",
            file=sys.stderr,
        )
        return 2
    try:
        packet = load_json(args.input)
        if args.role == "semantic":
            return run_semantic(args, packet, api_key)
        if args.logic_reviewer == "external":
            return run_logic(args, packet, api_key)
        return run_local_logic(args, packet)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
