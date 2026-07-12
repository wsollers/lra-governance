from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import validator_file_set
from core.tex import INPUT_RE, is_routed, read_text, strip_latex_comment, strip_latex_comments
from core.volume import routed_chapter_roots


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in routed_chapter_roots(volume_root):
        included = validator_file_set(chapter, files)
        proofs_root = chapter / "proofs"
        proofs_index = proofs_root / "index.tex"
        exercises_index = proofs_root / "exercises" / "index.tex"
        if exercises_index.exists() and _directly_inputs(proofs_index, exercises_index, chapter):
            findings.append(
                finding(
                    "proofs_index_routes_exercises",
                    "proofs/exercises/index.tex must be routed only from the chapter router, not from proofs/index.tex.",
                    proofs_index,
                    volume_root,
                    severity="warning",
                )
            )

        if proofs_index.exists() and proofs_index.resolve() in included:
            text = read_text(proofs_index)
            if "\\begin{proof}" in text or "\\LRAProofFor{" in text:
                findings.append(
                    finding(
                        "proofs_index_contains_proof_content",
                        "proofs/index.tex must be a router, not a proof-content file.",
                        proofs_index,
                        volume_root,
                    )
                )
            _check_router_only(volume_root, proofs_index, findings, "proofs_index_contains_rendered_content", "proofs/index.tex")

        for topic_dir in _active_topic_dirs(proofs_root, included):
            index = topic_dir / "index.tex"
            index_included = index.exists() and index.resolve() in included
            if index_included:
                text = read_text(index)
                if "\\begin{proof}" in text or "\\LRAProofFor{" in text:
                    findings.append(
                        finding(
                            "proofs_topic_index_contains_proof_content",
                            f"proofs/{topic_dir.name}/index.tex must route proof files, not contain proof content.",
                            index,
                            volume_root,
                        )
                    )
                _check_router_only(
                    volume_root,
                    index,
                    findings,
                    "proofs_topic_index_contains_rendered_content",
                    f"proofs/{topic_dir.name}/index.tex",
                )
                if not is_routed(proofs_index, index, chapter):
                    findings.append(
                        finding(
                            "unrouted_proofs_topic",
                            f"proofs/{topic_dir.name}/index.tex is not routed from proofs/index.tex.",
                            index,
                            volume_root,
                        )
                    )
            for proof_file in _active_topic_files(topic_dir, included):
                if proof_file.name == "index.tex":
                    continue
                if proof_file.resolve() not in included:
                    continue
                if index_included and not is_routed(index, proof_file, chapter):
                    findings.append(
                        finding(
                            "unrouted_proof_topic_file",
                            f"{proof_file.relative_to(chapter).as_posix()} is not routed from proofs/{topic_dir.name}/index.tex.",
                            proof_file,
                            volume_root,
                        )
                    )
    return findings


def _active_topic_dirs(proofs_root: Path, included: set[Path]) -> list[Path]:
    topics: set[Path] = set()
    for path in included:
        try:
            rel = path.relative_to(proofs_root)
        except ValueError:
            continue
        if len(rel.parts) >= 2 and rel.parts[0] != "exercises":
            topics.add(proofs_root / rel.parts[0])
    return sorted(topics)


def _active_topic_files(topic_dir: Path, included: set[Path]) -> list[Path]:
    return sorted(
        path
        for path in included
        if path.parent == topic_dir and path.name != "index.tex"
    )


def _directly_inputs(index_path: Path, target: Path, chapter_root: Path) -> bool:
    if not index_path.exists():
        return False
    try:
        relative = target.relative_to(chapter_root).as_posix().removesuffix(".tex")
    except ValueError:
        relative = target.as_posix().replace("\\", "/").removesuffix(".tex")
    variants = {relative, relative.removesuffix("/index")}
    for match in INPUT_RE.finditer(strip_latex_comments(read_text(index_path))):
        routed = match.group(1).replace("\\", "/").removesuffix(".tex")
        routed_base = routed.removesuffix("/index")
        if (
            routed in variants
            or routed_base in variants
            or routed.endswith(f"/{relative}")
            or routed_base.endswith(f"/{relative.removesuffix('/index')}")
        ):
            return True
    return False


def _check_router_only(volume_root: Path, index: Path, findings: list[Finding], code: str, label: str) -> None:
    for line_no, raw in enumerate(read_text(index).splitlines(), 1):
        line = strip_latex_comment(raw).strip()
        if line and not INPUT_RE.fullmatch(line):
            findings.append(
                finding(
                    code,
                    f"{label} must be a router containing only input lines.",
                    index,
                    volume_root,
                    line_no,
                )
            )
