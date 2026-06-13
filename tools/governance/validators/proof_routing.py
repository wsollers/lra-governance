from __future__ import annotations

from pathlib import Path

from core.finding import Finding, finding
from core.file_inventory import reachable_files
from core.tex import INPUT_RE, is_routed, read_text, strip_latex_comment, strip_latex_comments
from core.volume import chapter_roots, is_ignored


def validate(volume_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for chapter in chapter_roots(volume_root):
        included = reachable_files(chapter)
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

        if not proofs_root.exists():
            continue
        for topic_dir in sorted(
            path
            for path in proofs_root.iterdir()
            if path.is_dir() and path.name != "exercises" and not is_ignored(path, proofs_root)
        ):
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
            for proof_file in sorted(topic_dir.glob("*.tex")):
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
