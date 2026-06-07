#!/usr/bin/env python3
"""Run a strict house-rule audit for one LRA chapter.

This validator is chapter-scoped by design. It checks the source shape that a
finished chapter should satisfy and reports a single pass/fail summary.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


FORMAL_ENVS = {
    "definition": "def",
    "axiom": "ax",
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
PROOF_ENVS = {"theorem", "lemma", "proposition", "corollary"}
ALLOWED_NOTE_TOP_ENVS = FORMAL_ENVS.keys() | {
    "remark*",
    "example*",
    "dependencies",
    "tcolorbox",
    "longtable",
    "tabular",
    "tabularx",
    "itemize",
    "enumerate",
}
ALLOWED_PROOF_TOP_ENVS = {
    "remark*",
    "theorem*",
    "proof",
    "dependencies",
}
LABEL_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor", "prf", "ex", "fig"}
DEPENDENCY_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
BEGIN_ENV_RE = re.compile(r"\\begin\{([^{}]+)\}(?:\[[^\]]*\])?")
END_ENV_RE = re.compile(r"\\end\{([^{}]+)\}")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^{}]+)\}")
LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]")
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{([^{}]+)\}")
PLAIN_BLOCK_RE = re.compile(r"\\begin\{(remark|example)\}(?!\*)")
ONLINE_GRAPHICS_RE = re.compile(r"\\(?:includegraphics|input)\{https?://", re.IGNORECASE)
SECTION_RE = re.compile(r"\\(?:sub)*section\*?(?:\[[^\]]*\])?\{[^{}]+\}")
TOOLKIT_RE = re.compile(r"\\begin\{tcolorbox\}(?:\[[\s\S]*?\])?[\s\S]{0,1200}?Toolkit", re.IGNORECASE)
TCOLORBOX_RE = re.compile(r"\\begin\{tcolorbox\}(?:\[[\s\S]*?\])?")
BAD_LABEL_PARTS = {
    "the",
    "following",
    "this",
    "with",
    "for",
    "therefore",
    "and",
    "or",
    "let",
    "denote",
    "page",
}
TOP_LEVEL_COMMANDS = (
    "\\chapter",
    "\\section",
    "\\subsection",
    "\\subsubsection",
    "\\paragraph",
    "\\input",
    "\\include",
    "\\label",
    "\\newpage",
    "\\clearpage",
    "\\phantomsection",
    "\\noindent",
    "\\FloatBarrier",
    "\\LRAProofFor",
)
IGNORED_LABEL_PREFIXES = {"ch", "sec", "subsec", "toc"}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str
    line: int = 1
    severity: str = "error"


@dataclass
class FormalBlock:
    env: str
    prefix: str
    label: str | None
    path: Path
    line: int
    text: str
    decoration: str


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def strip_comment(line: str) -> str:
    escaped = False
    out: list[str] = []
    for ch in line:
        if ch == "\\":
            escaped = not escaped
            out.append(ch)
            continue
        if ch == "%" and not escaped:
            break
        escaped = False
        out.append(ch)
    return "".join(out)


def uncommented(text: str) -> str:
    return "\n".join(strip_comment(line) for line in text.splitlines())


def line_at(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def tex_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.tex")
        if not any(part.startswith(".") for part in path.parts)
    )


def add(findings: list[Finding], root: Path, path: Path, code: str, message: str, line: int = 1) -> None:
    findings.append(Finding(code=code, message=message, path=rel(path, root), line=line))


def normalized_inputs(path: Path) -> set[str]:
    if not path.exists():
        return set()
    targets: set[str] = set()
    for match in INPUT_RE.finditer(uncommented(read(path))):
        target = match.group(1).replace("\\", "/").removesuffix(".tex")
        targets.add(target)
        targets.add(target.removesuffix("/index"))
        targets.add(Path(target).name)
    return targets


def is_routed(index_path: Path, target: Path, chapter: Path) -> bool:
    targets = normalized_inputs(index_path)
    if not targets:
        return False
    try:
        target_rel = target.relative_to(chapter).as_posix().removesuffix(".tex")
    except ValueError:
        target_rel = target.as_posix().removesuffix(".tex")
    variants = {
        target_rel,
        target_rel.removesuffix("/index"),
        target.name,
        target.stem,
        target.parent.name,
    }
    return bool(targets & variants)


def topic_dirs(parent: Path) -> set[str]:
    if not parent.exists():
        return set()
    return {
        child.name
        for child in parent.iterdir()
        if child.is_dir() and not child.name.startswith(".") and child.name != "exercises"
    }


def validate_chapter_layout(chapter: Path, findings: list[Finding]) -> None:
    for relative in ("index.tex", "chapter.yaml", "notes/index.tex", "proofs/index.tex"):
        path = chapter / relative
        if not path.exists():
            add(findings, chapter, path, "missing_chapter_artifact", f"Missing {relative}.")
    for relative in ("notes", "proofs", "proofs/exercises"):
        path = chapter / relative
        if not path.is_dir():
            add(findings, chapter, path, "missing_chapter_directory", f"Missing {relative}/.")

    capstone_candidates = [
        chapter / "capstone.tex",
        chapter / "proofs" / "exercises" / f"capstone-{chapter.name}.tex",
    ]
    if not any(path.exists() for path in capstone_candidates):
        add(findings, chapter, chapter, "missing_capstone", "Missing chapter capstone artifact.")

    chapter_index = chapter / "index.tex"
    if chapter_index.exists():
        chapter_text = uncommented(read(chapter_index))
        if "\\chapter" not in chapter_text:
            add(findings, chapter, chapter_index, "missing_chapter_heading", "Missing chapter heading.")
        if "\\label{ch:" not in chapter_text:
            add(findings, chapter, chapter_index, "missing_chapter_label", "Missing chapter label.")
        first_input = chapter_text.find("\\input")
        pre_inputs = chapter_text if first_input == -1 else chapter_text[:first_input]
        breadcrumb = TCOLORBOX_RE.search(pre_inputs)
        if not breadcrumb:
            add(findings, chapter, chapter_index, "missing_breadcrumb", "Chapter index must contain a breadcrumb tcolorbox before routed inputs.")
        else:
            breadcrumb_block = pre_inputs[breadcrumb.start() : pre_inputs.find("\\end{tcolorbox}", breadcrumb.start())]
            if "\\textbf" not in breadcrumb_block or "\\;\\to\\;" not in breadcrumb_block:
                add(findings, chapter, chapter_index, "invalid_breadcrumb", "Breadcrumb must bold the current chapter and use the arrow-chain form.", line_at(chapter_text, breadcrumb.start()))
            if re.search(r"title\s*=\s*\{[^{}]*Breadcrumb", breadcrumb_block, re.IGNORECASE):
                add(findings, chapter, chapter_index, "invalid_breadcrumb_title", "Breadcrumb title must be the chapter subject, not 'Breadcrumb'.", line_at(chapter_text, breadcrumb.start()))
        if not re.search(r"Roadmap|roadmap", pre_inputs):
            add(findings, chapter, chapter_index, "missing_structural_roadmap", "Chapter index must include structural roadmap content before routed inputs.")
        if not re.search(r"Chapter structure|chapter structure|Structure", pre_inputs):
            add(findings, chapter, chapter_index, "missing_chapter_structure", "Chapter index must include chapter-structure content before routed inputs.")
        for relative in ("notes/index.tex", "proofs/index.tex"):
            if (chapter / relative).exists() and not is_routed(chapter_index, chapter / relative, chapter):
                add(findings, chapter, chapter_index, "unrouted_chapter_index", f"{relative} is not routed from chapter index.")

    notes_topics = topic_dirs(chapter / "notes")
    proofs_topics = topic_dirs(chapter / "proofs")
    for topic in sorted(notes_topics - proofs_topics):
        add(findings, chapter, chapter / "notes" / topic, "missing_matching_proofs_topic", f"notes/{topic}/ has no matching proofs/{topic}/.")
    for topic in sorted(proofs_topics - notes_topics):
        add(findings, chapter, chapter / "proofs" / topic, "orphan_proofs_topic", f"proofs/{topic}/ has no matching notes/{topic}/.")

    for topic in sorted(notes_topics):
        index = chapter / "notes" / topic / "index.tex"
        if not index.exists():
            add(findings, chapter, index, "missing_notes_topic_index", f"Missing notes/{topic}/index.tex.")
        elif not is_routed(chapter / "notes" / "index.tex", index, chapter):
            add(findings, chapter, index, "unrouted_notes_topic", f"notes/{topic}/index.tex is not routed from notes/index.tex.")
    for topic in sorted(proofs_topics):
        index = chapter / "proofs" / topic / "index.tex"
        if not index.exists():
            add(findings, chapter, index, "missing_proofs_topic_index", f"Missing proofs/{topic}/index.tex.")
        elif not is_routed(chapter / "proofs" / "index.tex", index, chapter):
            add(findings, chapter, index, "unrouted_proofs_topic", f"proofs/{topic}/index.tex is not routed from proofs/index.tex.")


def validate_toolkits(chapter: Path, findings: list[Finding]) -> None:
    notes_root = chapter / "notes"
    for path in tex_files(notes_root) if notes_root.exists() else []:
        if path.name == "index.tex":
            continue
        text = uncommented(read(path))
        heading = SECTION_RE.search(text)
        if not heading:
            continue
        first_formal_positions = [
            match.start()
            for match in BEGIN_ENV_RE.finditer(text)
            if match.group(1) in FORMAL_ENVS
        ]
        first_formal = min(first_formal_positions) if first_formal_positions else len(text)
        section_prelude = text[heading.end() : first_formal]
        toolkit_matches = list(TOOLKIT_RE.finditer(section_prelude))
        if len(toolkit_matches) != 1:
            add(findings, chapter, path, "missing_or_duplicate_toolkit", "Each notes section must begin with exactly one Toolkit tcolorbox before formal artifacts.", line_at(text, heading.start()))
            continue
        first_box = TCOLORBOX_RE.search(section_prelude)
        if first_box and first_box.start() != toolkit_matches[0].start():
            add(findings, chapter, path, "toolkit_not_first_box", "The Toolkit must be the first tcolorbox in the section prelude.", line_at(text, heading.end() + toolkit_matches[0].start()))
        if re.search(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary|proof)\}", section_prelude):
            add(findings, chapter, path, "formal_content_inside_toolkit_region", "Section prelude before first formal artifact must not contain formal theorem/proof environments.", line_at(text, heading.start()))


def top_level_allowed_line(line: str) -> bool:
    stripped = strip_comment(line).strip()
    return not stripped or stripped.startswith("%") or stripped.startswith(TOP_LEVEL_COMMANDS)


def validate_block_discipline(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = read(path)
    stack: list[str] = []
    is_note = "/notes/" in path.as_posix().replace("\\", "/")
    is_proof = "/proofs/" in path.as_posix().replace("\\", "/") and "/proofs/exercises/" not in path.as_posix().replace("\\", "/")
    allowed = ALLOWED_PROOF_TOP_ENVS if is_proof else ALLOWED_NOTE_TOP_ENVS

    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = strip_comment(raw_line)
        plain = PLAIN_BLOCK_RE.search(line)
        if plain:
            add(findings, chapter, path, "plain_remark_or_example", "Use remark* or example* for house prose/example blocks.", line_no)
        begin = BEGIN_ENV_RE.match(line)
        if begin:
            env = begin.group(1)
            if not stack and (is_note or is_proof) and env not in allowed:
                add(findings, chapter, path, "unexpected_top_level_environment", f"Unexpected top-level environment {env}.", line_no)
            stack.append(env)
        if not stack and (is_note or is_proof) and not top_level_allowed_line(raw_line):
            add(findings, chapter, path, "top_level_prose", "Prose must be inside a formal, remark*, example*, proof, or dependencies block.", line_no)
        end = END_ENV_RE.match(line)
        if end and stack:
            stack.pop()
    if stack:
        add(findings, chapter, path, "unclosed_environment", f"Unclosed environment(s): {', '.join(stack)}.")


def validate_figures(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = uncommented(read(path))
    if ONLINE_GRAPHICS_RE.search(text):
        add(findings, chapter, path, "online_figure", "Online figure or input URL is not allowed.")
    if "\\begin{tikzpicture}" in text and not path.name.startswith("figure-"):
        add(findings, chapter, path, "inline_tikzpicture", "Nontrivial TikZ must live in a dedicated figure source file.")
    if path.name.startswith("figure-") and "\\begin{tikzpicture}" in text:
        forbidden = ["\\caption", "\\label", "\\begin{figure}", "\\end{figure}"]
        for token in forbidden:
            if token in text:
                add(findings, chapter, path, "invalid_figure_source", f"Figure source contains forbidden token {token}.")


def extract_formal_blocks(chapter: Path) -> list[FormalBlock]:
    blocks: list[FormalBlock] = []
    note_root = chapter / "notes"
    for path in tex_files(note_root) if note_root.exists() else []:
        text = uncommented(read(path))
        matches = list(BEGIN_ENV_RE.finditer(text))
        for idx, match in enumerate(matches):
            env = match.group(1)
            if env not in FORMAL_ENVS:
                continue
            end = re.search(rf"\\end\{{{re.escape(env)}\}}", text[match.end() :])
            if not end:
                continue
            end_pos = match.end() + end.end()
            block_text = text[match.start() : end_pos]
            next_formal = len(text)
            for later in matches[idx + 1 :]:
                if later.group(1) in FORMAL_ENVS:
                    next_formal = later.start()
                    break
            labels = LABEL_RE.findall(block_text)
            blocks.append(
                FormalBlock(
                    env=env,
                    prefix=FORMAL_ENVS[env],
                    label=labels[0] if labels else None,
                    path=path,
                    line=line_at(text, match.start()),
                    text=block_text,
                    decoration=text[end_pos:next_formal],
                )
            )
    return blocks


def validate_label(chapter: Path, path: Path, label: str, line: int, findings: list[Finding]) -> None:
    if ":" not in label:
        add(findings, chapter, path, "malformed_label", f"Label lacks prefix separator: {label}.", line)
        return
    prefix, slug = label.split(":", 1)
    if prefix in IGNORED_LABEL_PREFIXES:
        return
    if prefix not in LABEL_PREFIXES:
        add(findings, chapter, path, "unknown_label_prefix", f"Unknown label prefix: {label}.", line)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", slug):
        add(findings, chapter, path, "weak_label_slug", f"Label slug should be lowercase kebab-case with readable terms: {label}.", line)
    if any(part in BAD_LABEL_PARTS for part in slug.split("-")):
        add(findings, chapter, path, "ocr_like_label", f"Label appears to include prose/OCR filler: {label}.", line)


def validate_labels(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = uncommented(read(path))
    for match in LABEL_RE.finditer(text):
        validate_label(chapter, path, match.group(1), line_at(text, match.start()), findings)


def dependency_bodies(decoration: str) -> list[str]:
    return re.findall(r"\\begin\{dependencies\}(.*?)\\end\{dependencies\}", decoration, re.DOTALL)


def validate_formal_blocks(chapter: Path, blocks: list[FormalBlock], findings: list[Finding]) -> dict[str, FormalBlock]:
    by_label: dict[str, FormalBlock] = {}
    for block in blocks:
        if not block.label:
            add(findings, chapter, block.path, "missing_formal_label", f"{block.env} has no label.", block.line)
            continue
        by_label[block.label] = block
        if not block.label.startswith(f"{block.prefix}:"):
            add(findings, chapter, block.path, "label_prefix_mismatch", f"{block.env} label should start with {block.prefix}:.", block.line)
        if not re.search(r"\\begin\{remark\*\}\[Standard quantified statement\]", block.decoration):
            add(findings, chapter, block.path, "missing_standard_quantified_statement", f"{block.label} lacks Standard quantified statement block.", block.line)
        if not re.search(r"\\begin\{remark\*\}\[Interpretation\]", block.decoration):
            add(findings, chapter, block.path, "missing_interpretation", f"{block.label} lacks Interpretation block.", block.line)
        dep_bodies = dependency_bodies(block.decoration)
        if not dep_bodies:
            add(findings, chapter, block.path, "missing_dependencies", f"{block.label} lacks shared dependencies block.", block.line)
        for body in dep_bodies:
            for item in re.finditer(r"\\item(.*)", body):
                item_text = item.group(1)
                refs = HYPERREF_RE.findall(item_text)
                if not refs:
                    add(findings, chapter, block.path, "dependency_without_hyperref", f"{block.label} dependency item lacks hyperref.", block.line)
                for target in refs:
                    prefix = target.split(":", 1)[0]
                    if prefix not in DEPENDENCY_PREFIXES:
                        add(findings, chapter, block.path, "invalid_dependency_target", f"{block.label} dependency targets non-statement label {target}.", block.line)
        block_window = block.text + "\n" + block.decoration
        if block.env in PROOF_ENVS and block.label:
            proof_target = f"prf:{block.label.split(':', 1)[1]}"
            if proof_target not in HYPERREF_RE.findall(block_window):
                add(findings, chapter, block.path, "missing_proof_navigation", f"{block.label} lacks navigation to {proof_target}.", block.line)

        order_checks = [
            ("proof_link", r"\\hyperref\[prf:"),
            ("standard_quantified_statement", r"\[Standard quantified statement\]"),
            ("interpretation", r"\[Interpretation\]"),
            ("dependencies", r"\\begin\{dependencies\}"),
        ]
        positions = [(name, re.search(pattern, block_window).start()) for name, pattern in order_checks if re.search(pattern, block_window)]
        for (left_name, left_pos), (right_name, right_pos) in zip(positions, positions[1:]):
            if right_pos < left_pos:
                add(findings, chapter, block.path, "decoration_order", f"{right_name} appears before {left_name} for {block.label}.", block.line)
    return by_label


def validate_proofs(chapter: Path, note_blocks: dict[str, FormalBlock], findings: list[Finding]) -> None:
    proof_labels: dict[str, Path] = {}
    proof_for: dict[str, Path] = {}
    proofs_root = chapter / "proofs"
    for path in tex_files(proofs_root) if proofs_root.exists() else []:
        if path.name == "index.tex" or "exercises" in path.parts:
            continue
        text = uncommented(read(path))
        for label in LABEL_RE.findall(text):
            if label.startswith("prf:"):
                proof_labels[label] = path
        for label in PROOF_FOR_RE.findall(text):
            proof_for[label] = path
        for token, code in [
            ("\\newpage", "missing_proof_newpage"),
            ("\\phantomsection", "missing_proof_phantomsection"),
            ("\\LRAProofFor{", "missing_lra_proof_for"),
            ("\\begin{remark*}[Return]", "missing_return_navigation"),
            ("\\begin{theorem*}", "missing_restatement"),
            ("Professional Standard Proof", "missing_professional_proof_layer"),
            ("Detailed Learning Proof", "missing_detailed_learning_layer"),
            ("\\begin{remark*}[Proof structure]", "missing_proof_structure"),
            ("\\begin{dependencies}", "missing_proof_dependencies"),
            ("\\clearpage", "missing_proof_clearpage"),
        ]:
            if token not in text:
                add(findings, chapter, path, code, f"Proof file missing {token}.")
    for label, block in note_blocks.items():
        if block.env not in PROOF_ENVS:
            continue
        expected = f"prf:{label.split(':', 1)[1]}"
        if expected not in proof_labels:
            add(findings, chapter, block.path, "missing_proof_file", f"No proof label found for {label}; expected {expected}.", block.line)
        if label not in proof_for:
            add(findings, chapter, block.path, "missing_proof_association", f"No proof file declares \\LRAProofFor{{{label}}}.", block.line)


def validate_exercises(chapter: Path, findings: list[Finding]) -> None:
    exercises = chapter / "exercises"
    if exercises.exists():
        if not (exercises / "index.tex").exists():
            add(findings, chapter, exercises / "index.tex", "missing_exercises_index", "Missing exercises/index.tex.")
        for path in tex_files(exercises):
            if path.name == "index.tex":
                continue
            text = uncommented(read(path))
            if "\\label{ex:" not in text:
                add(findings, chapter, path, "missing_exercise_label", "Exercise file has no ex: label.")
            if "\\begin{exercise" not in text and "\\Exercise" not in text:
                add(findings, chapter, path, "missing_exercise_environment", "Exercise file must use the house exercise environment or macro.")
            if not is_routed(exercises / "index.tex", path, chapter):
                add(findings, chapter, path, "unrouted_exercise_file", "Exercise file is not routed from exercises/index.tex.")
    proof_exercises = chapter / "proofs" / "exercises"
    if proof_exercises.exists():
        proof_index = proof_exercises / "index.tex"
        if not proof_index.exists():
            add(findings, chapter, proof_index, "missing_proof_exercises_index", "Missing proofs/exercises/index.tex.")
        for path in tex_files(proof_exercises):
            if path.name == "index.tex":
                continue
            if proof_index.exists() and not is_routed(proof_index, path, chapter):
                add(findings, chapter, path, "unrouted_exercise_proof_file", "Exercise proof file is not routed from proofs/exercises/index.tex.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one chapter against LRA house rules.")
    parser.add_argument("--chapter", required=True, type=Path, help="Chapter root, e.g. volume-i/propositional-logic.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chapter = args.chapter.resolve()
    findings: list[Finding] = []
    if not chapter.exists():
        findings.append(Finding("missing_chapter", "Chapter path does not exist.", str(chapter)))
    else:
        validate_chapter_layout(chapter, findings)
        for path in tex_files(chapter):
            validate_block_discipline(chapter, path, findings)
            validate_figures(chapter, path, findings)
            validate_labels(chapter, path, findings)
        validate_toolkits(chapter, findings)
        note_blocks = validate_formal_blocks(chapter, extract_formal_blocks(chapter), findings)
        validate_proofs(chapter, note_blocks, findings)
        validate_exercises(chapter, findings)

    summary = {
        "chapter": str(chapter),
        "status": "FAIL" if findings else "PASS",
        "error_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print("Chapter house-rule validation summary")
        print(f"chapter: {chapter}")
        print(f"error_count: {len(findings)}")
        print(f"status: {summary['status']}")
        for finding in findings:
            print(f"ERROR {finding.code} {finding.path}:{finding.line} - {finding.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
