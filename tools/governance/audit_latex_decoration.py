#!/usr/bin/env python3
"""Inventory theorem-like LaTeX decoration compliance in LRA volume repos."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


AUDITED_ENVS = {
    "definition": "def",
    "axiom": "ax",
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
OPTIONAL_REPORT_ENVS = {"example", "remark", "exercise"}
ALL_ENVS = tuple(AUDITED_ENVS.keys() | OPTIONAL_REPORT_ENVS)
RESULT_ENVS = {"theorem", "lemma", "proposition", "corollary"}
STATEMENT_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
EXCLUDED_DIRS = {
    ".git",
    "common",
    "bibliography",
    "build",
    "dist",
    "lean",
    "out",
    "output",
    "outputs",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".history",
    "reports",
}
STANDARD_FUNCTIONS = {
    "sin",
    "cos",
    "tan",
    "log",
    "ln",
    "exp",
    "sup",
    "inf",
    "lim",
    "max",
    "min",
    "arg",
}

BEGIN_RE = re.compile(
    r"\\begin\{(?P<env>"
    + "|".join(re.escape(env) for env in ALL_ENVS)
    + r")\}(?:\[(?P<title>[^\]]*)\])?"
)
END_TEMPLATE = r"\\end\{%s\}"
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]\{([^}]*)\}")
ITEM_RE = re.compile(r"\\item(?:\s|$)")
PROSE_ITEM_RE = re.compile(r"\\item\s+(?!\\hyperref\[)")
PREDICATE_RE = re.compile(r"(?<!\\)\b([A-Z][A-Za-z0-9_]{2,})\s*\(")


@dataclass
class LatexBlock:
    environment: str
    title: str
    line_start: int
    line_end: int
    text: str
    decoration: str
    box_status: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit LRA volume theorem-like LaTeX decoration compliance."
    )
    parser.add_argument("--root", required=True, help="Repository family root.")
    parser.add_argument("--repos", nargs="+", required=True, help="Repos to scan.")
    parser.add_argument("--out", required=True, help="Output directory for reports.")
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--follow-symlinks", action="store_true")
    parser.add_argument("--fail-on-errors", action="store_true")
    parser.add_argument("--use-ollama", action="store_true")
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--ollama-timeout", type=float, default=60.0)
    return parser.parse_args(argv)


def safe_resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_excluded_dir(path: Path) -> bool:
    name = path.name
    return (
        name in EXCLUDED_DIRS
        or name.startswith("_minted-")
        or name.endswith(".egg-info")
        or name in {"cmake-build-debug", "cmake-build-release"}
    )


def iter_tex_files(repo_path: Path, follow_symlinks: bool) -> list[Path]:
    tex_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_path, followlinks=follow_symlinks):
        current = Path(dirpath)
        if current.is_symlink() and not follow_symlinks:
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if not is_excluded_dir(current / name)]
        for filename in filenames:
            if filename.endswith(".tex"):
                path = current / filename
                if path.is_symlink() and not follow_symlinks:
                    continue
                tex_files.append(path)
    return sorted(tex_files)


def line_number_at(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def find_next_begin(text: str, start: int) -> int:
    match = BEGIN_RE.search(text, start)
    return match.start() if match else len(text)


def line_window_after(text: str, start_index: int, max_lines: int) -> tuple[int, str]:
    end_index = find_next_begin(text, start_index)
    window = text[start_index:end_index]
    lines = window.splitlines()
    clipped = "\n".join(lines[:max_lines])
    return end_index, clipped


def previous_lines(text: str, start_index: int, count: int) -> str:
    prefix = text[:start_index].splitlines()
    return "\n".join(prefix[-count:])


def detect_box_status(block_text: str, preceding: str) -> str:
    combined = preceding + "\n" + block_text
    if re.search(r"\\begin\{[^}]*tcolorbox|\\begin\{.*box|\\(?:blue|gray|green|red)?box", combined):
        return "detected"
    return "uncertain"


def extract_blocks(text: str) -> list[LatexBlock]:
    blocks: list[LatexBlock] = []
    for match in BEGIN_RE.finditer(text):
        env = match.group("env")
        title = (match.group("title") or "").strip()
        end_re = re.compile(END_TEMPLATE % re.escape(env))
        end_match = end_re.search(text, match.end())
        if not end_match:
            continue
        block_text = text[match.start() : end_match.end()]
        _, decoration = line_window_after(text, end_match.end(), 80)
        preceding = previous_lines(text, match.start(), 20)
        blocks.append(
            LatexBlock(
                environment=env,
                title=title,
                line_start=line_number_at(text, match.start()),
                line_end=line_number_at(text, end_match.end()),
                text=block_text,
                decoration=decoration,
                box_status=detect_box_status(block_text, preceding),
            )
        )
    return blocks


def issue(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def dependency_window(decoration: str) -> str:
    dep_match = re.search(
        r"\\begin\{remark\*?\}\[Dependencies\](?P<body>.*?)\\end\{remark\*?\}",
        decoration,
        re.DOTALL | re.IGNORECASE,
    )
    if dep_match:
        return dep_match.group("body")
    if re.search(r"Dependencies", decoration, re.IGNORECASE):
        lines = decoration.splitlines()
        selected: list[str] = []
        capture = False
        for line in lines:
            if "Dependencies" in line:
                capture = True
            if capture:
                selected.append(line)
                if len(selected) >= 25:
                    break
        return "\n".join(selected)
    return ""


def has_named_block(decoration: str, names: tuple[str, ...]) -> bool:
    lowered = decoration.lower()
    return any(name in lowered for name in names)


def find_predicate_leaks(block_text: str) -> list[str]:
    found: list[str] = []
    for match in PREDICATE_RE.finditer(block_text):
        name = match.group(1)
        if name.lower() in STANDARD_FUNCTIONS:
            continue
        if name in {"Definition", "Theorem", "Lemma", "Proposition", "Corollary"}:
            continue
        found.append(name)
    return sorted(set(found))


def deterministic_classification(env: str, issues: list[dict[str, str]]) -> tuple[str, str]:
    if env in OPTIONAL_REPORT_ENVS:
        return "not_applicable", "info"
    severities = Counter(item["severity"] for item in issues)
    if severities["error"]:
        return "non_compliant", "error"
    if len(issues) >= 3:
        return "non_compliant", "warning"
    if issues:
        return "mostly_compliant", "warning"
    return "compliant", "info"


def analyze_block(block: LatexBlock) -> dict[str, Any]:
    labels = LABEL_RE.findall(block.text)
    label = labels[0] if labels else ""
    label_prefix = label.split(":", 1)[0] if ":" in label else ""
    expected_prefix = AUDITED_ENVS.get(block.environment, "")
    decoration = block.decoration
    dep_window = dependency_window(decoration)
    hyperrefs = HYPERREF_RE.findall(dep_window)
    predicate_leaks = find_predicate_leaks(block.text)
    issues: list[dict[str, str]] = []

    if block.environment in AUDITED_ENVS:
        if not label:
            issues.append(issue("missing_label", "The block has no visible label.", "error"))
        elif label_prefix != expected_prefix:
            issues.append(
                issue(
                    "wrong_label_prefix",
                    f"Expected label prefix '{expected_prefix}:' but found '{label_prefix}:'.",
                    "error",
                )
            )

        if not has_named_block(decoration, ("interpretation",)):
            issues.append(issue("missing_interpretation", "Interpretation remark is missing."))
        if not dep_window:
            issues.append(issue("missing_dependencies", "Dependencies remark is missing."))
        else:
            if "prf:" in dep_window:
                issues.append(
                    issue(
                        "prf_dependency_target",
                        "Dependency block appears to use a prf: label as a dependency target.",
                        "error",
                    )
                )
            if not hyperrefs:
                issues.append(
                    issue(
                        "dependencies_without_hyperref",
                        "Dependency block contains no visible hyperref dependency targets.",
                    )
                )
            if PROSE_ITEM_RE.search(dep_window):
                issues.append(
                    issue(
                        "prose_only_dependency",
                        "Dependency block has an item that is not a hyperref dependency.",
                    )
                )
            for target, _name in hyperrefs:
                target_prefix = target.split(":", 1)[0] if ":" in target else ""
                if target_prefix not in STATEMENT_PREFIXES:
                    issues.append(
                        issue(
                            "dependency_not_statement_label",
                            f"Dependency target '{target}' is not a statement label.",
                            "error",
                        )
                    )

        if predicate_leaks:
            issues.append(
                issue(
                    "predicate_leakage_suspected",
                    "Predicate-like identifiers appear inside the theorem body: "
                    + ", ".join(predicate_leaks[:8]),
                )
            )
        if len(labels) > 1:
            issues.append(
                issue(
                    "multiple_labels_in_block",
                    "Multiple labels appear inside one theorem-like block.",
                    "error",
                )
            )
        if re.search(r"\\item\s+\\textbf\{(?:Definition|Theorem|Lemma|Proposition|Corollary)", block.text):
            issues.append(
                issue(
                    "multiple_objects_in_environment",
                    "The block may contain multiple theorem-like objects.",
                    "error",
                )
            )
        if block.line_end - block.line_start + 1 > 120:
            issues.append(issue("oversized_block", "The block is more than 120 lines long."))

        if block.environment in RESULT_ENVS and not has_named_block(
            decoration, ("proof", "see proof", "proof file", "proved")
        ):
            issues.append(
                issue(
                    "proof_availability_unclear",
                    "Proof link or proof availability is not visible nearby.",
                    "info",
                )
            )

    has_quantified = has_named_block(decoration, ("quantified", "formal statement"))
    has_predicate = has_named_block(decoration, ("predicate reading", "predicate-reading"))
    has_negation = has_named_block(decoration, ("negated", "negation"))
    classification, severity = deterministic_classification(block.environment, issues)

    return {
        "label": label,
        "label_prefix": label_prefix,
        "label_prefix_ok": bool(label and label_prefix == expected_prefix),
        "box_status": block.box_status,
        "has_interpretation": has_named_block(decoration, ("interpretation",)),
        "has_quantified_statement": has_quantified,
        "has_predicate_reading": has_predicate,
        "has_negation": has_negation,
        "has_dependencies": bool(dep_window),
        "dependencies_use_hyperref": bool(hyperrefs),
        "dependencies_use_statement_labels": bool(hyperrefs)
        and all((target.split(":", 1)[0] if ":" in target else "") in STATEMENT_PREFIXES for target, _ in hyperrefs),
        "uses_prf_as_dependency": "prf:" in dep_window,
        "predicate_leakage_suspected": bool(predicate_leaks),
        "issues": issues,
        "classification": classification,
        "severity": severity,
        "summary": summarize_issues(issues),
    }


def summarize_issues(issues: list[dict[str, str]]) -> str:
    if not issues:
        return "No deterministic issues found."
    return "; ".join(item["code"] for item in issues[:5])


def prompt_path() -> Path:
    return Path(__file__).resolve().parent / "prompts" / "ollama-decoration-classifier.md"


def call_ollama(
    model: str,
    timeout: float,
    prompt_template: str,
    block: LatexBlock,
    deterministic: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    payload = {
        "model": model,
        "stream": False,
        "prompt": (
            prompt_template
            + "\n\nBLOCK:\n"
            + block.text[:5000]
            + "\n\nNEARBY_DECORATION:\n"
            + block.decoration[:5000]
            + "\n\nDETERMINISTIC_FINDINGS:\n"
            + json.dumps(deterministic, ensure_ascii=True, indent=2)
        ),
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, issue("ollama_request_failed", f"Ollama request failed: {exc}")

    raw = response_data.get("response", "")
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, issue("ollama_invalid_json", "Ollama response was not strict JSON.")


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def audit_repo(
    root: Path,
    repo: str,
    max_files: int | None,
    follow_symlinks: bool,
    use_ollama: bool,
    model: str,
    ollama_timeout: float,
    prompt_template: str | None,
) -> tuple[list[dict[str, Any]], int]:
    repo_path = safe_resolve(root / repo)
    if not repo_path.exists() or not repo_path.is_dir():
        raise FileNotFoundError(f"Repository not found: {repo_path}")
    if root not in repo_path.parents and repo_path != root:
        raise ValueError(f"Repository path escapes root: {repo_path}")

    tex_files = iter_tex_files(repo_path, follow_symlinks)
    if max_files is not None:
        tex_files = tex_files[:max_files]

    records: list[dict[str, Any]] = []
    for tex_file in tex_files:
        text = tex_file.read_text(encoding="utf-8", errors="replace")
        for block in extract_blocks(text):
            deterministic = analyze_block(block)
            issues = list(deterministic["issues"])
            ollama_result = None
            ollama_used = False
            if use_ollama and prompt_template:
                ollama_used = True
                ollama_result, ollama_issue = call_ollama(
                    model, ollama_timeout, prompt_template, block, deterministic
                )
                if ollama_issue:
                    issues.append(ollama_issue)

            classification = deterministic["classification"]
            severity = deterministic["severity"]
            if ollama_result and isinstance(ollama_result, dict):
                classification = str(ollama_result.get("classification", classification))
                severity = str(ollama_result.get("severity", severity))

            records.append(
                {
                    "repo": repo,
                    "file": relative_path(tex_file, repo_path),
                    "environment": block.environment,
                    "title": block.title,
                    "line_start": block.line_start,
                    "line_end": block.line_end,
                    "label": deterministic["label"],
                    "label_prefix": deterministic["label_prefix"],
                    "classification": classification,
                    "severity": severity,
                    "box_status": deterministic["box_status"],
                    "detected": {k: v for k, v in deterministic.items() if k.startswith("has_") or k.endswith("_ok") or k.startswith("dependencies_") or k in {"uses_prf_as_dependency", "predicate_leakage_suspected"}},
                    "issues": issues,
                    "deterministic_issue_count": len(deterministic["issues"]),
                    "ollama_used": ollama_used,
                    "ollama_result": ollama_result,
                    "summary": summarize_issues(issues),
                }
            )
    return records, len(tex_files)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "repo",
        "file",
        "environment",
        "title",
        "line_start",
        "line_end",
        "label",
        "classification",
        "severity",
        "deterministic_issue_count",
        "ollama_used",
        "summary",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    records = data["records"]
    classification_counts = Counter(record["classification"] for record in records)
    issue_counts = Counter(
        item["code"] for record in records for item in record.get("issues", [])
    )
    file_counts: dict[str, int] = defaultdict(int)
    for record in records:
        file_counts[f"{record['repo']}/{record['file']}"] += len(record.get("issues", []))

    lines = [
        "# Decoration Audit",
        "",
        f"- Total scanned files: {data['total_scanned_files']}",
        f"- Total blocks: {len(records)}",
        "",
        "## Counts By Classification",
        "",
    ]
    for name, count in classification_counts.most_common():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Counts By Issue Code", ""])
    if issue_counts:
        for code, count in issue_counts.most_common():
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- No issues found.")

    lines.extend(["", "## Top Files By Issue Count", ""])
    for filename, count in sorted(file_counts.items(), key=lambda item: item[1], reverse=True)[:10]:
        if count:
            lines.append(f"- `{filename}`: {count}")
    if not any(file_counts.values()):
        lines.append("- No file-level issues found.")

    lines.extend(["", "## Sample Non-Compliant Blocks", ""])
    samples = [
        record
        for record in records
        if record["classification"] in {"non_compliant", "needs_human_review"}
    ][:10]
    if samples:
        for record in samples:
            lines.append(
                f"- `{record['repo']}/{record['file']}:{record['line_start']}` "
                f"{record['environment']} `{record.get('label') or '(no label)'}`: "
                f"{record['summary']}"
            )
    else:
        lines.append("- No non-compliant samples in this run.")

    lines.extend(["", "## Next Recommended Refactor Targets", ""])
    if issue_counts:
        lines.append("- Review files with the highest issue counts first.")
        lines.append("- Prioritize missing labels, wrong label prefixes, and dependency issues.")
        lines.append("- Use local-model classification only for ambiguous cases after deterministic triage.")
    else:
        lines.append("- Expand the scan to more files or repos to estimate broader refactor scope.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = safe_resolve(Path(args.root))
    out_dir = safe_resolve(Path(args.out))

    if not root.exists() or not root.is_dir():
        print(f"fatal: root directory not found: {root}", file=sys.stderr)
        return 1
    if root in out_dir.parents or out_dir == root:
        pass
    else:
        print(f"fatal: output directory must be under root: {out_dir}", file=sys.stderr)
        return 1

    prompt_template = None
    if args.use_ollama:
        template_path = prompt_path()
        if not template_path.exists():
            print(f"fatal: Ollama prompt template missing: {template_path}", file=sys.stderr)
            return 1
        prompt_template = template_path.read_text(encoding="utf-8")

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"fatal: could not create output directory: {exc}", file=sys.stderr)
        return 1

    all_records: list[dict[str, Any]] = []
    scanned_files = 0
    try:
        for repo in args.repos:
            records, file_count = audit_repo(
                root=root,
                repo=repo,
                max_files=args.max_files,
                follow_symlinks=args.follow_symlinks,
                use_ollama=args.use_ollama,
                model=args.model,
                ollama_timeout=args.ollama_timeout,
                prompt_template=prompt_template,
            )
            all_records.extend(records)
            scanned_files += file_count
    except (OSError, ValueError) as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 1

    data = {
        "root": str(root),
        "repos": args.repos,
        "total_scanned_files": scanned_files,
        "total_blocks": len(all_records),
        "ollama_used": args.use_ollama,
        "records": all_records,
    }
    write_json(out_dir / "decoration-audit.json", data)
    write_csv(out_dir / "decoration-audit.csv", all_records)
    write_markdown(out_dir / "decoration-audit.md", data)

    error_count = sum(1 for record in all_records if record["severity"] == "error")
    print(
        f"audit completed: {scanned_files} files scanned, "
        f"{len(all_records)} blocks found, {error_count} error-severity records"
    )
    if args.fail_on_errors and error_count:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

