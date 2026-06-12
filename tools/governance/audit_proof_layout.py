#!/usr/bin/env python3
"""Audit LRA proof files for schema-level layout compliance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from _targeting import discovery_lines, is_ignored_path, proof_validation_paths, resolve_target, target_chapters


PROOF_EXTENSIONS = {".tex"}
THEOREM_LABEL_RE = re.compile(r"\\label\{((?:thm|lem|prop|cor):[a-z0-9-]+)\}")
PROOF_LABEL_RE = re.compile(r"\\label\{(prf:[a-z0-9-]+)\}")
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{((?:thm|lem|prop|cor):[a-z0-9-]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[([a-z]+:[a-z0-9-]+)\]\{([^}]*)\}")
PROOF_VAULT_RE = re.compile(r"\\ProofVaultURL\{([^}]*)\}")
BEGIN_PROOF_RE = re.compile(r"\\begin\{proof\}(.*?)\\end\{proof\}", re.DOTALL)
THEOREM_STAR_RE = re.compile(
    r"\\begin\{(?:theorem|lemma|proposition|corollary)\*\}(?:\[[^\]]*\])?(.*?)\\end\{(?:theorem|lemma|proposition|corollary)\*\}",
    re.DOTALL,
)
PROOF_STRUCTURE_RE = re.compile(
    r"\\begin\{remark\*\}\[Proof structure\](.*?)\\end\{remark\*\}",
    re.DOTALL,
)
DEPENDENCIES_RE = re.compile(
    r"(?:\\begin\{dependencies\}(.*?)\\end\{dependencies\}"
    r"|\\begin\{remark\*\}\[Dependencies\](.*?)\\end\{remark\*\}"
    r"|\\NoLocalDependencies)",
    re.DOTALL,
)
ASCII_HYPHEN_FILENAME_RE = re.compile(r"^[a-z0-9-]+\.tex$")


@dataclass
class Finding:
    severity: str
    code: str
    message: str


@dataclass
class ProofAudit:
    path: str
    status: str
    theorem_label: str | None = None
    proof_label: str | None = None
    note_topic: str | None = None
    proof_topic: str | None = None
    findings: list[Finding] = field(default_factory=list)


@dataclass
class AuditSummary:
    root: str
    refactor_mode: bool
    proof_files: int = 0
    compliant_full: int = 0
    compliant_stub: int = 0
    non_compliant: int = 0
    warnings: int = 0
    errors: int = 0
    audits: list[ProofAudit] = field(default_factory=list)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit proof files for LRA proof layout compliance."
    )
    parser.add_argument("--root", required=True, help="Leaf repo, volume, or chapter root.")
    parser.add_argument("--volume", help="Audit proofs under a discovered volume, such as volume-ii.")
    parser.add_argument("--chapter", help="Audit proofs under a discovered chapter, such as whole-numbers.")
    parser.add_argument(
        "--section",
        help="Audit proofs under one discovered topic, such as extending-addition. Use --chapter if ambiguous.",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List discovered volumes, chapters, and sections, then exit.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Fail if any proof is non-compliant.")
    parser.add_argument(
        "--refactor-mode",
        action="store_true",
        help="Recognize legacy proofs/notes layout as transitional instead of an error.",
    )
    return parser.parse_args(argv)


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def add(audit: ProofAudit, severity: str, code: str, message: str) -> None:
    audit.findings.append(Finding(severity, code, message))


def find_chapter_roots(root: Path) -> list[Path]:
    roots = []
    for proofs_dir in root.rglob("proofs"):
        if is_ignored_path(proofs_dir, root):
            continue
        if proofs_dir.is_dir() and (proofs_dir.parent / "notes").is_dir():
            roots.append(proofs_dir.parent)
    if root.name != "proofs" and (root / "proofs").is_dir() and (root / "notes").is_dir():
        roots.append(root)
    return sorted(set(path.resolve() for path in roots))


def proof_files(chapter_root: Path) -> list[Path]:
    proofs_root = chapter_root / "proofs"
    if not proofs_root.exists():
        return []
    files = []
    for path in proofs_root.rglob("*.tex"):
        if is_ignored_path(path, chapter_root):
            continue
        rel = path.relative_to(proofs_root).parts
        if path.name == "index.tex":
            continue
        if rel and rel[0] == "exercises":
            continue
        files.append(path)
    return sorted(files)


def proof_files_under(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in paths:
        if not root.exists():
            continue
        for path in root.rglob("*.tex"):
            if is_ignored_path(path, root):
                continue
            if path.name == "index.tex":
                continue
            if "exercises" in path.parts:
                continue
            files.append(path)
    return sorted(set(path.resolve() for path in files))


def topic_after(anchor: str, path: Path, chapter_root: Path) -> str | None:
    try:
        parts = path.relative_to(chapter_root).parts
    except ValueError:
        return None
    if anchor not in parts:
        return None
    index = parts.index(anchor)
    if index + 2 >= len(parts):
        return None
    return parts[index + 1]


def note_topics(chapter_root: Path) -> dict[str, str]:
    topics: dict[str, str] = {}
    notes = chapter_root / "notes"
    if not notes.exists():
        return topics
    for path in sorted(notes.rglob("*.tex")):
        if is_ignored_path(path, chapter_root):
            continue
        if path.name == "index.tex":
            continue
        topic = topic_after("notes", path, chapter_root)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label in THEOREM_LABEL_RE.findall(text):
            if topic:
                topics[label] = topic
    return topics


def normalized_input_targets(index_text: str) -> set[str]:
    targets = set()
    for match in re.finditer(r"\\(?:input|include)\{([^}]+)\}", index_text):
        target = match.group(1).replace("\\", "/").removesuffix(".tex")
        targets.add(target)
        targets.add(Path(target).name)
    return targets


def index_inputs(index_path: Path, target: Path, chapter_root: Path) -> bool:
    if not index_path.exists():
        return False
    text = index_path.read_text(encoding="utf-8", errors="ignore")
    targets = normalized_input_targets(text)
    rel = target.relative_to(chapter_root).as_posix().removesuffix(".tex")
    return rel in targets or target.stem in targets or rel.removesuffix("/index") in targets


def block(text: str, regex: re.Pattern[str]) -> str:
    match = regex.search(text)
    if not match:
        return ""
    groups = [group for group in match.groups() if group is not None]
    return groups[0] if groups else match.group(0)


def proof_blocks(text: str) -> tuple[str, str]:
    professional = ""
    detailed = ""
    for body in BEGIN_PROOF_RE.findall(text):
        if "Professional Standard Proof" in body:
            professional = body
        if "Detailed Learning Proof" in body:
            detailed = body
    return professional, detailed


def has_todo(text: str) -> bool:
    return bool(re.search(r"\bTODO\b", text, re.IGNORECASE))


def position(text: str, pattern: str) -> int:
    found = re.search(pattern, text, re.DOTALL)
    return found.start() if found else -1


def validate_order(text: str, audit: ProofAudit) -> None:
    layers = [
        ("newpage", r"\\newpage"),
        ("phantomsection", r"\\phantomsection"),
        ("proof_label", r"\\label\{prf:[a-z0-9-]+\}"),
        ("proof_for", r"\\LRAProofFor\{(?:thm|lem|prop|cor):[a-z0-9-]+\}"),
        ("return_navigation", r"\\begin\{remark\*\}\[Return\]"),
        ("theorem_restatement", r"\\begin\{(?:theorem|lemma|proposition|corollary)\*\}"),
        ("professional_standard_proof", r"Professional Standard Proof"),
        ("detailed_learning_proof", r"Detailed Learning Proof"),
        ("proof_structure", r"\\begin\{remark\*\}\[Proof structure\]"),
        ("dependencies", r"(?:\\begin\{dependencies\}|\\begin\{remark\*\}\[Dependencies\]|\\NoLocalDependencies)"),
        ("clearpage", r"\\clearpage"),
    ]
    positions = [(name, position(text, pattern)) for name, pattern in layers]
    for name, pos in positions:
        if pos < 0:
            add(audit, "error", f"missing_{name}", f"Missing required layer: {name}.")
    present = [(name, pos) for name, pos in positions if pos >= 0]
    for (left_name, left_pos), (right_name, right_pos) in zip(present, present[1:]):
        if right_pos < left_pos:
            add(
                audit,
                "error",
                "layer_order",
                f"Layer {right_name} appears before {left_name}.",
            )


def audit_proof(path: Path, chapter_root: Path, root: Path, notes: dict[str, str], refactor_mode: bool) -> ProofAudit:
    rel = relpath(path, root)
    text = path.read_text(encoding="utf-8", errors="ignore")
    audit = ProofAudit(path=rel, status="non_compliant")

    proof_topic = topic_after("proofs", path, chapter_root)
    audit.proof_topic = proof_topic
    if path.name == "index.tex":
        add(audit, "error", "index_as_proof", "Index file should not be audited as a proof.")
    if not ASCII_HYPHEN_FILENAME_RE.match(path.name):
        add(audit, "error", "filename_style", "Proof filename must be lowercase hyphenated ASCII.")

    labels = PROOF_LABEL_RE.findall(text)
    proof_fors = PROOF_FOR_RE.findall(text)
    audit.proof_label = labels[0] if labels else None
    audit.theorem_label = proof_fors[0] if proof_fors else None

    if len(labels) != 1:
        add(audit, "error", "proof_label_count", f"Expected exactly one proof label; found {len(labels)}.")
    if len(proof_fors) != 1:
        add(audit, "error", "proof_for_count", f"Expected exactly one LRAProofFor target; found {len(proof_fors)}.")
    if labels and proof_fors:
        proof_root = labels[0].split(":", 1)[1]
        theorem_root = proof_fors[0].split(":", 1)[1]
        if proof_root != theorem_root:
            add(audit, "error", "label_root_mismatch", "Proof label root must match LRAProofFor root.")
        expected_filename = f"prf-{proof_root}.tex"
        if path.name != expected_filename:
            add(audit, "error", "filename_label_mismatch", f"Expected filename {expected_filename}.")

    if proof_topic == "notes":
        severity = "warning" if refactor_mode else "error"
        add(
            audit,
            severity,
            "legacy_proofs_notes_layout",
            "Legacy proofs/notes layout is allowed only in explicit refactor mode.",
        )
    elif not proof_topic:
        add(audit, "error", "missing_proof_topic", "Proof file is not under proofs/{topic}/.")

    if audit.theorem_label:
        note_topic = notes.get(audit.theorem_label)
        audit.note_topic = note_topic
        if note_topic and proof_topic and proof_topic != note_topic:
            severity = "warning" if refactor_mode and proof_topic == "notes" else "error"
            add(
                audit,
                severity,
                "topic_mismatch",
                f"Theorem is under notes/{note_topic}/ but proof is under proofs/{proof_topic}/.",
            )
        if note_topic is None:
            add(audit, "warning", "unknown_note_topic", "Could not resolve theorem label to a notes topic.")

    validate_order(text, audit)

    if audit.theorem_label:
        return_links = [target for target, _ in HYPERREF_RE.findall(text) if target == audit.theorem_label]
        if not return_links:
            add(audit, "error", "missing_return_link", "Missing return hyperref to LRAProofFor target.")

    vault = PROOF_VAULT_RE.search(text)
    theorem_pos = position(text, r"\\begin\{(?:theorem|lemma|proposition|corollary)\*\}")
    return_pos = position(text, r"\\begin\{remark\*\}\[Return\]")
    if vault:
        url = vault.group(1).strip()
        if not url:
            add(audit, "error", "empty_proof_vault_url", "ProofVaultURL must not be empty.")
        if re.search(r"\.(?:jpg|jpeg|png|webp)$", url, re.IGNORECASE):
            add(audit, "error", "raw_image_proof_vault_url", "ProofVaultURL must point to a record, not a raw image.")
        if return_pos >= 0 and theorem_pos >= 0 and not (return_pos < vault.start() < theorem_pos):
            add(audit, "error", "proof_vault_url_position", "ProofVaultURL must appear after Return and before the starred restatement.")

    theorem_body = block(text, THEOREM_STAR_RE)
    professional_body, detailed_body = proof_blocks(text)
    structure_body = block(text, PROOF_STRUCTURE_RE)
    dependencies_body = block(text, DEPENDENCIES_RE)

    if theorem_body and "\\label" in theorem_body:
        add(audit, "error", "label_inside_restatement", "theorem* restatement must not contain labels.")
    if not professional_body:
        add(audit, "error", "missing_professional_body", "Missing Professional Standard proof body.")
    if not detailed_body:
        add(audit, "error", "missing_detailed_body", "Missing Detailed Learning proof body.")
    if not structure_body:
        add(audit, "error", "missing_proof_structure_body", "Missing Proof structure remark.")
    if not dependencies_body:
        add(audit, "error", "missing_dependencies_body", "Missing dependencies block.")

    for target, _ in HYPERREF_RE.findall(dependencies_body):
        if target.startswith("prf:"):
            add(audit, "error", "proof_dependency_target", "Dependencies must not target proof labels.")

    todo_parts = {
        "theorem_restatement": has_todo(theorem_body),
        "professional_standard_proof": has_todo(professional_body),
        "detailed_learning_proof": has_todo(detailed_body),
        "proof_structure": has_todo(structure_body),
        "dependencies": has_todo(dependencies_body),
    }
    proof_todo = todo_parts["professional_standard_proof"] or todo_parts["detailed_learning_proof"]
    if proof_todo and not (todo_parts["professional_standard_proof"] and todo_parts["detailed_learning_proof"]):
        add(audit, "error", "partial_stub", "Stub proofs must TODO both proof bodies or neither.")

    topic_index = chapter_root / "proofs" / (proof_topic or "") / "index.tex"
    proof_index = chapter_root / "proofs" / "index.tex"
    if proof_topic and not index_inputs(topic_index, path, chapter_root):
        add(audit, "error", "proof_not_in_topic_index", "Proof file is not reachable from proofs/{topic}/index.tex.")
    if proof_topic and not index_inputs(proof_index, topic_index, chapter_root):
        add(audit, "error", "topic_index_not_in_proofs_index", "proofs/{topic}/index.tex is not reachable from proofs/index.tex.")

    errors = [finding for finding in audit.findings if finding.severity == "error"]
    if not errors:
        audit.status = "compliant_stub" if proof_todo else "compliant_full"
    return audit


def audit_root(
    root: Path,
    refactor_mode: bool,
    chapters: list[Path] | None = None,
    scoped_proof_dirs: list[Path] | None = None,
) -> AuditSummary:
    root = root.resolve()
    summary = AuditSummary(root=str(root), refactor_mode=refactor_mode)
    for chapter_root in chapters if chapters is not None else find_chapter_roots(root):
        notes = note_topics(chapter_root)
        files = proof_files_under(scoped_proof_dirs) if scoped_proof_dirs is not None else proof_files(chapter_root)
        for path in files:
            if not path.is_relative_to(chapter_root):
                continue
            audit = audit_proof(path, chapter_root, root, notes, refactor_mode)
            summary.audits.append(audit)
            summary.proof_files += 1
            if audit.status == "compliant_full":
                summary.compliant_full += 1
            elif audit.status == "compliant_stub":
                summary.compliant_stub += 1
            else:
                summary.non_compliant += 1
            summary.errors += sum(1 for finding in audit.findings if finding.severity == "error")
            summary.warnings += sum(1 for finding in audit.findings if finding.severity == "warning")
    return summary


def print_text(summary: AuditSummary) -> None:
    print(f"root: {summary.root}")
    print(f"refactor_mode: {summary.refactor_mode}")
    print(f"proof_files: {summary.proof_files}")
    print(f"compliant_full: {summary.compliant_full}")
    print(f"compliant_stub: {summary.compliant_stub}")
    print(f"non_compliant: {summary.non_compliant}")
    print(f"warnings: {summary.warnings}")
    print(f"errors: {summary.errors}")
    for audit in summary.audits:
        if audit.status != "non_compliant":
            continue
        print(f"\nNON-COMPLIANT {audit.path}")
        for finding in audit.findings:
            print(f"- {finding.severity}: {finding.code}: {finding.message}")


def to_json(summary: AuditSummary) -> str:
    return json.dumps(asdict(summary), indent=2)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.list_targets:
        print("\n".join(discovery_lines(root)))
        return 0
    try:
        target = resolve_target(root, args.volume, args.chapter, args.section)
    except ValueError as exc:
        print(f"ERROR target_resolution - {exc}", file=sys.stderr)
        return 2
    scoped_dirs = proof_validation_paths(target) if target.scope == "section" else None
    summary = audit_root(root, args.refactor_mode, target_chapters(target), scoped_dirs)
    if args.format == "json":
        print(to_json(summary))
    else:
        print_text(summary)
    if args.strict and summary.non_compliant:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
