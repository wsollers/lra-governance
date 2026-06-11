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

from _targeting import is_ignored_path


FORMAL_ENVS = {
    "definition": "def",
    "axiom": "ax",
    "theorem": "thm",
    "lemma": "lem",
    "proposition": "prop",
    "corollary": "cor",
}
FORMAL_BOX_ENVS = {
    "definitionbox": "definition",
    "axiombox": "axiom",
    "theorembox": "theorem",
    "lemmabox": "lemma",
    "propositionbox": "proposition",
    "corollarybox": "corollary",
}
PROOF_ENVS = {"theorem", "lemma", "proposition", "corollary"}
STARRED_RESTATEMENT_ENVS = {"theorem*", "lemma*", "proposition*", "corollary*"}
ALLOWED_NOTE_TOP_ENVS = set(FORMAL_BOX_ENVS) | {
    "remark*",
    "example*",
    "exposition",
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
    *STARRED_RESTATEMENT_ENVS,
    "proof",
    "dependencies",
}
LABEL_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor", "prf", "ex", "fig", "cap"}
DEPENDENCY_PREFIXES = {"def", "ax", "thm", "lem", "prop", "cor"}
NOTE_ONLY_TOPICS = {"notation"}
BEGIN_ENV_RE = re.compile(r"\\begin\{([^{}]+)\}(?:\[[^\]]*\])?")
END_ENV_RE = re.compile(r"\\end\{([^{}]+)\}")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^{}]+)\}")
LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]")
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{([^{}]+)\}")
OPERATORNAME_RE = re.compile(r"\\operatorname\{([^{}]+)\}")
BEGIN_ARTIFACT_RE = re.compile(r"%\s*BEGIN GENERATED ARTIFACT:\s*([A-Za-z0-9:-]+)")
END_ARTIFACT_RE = re.compile(r"%\s*END GENERATED ARTIFACT:\s*([A-Za-z0-9:-]+)")
CITE_OR_LABEL_RE = re.compile(r"\\(?:label|cite|citet|citep)\b")
PLAIN_BLOCK_RE = re.compile(r"\\begin\{(remark|example)\}(?!\*)")
ONLINE_GRAPHICS_RE = re.compile(r"\\(?:includegraphics|input)\{https?://", re.IGNORECASE)
STARRED_CHAPTER_RE = re.compile(r"\\chapter\*(?:\[[^\]]*\])?\{[^{}]+\}")
SECTION_HEADING_RE = re.compile(r"\\section(?:\[[^\]]*\])?\{[^{}]+\}")
STARRED_SECTION_RE = re.compile(r"\\section\*(?:\[[^\]]*\])?\{[^{}]+\}")
UNSTARRED_SUBSECTION_RE = re.compile(r"\\sub(?:sub)?section(?:\[[^\]]*\])?\{[^{}]+\}")
STARRED_SUBSECTION_RE = re.compile(r"\\sub(?:sub)?section\*(?:\[[^\]]*\])?\{[^{}]+\}")
TOOLKIT_RE = re.compile(r"\\begin\{tcolorbox\}(?:\[[\s\S]*?\])?[\s\S]{0,1200}?Toolkit", re.IGNORECASE)
TCOLORBOX_RE = re.compile(r"\\begin\{tcolorbox\}(?:\[[\s\S]*?\])?")
TCOLORBOX_FORMAL_RE = re.compile(
    r"\\begin\{tcolorbox\}(?P<options>\[[\s\S]*?\])?\s*"
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}",
    re.IGNORECASE,
)
FORMAL_BOX_RE = re.compile(
    r"\\begin\{(?P<wrapper>definitionbox|axiombox|theorembox|lemmabox|propositionbox|corollarybox)\}"
    r"(?:\{[^{}]*\})?\s*"
    r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}",
    re.IGNORECASE,
)
EXPOSITION_RE = re.compile(r"\\begin\{remark\*\}\[Exposition\](?P<body>[\s\S]*?)\\end\{remark\*\}", re.IGNORECASE)
EXPOSITION_BEGIN_RE = re.compile(r"\s*\\begin\{remark\*\}\[Exposition\]", re.IGNORECASE)
DECORATION_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|dependencies)\}(?:\[(?P<title>[^\]]+)\])?",
    re.IGNORECASE,
)
VOICE_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|exposition)\}(?:\[(?P<title>[^\]]+)\])?(?P<body>[\s\S]*?)\\end\{(?P=env)\}",
    re.IGNORECASE,
)
EXERCISE_ENV_RE = re.compile(r"\\begin\{(?:exercise|exerciseproblem|exerciseitem|generatedexercise|sourcedexercise)\b|\\(?:Exercise|GeneratedExercise|SourcedExercise)\b")
STRUCTURAL_ORDER = {
    "chapter": [
        "chapter",
        "chapter_label",
        "breadcrumb",
        "notes_input",
        "proofs_input",
        "capstone_heading",
        "capstone_input",
    ],
    "proof": [
        "newpage",
        "phantomsection",
        "proof_label",
        "proof_for",
        "return",
        "proof_vault",
        "restatement",
        "professional",
        "detailed",
        "proof_structure",
        "dependencies",
        "clearpage",
    ],
    "capstone": [
        "newpage",
        "phantomsection",
        "capstone_label",
        "capstone_box",
        "dependency_ceiling",
    ],
}
DECORATION_ORDER = {
    "proof_link": 10,
    "standard quantified statement": 20,
    "definition predicate reading": 30,
    "predicate reading": 30,
    "negated quantified statement": 40,
    "negation predicate reading": 50,
    "failure modes": 60,
    "failure mode decomposition": 70,
    "contrapositive quantified statement": 80,
    "contrapositive predicate reading": 90,
    "interpretation": 100,
    "historical note": 105,
    "comparison with feferman": 105,
    "exposition": 110,
    "examples": 120,
    "non-examples": 130,
    "dependencies": 140,
}
DEPENDENT_DECORATION_PARENTS = {
    "negation predicate reading": "negated quantified statement",
    "failure mode decomposition": "failure modes",
    "contrapositive predicate reading": "contrapositive quantified statement",
}
RESTATEMENT_ENV_BY_PREFIX = {
    "thm": "theorem*",
    "lem": "lemma*",
    "prop": "proposition*",
    "cor": "corollary*",
}
FORBIDDEN_DECORATION_BY_ENV = {
    "definition": {"contrapositive quantified statement", "contrapositive predicate reading"},
    "axiom": {
        "contrapositive quantified statement",
        "contrapositive predicate reading",
        "examples",
        "non-examples",
    },
    "theorem": {"examples", "non-examples"},
    "lemma": {"examples", "non-examples"},
    "proposition": {"examples", "non-examples"},
    "corollary": {"examples", "non-examples"},
}
TCOLORBOX_STYLE_BY_ENV = {
    "definition": ("defbox", "defborder"),
    "axiom": ("axiombox", "axiomborder"),
    "theorem": ("thmbox", "thmborder"),
    "lemma": ("lembox", "lemborder"),
    "proposition": ("propbox", "propborder"),
    "corollary": ("corbox", "corborder"),
}
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
PROHIBITED_PROOF_MACROS = (
    "\\flash",
    "\\Flash",
    "\\ProofStep",
    "\\Step",
    "\\proofstep",
)
PROOF_BODY_RE = re.compile(r"\\begin\{proof\}([\s\S]*?)\\end\{proof\}")
RESTATEMENT_RE = re.compile(r"\\begin\{(?P<env>theorem\*|lemma\*|proposition\*|corollary\*)\}([\s\S]*?)\\end\{(?P=env)\}")
DISPLAY_MATH_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
VOICE_BANNED_PATTERNS = {
    r"\bwe\b": "first-person plural",
    r"\bus\b": "first-person plural",
    r"\bour\b": "first-person plural",
    r"\bours\b": "first-person plural",
    r"\bourselves\b": "first-person plural",
    r"\byou\b": "direct reader address",
    r"\byour\b": "direct reader address",
    r"\byours\b": "direct reader address",
    r"\byourself\b": "direct reader address",
    r"\byourselves\b": "direct reader address",
    r"\bstudents?\b": "classroom voice",
    r"\breaders?\b": "reader-address voice",
    r"\blearners?\b": "classroom voice",
    r"\binstructors?\b": "classroom voice",
    r"\bteachers?\b": "classroom voice",
    r"\bclass(?:room)?\b": "classroom voice",
    r"\bcourse\b": "course-transcript voice",
    r"\blecture\b": "course-transcript voice",
    r"\blesson\b": "workbook voice",
    r"\bworkbook\b": "workbook voice",
    r"\bworksheet\b": "workbook voice",
    r"\bhomework\b": "workbook voice",
}


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


def latex_word_count(text: str) -> int:
    without_commands = re.sub(r"\\[A-Za-z]+(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", text)
    plain = re.sub(r"[^A-Za-z0-9]+", " ", without_commands)
    return len(plain.split())


def begins_with_section_exposition(text: str) -> re.Match[str] | None:
    body = text.lstrip()
    heading = STARRED_SUBSECTION_RE.match(body)
    if heading:
        body = body[heading.end() :].lstrip()
    return EXPOSITION_BEGIN_RE.match(body)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def tex_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.tex")
        if not any(part.startswith(".") for part in path.parts)
        and not is_ignored_path(path, root)
    )


def add(
    findings: list[Finding],
    root: Path,
    path: Path,
    code: str,
    message: str,
    line: int = 1,
    severity: str = "error",
) -> None:
    findings.append(Finding(code=code, message=message, path=rel(path, root), line=line, severity=severity))


def normalized_inputs(path: Path) -> set[str]:
    targets: set[str] = set()
    for target in ordered_inputs(path):
        targets.add(target)
        targets.add(target.removesuffix("/index"))
        targets.add(Path(target).name)
    return targets


def ordered_inputs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        match.group(1).replace("\\", "/").removesuffix(".tex")
        for match in INPUT_RE.finditer(uncommented(read(path)))
    ]


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


def latex_input_path(path: Path) -> str:
    parts = path.with_suffix("").parts
    for idx, part in enumerate(parts):
        if part.startswith("volume-"):
            return Path(*parts[idx:]).as_posix()
    return path.with_suffix("").as_posix()


def position_map(text: str, markers: list[tuple[str, str]]) -> list[tuple[str, int]]:
    positions: list[tuple[str, int]] = []
    for name, pattern in markers:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            positions.append((name, match.start()))
    return positions


def validate_order(
    chapter: Path,
    path: Path,
    text: str,
    positions: list[tuple[str, int]],
    order: list[str],
    findings: list[Finding],
    code: str,
) -> None:
    rank = {name: idx for idx, name in enumerate(order)}
    ranked = [(name, pos) for name, pos in positions if name in rank]
    for (left_name, left_pos), (right_name, right_pos) in zip(ranked, ranked[1:]):
        if rank[right_name] < rank[left_name]:
            add(
                findings,
                chapter,
                path,
                code,
                f"{right_name} appears before {left_name}; expected order is {', '.join(order)}.",
                line_at(text, right_pos),
            )


def topic_dirs(parent: Path) -> set[str]:
    if not parent.exists():
        return set()
    return {
        child.name
        for child in parent.iterdir()
        if child.is_dir()
        and not child.name.startswith(".")
        and child.name != "exercises"
        and not is_ignored_path(child)
    }


def tex_siblings(directory: Path, exclude_index: bool = True) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.glob("*.tex")
        if not (exclude_index and path.name == "index.tex")
    )


def repo_root_for_chapter(chapter: Path) -> Path:
    for parent in [chapter, *chapter.parents]:
        if (parent / "main.tex").exists() or (parent / "predicates.yaml").exists():
            return parent
    return chapter.parent


def simple_yaml_terms(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = read(path)
    terms: set[str] = set()
    for match in re.finditer(r"^\s*[-]?\s*([A-Za-z][A-Za-z0-9_-]*)\s*:", text, re.MULTILINE):
        terms.add(match.group(1).lower())
    for match in re.finditer(r"\\operatorname\{([^{}]+)\}", text):
        terms.add(match.group(1).lower())
    return terms


def canonical_terms(chapter: Path) -> set[str]:
    root = repo_root_for_chapter(chapter)
    terms: set[str] = set()
    for name in ("predicates.yaml", "relations.yaml", "notation.yaml"):
        terms |= simple_yaml_terms(root / name)
    if not terms:
        fallback = root.parent / "Learning-Real-Analysis"
        for name in ("predicates.yaml", "relations.yaml", "notation.yaml"):
            terms |= simple_yaml_terms(fallback / name)
    return terms


def all_labels(chapter: Path) -> set[str]:
    labels: set[str] = set()
    for path in tex_files(chapter):
        labels.update(LABEL_RE.findall(uncommented(read(path))))
    return labels


def validate_latex_integrity(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = uncommented(read(path))
    stack: list[tuple[str, int]] = []
    for match in re.finditer(r"\\(begin|end)\{([^{}]+)\}", text):
        kind, env = match.group(1), match.group(2)
        if kind == "begin":
            stack.append((env, match.start()))
        elif not stack:
            add(findings, chapter, path, "unmatched_environment_end", f"Unmatched \\end{{{env}}}.", line_at(text, match.start()))
        else:
            open_env, open_pos = stack.pop()
            if open_env != env:
                add(findings, chapter, path, "mismatched_environment", f"Opened {open_env} but closed {env}.", line_at(text, match.start()))
    for env, pos in stack:
        add(findings, chapter, path, "unclosed_environment", f"Unclosed environment {env}.", line_at(text, pos))
    if text.count("\\[") != text.count("\\]"):
        add(findings, chapter, path, "unbalanced_display_math", "Display math delimiters \\[ and \\] are not balanced.")
    for display in DISPLAY_MATH_RE.finditer(text):
        if CITE_OR_LABEL_RE.search(display.group(1)):
            add(findings, chapter, path, "label_or_cite_inside_display_math", "Move labels and citations outside display math.", line_at(text, display.start()))


def validate_generated_artifacts(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = read(path)
    begins = list(BEGIN_ARTIFACT_RE.finditer(text))
    ends = list(END_ARTIFACT_RE.finditer(text))
    if len(begins) != len(ends):
        add(findings, chapter, path, "generated_artifact_marker_count", "Generated artifact BEGIN/END marker counts differ.")
    for begin, end in zip(begins, ends):
        begin_label = begin.group(1)
        end_label = end.group(1)
        if begin_label != end_label:
            add(findings, chapter, path, "generated_artifact_marker_mismatch", f"Generated artifact begins as {begin_label} but ends as {end_label}.", line_at(text, begin.start()))
        body = text[begin.end() : end.start()]
        labels = LABEL_RE.findall(body)
        if ":" in begin_label and begin_label not in labels:
            add(findings, chapter, path, "generated_artifact_label_mismatch", f"Generated artifact {begin_label} does not contain a matching label.", line_at(text, begin.start()))


def validate_box_discipline(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = uncommented(read(path))
    open_boxes = [match.start() for match in re.finditer(r"\\begin\{tcolorbox\}", text)]
    close_boxes = [match.start() for match in re.finditer(r"\\end\{tcolorbox\}", text)]
    if len(open_boxes) != len(close_boxes):
        add(findings, chapter, path, "unbalanced_tcolorbox", "tcolorbox begin/end count is not balanced.")
    if len(open_boxes) > 1:
        events = sorted([(pos, 1) for pos in open_boxes] + [(pos, -1) for pos in close_boxes])
        depth = 0
        for pos, delta in events:
            depth += delta
            if depth > 1:
                add(findings, chapter, path, "nested_tcolorbox", "Nested tcolorbox environments are not allowed.", line_at(text, pos))
                break
    for boxed in re.finditer(r"\\begin\{tcolorbox\}[\s\S]*?\\end\{tcolorbox\}", text):
        body = boxed.group(0)
        if re.search(r"\\begin\{(?:remark\*?|example\*?|proof)\}", body):
            add(findings, chapter, path, "boxed_nonformal_content", "Remarks, examples, and proofs must not be boxed.", line_at(text, boxed.start()))


def validate_predicate_relation_scan(chapter: Path, path: Path, terms: set[str], findings: list[Finding]) -> None:
    if not terms:
        return
    text = uncommented(read(path))
    for match in OPERATORNAME_RE.finditer(text):
        name = match.group(1).strip()
        normalized = name.lower().replace("\\", "")
        if normalized and normalized not in terms:
            add(
                findings,
                chapter,
                path,
                "unknown_predicate_or_relation",
                f"Predicate/relation operator '{name}' is not in canonical YAML; ask for guidance because it may be acceptable.",
                line_at(text, match.start()),
                severity="warning",
            )


def validate_unique_labels(chapter: Path, findings: list[Finding]) -> None:
    seen: dict[str, Path] = {}
    for path in tex_files(chapter):
        text = uncommented(read(path))
        for match in LABEL_RE.finditer(text):
            label = match.group(1)
            if label in seen:
                add(findings, chapter, path, "duplicate_label", f"Duplicate label {label}; first seen in {rel(seen[label], chapter)}.", line_at(text, match.start()))
            else:
                seen[label] = path


def validate_chapter_registry(chapter: Path, findings: list[Finding]) -> None:
    registry = chapter.parent / "chapter.yaml"
    if not registry.exists():
        return
    text = read(registry)
    if not re.search(rf"(^|[\s:/-]){re.escape(chapter.name)}($|[\s:#,])", text):
        add(findings, chapter, registry, "chapter_missing_from_registry", "Chapter directory name is not present in the parent chapter registry.")


def note_topic_for_path(chapter: Path, path: Path) -> str | None:
    try:
        rel_parts = path.relative_to(chapter).parts
    except ValueError:
        return None
    if len(rel_parts) >= 3 and rel_parts[0] == "notes":
        return rel_parts[1]
    return None


def proof_topic_for_path(chapter: Path, path: Path) -> str | None:
    try:
        rel_parts = path.relative_to(chapter).parts
    except ValueError:
        return None
    if len(rel_parts) >= 3 and rel_parts[0] == "proofs":
        return rel_parts[1]
    return None


def validate_note_structure(chapter: Path, findings: list[Finding]) -> None:
    notes_root = chapter / "notes"
    notes_index = notes_root / "index.tex"
    formal_tokens = (
        "\\begin{definition}",
        "\\begin{theorem}",
        "\\begin{lemma}",
        "\\begin{proposition}",
        "\\begin{corollary}",
        "\\begin{axiom}",
    )
    if notes_index.exists() and any(token in uncommented(read(notes_index)) for token in formal_tokens):
        add(findings, chapter, notes_index, "notes_index_contains_formal_content", "notes/index.tex must be a router, not a formal-content file.")
    for path in tex_siblings(notes_root):
        add(findings, chapter, path, "legacy_flat_note_file", "Active note files must live under notes/{topic}/, not directly under notes/.")
    for topic in sorted(topic_dirs(notes_root)):
        topic_root = notes_root / topic
        index = topic_root / "index.tex"
        body_files = [path for path in tex_siblings(topic_root) if not path.name.startswith("figure-")]
        if not body_files:
            add(findings, chapter, topic_root, "missing_notes_topic_body", f"notes/{topic}/ must contain at least one routed note body file.")
        if index.exists():
            text = uncommented(read(index))
            if any(token in text for token in formal_tokens):
                add(findings, chapter, index, "notes_topic_index_contains_formal_content", f"notes/{topic}/index.tex must route topic files, not contain formal artifacts.")
            first_input = text.find("\\input")
            pre_inputs = text if first_input == -1 else text[:first_input]
            section_heading = SECTION_HEADING_RE.search(text)
            starred_section = STARRED_SECTION_RE.search(text)
            if starred_section:
                add(
                    findings,
                    chapter,
                    index,
                    "starred_section_router_heading",
                    "Section routers must use non-starred \\section{...} so sections appear in the table of contents.",
                    line_at(text, starred_section.start()),
                )
            if not section_heading:
                add(findings, chapter, index, "missing_section_router_heading", f"notes/{topic}/index.tex must begin routed content with \\section{{...}}.")
            elif text[: section_heading.start()].strip():
                add(
                    findings,
                    chapter,
                    index,
                    "section_router_heading_not_first",
                    "Section routers must begin with the non-starred \\section{...} heading.",
                    line_at(text, section_heading.start()),
                )
            elif first_input >= 0 and section_heading.start() > first_input:
                add(
                    findings,
                    chapter,
                    index,
                    "section_heading_after_input",
                    "Section router heading must appear before routed body inputs.",
                    line_at(text, section_heading.start()),
                )
            if UNSTARRED_SUBSECTION_RE.search(text):
                match = UNSTARRED_SUBSECTION_RE.search(text)
                if match:
                    add(
                        findings,
                        chapter,
                        index,
                        "unstarred_subsection_router_heading",
                        "Section routers must not introduce unstarred subsection headings.",
                        line_at(text, match.start()),
                    )
            if section_heading:
                prelude = pre_inputs[section_heading.end() :]
                box_matches = list(TCOLORBOX_RE.finditer(prelude))
                toolkit_matches = list(TOOLKIT_RE.finditer(prelude))
                exposition_matches = list(EXPOSITION_RE.finditer(prelude))
                if len(box_matches) != 1 or len(toolkit_matches) != 1:
                    add(
                        findings,
                        chapter,
                        index,
                        "invalid_section_toolkit_count",
                        "Section router prelude must contain exactly one Toolkit tcolorbox after the section heading.",
                        line_at(text, section_heading.start()),
                    )
                elif prelude[: toolkit_matches[0].start()].strip():
                    add(
                        findings,
                        chapter,
                        index,
                        "section_toolkit_not_immediate",
                        "The Toolkit must immediately follow the section heading in the section router.",
                        line_at(text, section_heading.end() + toolkit_matches[0].start()),
                    )
                if len(exposition_matches) != 1:
                    add(
                        findings,
                        chapter,
                        index,
                        "invalid_section_exposition_count",
                        "Section router prelude must contain exactly one short remark* block titled Exposition after the Toolkit.",
                        line_at(text, section_heading.start()),
                    )
                elif toolkit_matches:
                    toolkit_end = prelude.find("\\end{tcolorbox}", toolkit_matches[0].start())
                    if toolkit_end < 0:
                        add(findings, chapter, index, "unclosed_section_toolkit", "Section router Toolkit tcolorbox is not closed.", line_at(text, section_heading.end() + toolkit_matches[0].start()))
                    else:
                        after_toolkit = toolkit_end + len("\\end{tcolorbox}")
                        if exposition_matches[0].start() < after_toolkit:
                            add(
                                findings,
                                chapter,
                                index,
                                "section_router_order",
                                "Section router order must be section heading, Toolkit, Exposition, then routed inputs.",
                                line_at(text, section_heading.end() + exposition_matches[0].start()),
                            )
                        elif prelude[after_toolkit : exposition_matches[0].start()].strip():
                            add(
                                findings,
                                chapter,
                                index,
                                "section_exposition_not_immediate",
                                "The Exposition remark must immediately follow the Toolkit in the section router.",
                                line_at(text, section_heading.end() + exposition_matches[0].start()),
                            )
                    exposition_body = exposition_matches[0].group("body").strip()
                    if not exposition_body:
                        add(findings, chapter, index, "empty_section_exposition", "Section router Exposition must contain substantive prose.", line_at(text, section_heading.end() + exposition_matches[0].start()))
                    elif latex_word_count(exposition_body) > 100:
                        add(
                            findings,
                            chapter,
                            index,
                            "section_exposition_too_long",
                            "Section router Exposition should be brief and must not exceed 100 words.",
                            line_at(text, section_heading.end() + exposition_matches[0].start()),
                        )
            for body in body_files:
                if not is_routed(index, body, chapter):
                    add(findings, chapter, body, "unrouted_notes_topic_body", f"{rel(body, chapter)} is not routed from notes/{topic}/index.tex.")
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.tex", body.name):
                    add(findings, chapter, body, "invalid_note_filename", "Note body filename must be lowercase, hyphen-separated ASCII.", severity="warning")
                body_text = uncommented(read(body))
                unstarred_subsection = UNSTARRED_SUBSECTION_RE.search(body_text)
                if unstarred_subsection:
                    add(
                        findings,
                        chapter,
                        body,
                        "unstarred_subsection_body_heading",
                        "Topic body files must use starred subsection headings so the table of contents remains a chapter-section spine.",
                        line_at(body_text, unstarred_subsection.start()),
                    )
                body_exposition = begins_with_section_exposition(body_text)
                if body_exposition:
                    add(
                        findings,
                        chapter,
                        body,
                        "subsection_starts_with_exposition",
                        "Topic body files should not open with section-level Exposition; put the section orientation in notes/<section>/index.tex.",
                        line_at(body_text, body_exposition.start()),
                    )


def validate_index_order(chapter: Path, note_blocks: dict[str, FormalBlock], findings: list[Finding]) -> None:
    notes_index = chapter / "notes" / "index.tex"
    proofs_index = chapter / "proofs" / "index.tex"
    notes_inputs = [Path(target).name for target in ordered_inputs(notes_index)]
    proofs_inputs = [Path(target).name for target in ordered_inputs(proofs_index) if Path(target).name != "exercises"]
    if notes_inputs and proofs_inputs and notes_inputs != proofs_inputs:
        add(findings, chapter, proofs_index, "proof_topic_order_mismatch", "proofs/index.tex topic order must mirror notes/index.tex topic order.")
    proof_label_order = [
        f"prf:{block.label.split(':', 1)[1]}"
        for block in sorted(note_blocks.values(), key=lambda block: (rel(block.path, chapter), block.line))
        if block.env in PROOF_ENVS and block.label
    ]
    for topic in topic_dirs(chapter / "proofs"):
        index = chapter / "proofs" / topic / "index.tex"
        routed_roots = {Path(target).stem.removeprefix("prf-") for target in ordered_inputs(index)}
        expected = [label for label in proof_label_order if label.split(":", 1)[1] in routed_roots]
        actual = [f"prf:{Path(target).stem.removeprefix('prf-')}" for target in ordered_inputs(index)]
        if expected and actual and actual != expected:
            add(findings, chapter, index, "proof_file_order_mismatch", "Proof files must be routed in source theorem order.")


def validate_proof_structure(chapter: Path, findings: list[Finding]) -> None:
    proofs_root = chapter / "proofs"
    proofs_index = proofs_root / "index.tex"
    if proofs_index.exists():
        text = uncommented(read(proofs_index))
        if "\\begin{proof}" in text or "\\LRAProofFor{" in text:
            add(findings, chapter, proofs_index, "proofs_index_contains_proof_content", "proofs/index.tex must be a router, not a proof-content file.")
        proof_exercises = proofs_root / "exercises" / "index.tex"
        if proof_exercises.exists() and not is_routed(proofs_index, proof_exercises, chapter):
            add(findings, chapter, proofs_index, "unrouted_proof_exercises_index", "proofs/exercises/index.tex is not routed from proofs/index.tex.")
    for path in tex_siblings(proofs_root):
        add(findings, chapter, path, "legacy_flat_proof_file", "Active proof files must live under proofs/{topic}/, not directly under proofs/.")
    for topic in sorted(topic_dirs(proofs_root)):
        topic_root = proofs_root / topic
        index = topic_root / "index.tex"
        proof_files = tex_siblings(topic_root)
        if index.exists():
            text = uncommented(read(index))
            if "\\begin{proof}" in text or "\\LRAProofFor{" in text:
                add(findings, chapter, index, "proofs_topic_index_contains_proof_content", f"proofs/{topic}/index.tex must route proof files, not contain proof content.")
            for proof_file in proof_files:
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.tex", proof_file.name):
                    add(findings, chapter, proof_file, "invalid_proof_filename", "Proof filename must be lowercase, hyphen-separated ASCII.")
                if not is_routed(index, proof_file, chapter):
                    add(findings, chapter, proof_file, "unrouted_proof_topic_file", f"{rel(proof_file, chapter)} is not routed from proofs/{topic}/index.tex.")


def generate_capstone_stub(chapter: Path, findings: list[Finding]) -> None:
    proof_exercises = chapter / "proofs" / "exercises"
    capstone = proof_exercises / f"capstone-{chapter.name}.tex"
    index = proof_exercises / "index.tex"
    proof_exercises.mkdir(parents=True, exist_ok=True)
    if not index.exists():
        index.write_text(
            "% Exercise proofs: generated by validate_chapter_house_rules.py\n"
            f"\\input{{{latex_input_path(capstone)}}}\n",
            encoding="utf-8",
        )
    elif latex_input_path(capstone) not in ordered_inputs(index):
        text = read(index).rstrip()
        index.write_text(f"{text}\n\\input{{{latex_input_path(capstone)}}}\n", encoding="utf-8")
    if not capstone.exists():
        title = chapter.name.replace("-", " ").title()
        capstone.write_text(
            "% =========================================================\n"
            f"% Capstone Exercise: {title}\n"
            "% =========================================================\n"
            "% Status: Planned\n"
            f"% Dependency ceiling: all environments in {chapter.name}/chapter.yaml\n"
            "% =========================================================\n\n"
            "\\newpage\n"
            "\\phantomsection\n"
            f"\\label{{cap:{chapter.name}}}\n\n"
            "\\begin{tcolorbox}[\n"
            "  colback=gray!6,\n"
            "  colframe=gray!40,\n"
            "  arc=2pt,\n"
            "  left=8pt, right=8pt, top=6pt, bottom=6pt,\n"
            f"  title={{\\small\\textbf{{Capstone -- {title}}}}},\n"
            "  fonttitle=\\small\\bfseries\n"
            "]\n"
            "\\textbf{Status: Planned.}\n\n"
            "This capstone is a placeholder for one synthesis problem using only\n"
            "material from this chapter and its prerequisites.\n\n"
            "\\medskip\n\n"
            "\\textbf{Problem (Draft).}\n"
            "TODO: Replace this placeholder with exactly one chapter-synthesis problem.\n"
            "\\end{tcolorbox}\n\n"
            "\\begin{remark*}[Dependency ceiling]\n"
            "This capstone may use results from this chapter and earlier prerequisite\n"
            "chapters only. It must not invoke later chapter material.\n"
            "\\end{remark*}\n",
            encoding="utf-8",
        )
def validate_chapter_layout(chapter: Path, findings: list[Finding], generate_missing_capstone: bool = False, require_roadmap: bool = False) -> None:
    for relative in ("index.tex", "chapter.yaml", "notes/index.tex", "proofs/index.tex", "proofs/exercises/index.tex"):
        path = chapter / relative
        if not path.exists():
            add(findings, chapter, path, "missing_chapter_artifact", f"Missing {relative}.")
    for relative in ("notes", "proofs", "proofs/exercises"):
        path = chapter / relative
        if not path.is_dir():
            add(findings, chapter, path, "missing_chapter_directory", f"Missing {relative}/.")

    standard_capstone = chapter / "proofs" / "exercises" / f"capstone-{chapter.name}.tex"
    legacy_capstone = chapter / "capstone.tex"
    if not standard_capstone.exists():
        if generate_missing_capstone:
            generate_capstone_stub(chapter, findings)
        else:
            add(findings, chapter, standard_capstone, "missing_capstone", "Missing standard capstone artifact.")
    if legacy_capstone.exists() and not standard_capstone.exists():
        add(findings, chapter, legacy_capstone, "nonstandard_capstone_location", "Capstone must use proofs/exercises/capstone-{chapter}.tex.")

    chapter_index = chapter / "index.tex"
    if chapter_index.exists():
        chapter_text = uncommented(read(chapter_index))
        starred_chapter = STARRED_CHAPTER_RE.search(chapter_text)
        if starred_chapter:
            add(
                findings,
                chapter,
                chapter_index,
                "starred_chapter_heading",
                "Chapter routers must use non-starred \\chapter{...}; chapters must appear in the table of contents.",
                line_at(chapter_text, starred_chapter.start()),
            )
        if "\\chapter" not in chapter_text:
            add(findings, chapter, chapter_index, "missing_chapter_heading", "Missing chapter heading.")
        if "\\label{ch:" not in chapter_text and "\\label{chap:" not in chapter_text:
            add(findings, chapter, chapter_index, "missing_chapter_label", "Missing chapter label.")
        validate_order(
            chapter,
            chapter_index,
            chapter_text,
            position_map(
                chapter_text,
                [
                    ("chapter", r"\\chapter"),
                    ("chapter_label", r"\\label\{(?:ch|chap):"),
                    ("breadcrumb", r"\\breadcrumb\{"),
                    ("notes_input", r"\\input\{[^{}]*/notes/index(?:\.tex)?\}"),
                    ("proofs_input", r"\\LRAProofsInput\{[^{}]*/proofs/index(?:\.tex)?\}"),
                    ("capstone_heading", r"\\section\*\{Capstone\}"),
                    ("capstone_input", r"\\LRAExercisesInput\{[^{}]*/proofs/exercises/index(?:\.tex)?\}"),
                ],
            ),
            STRUCTURAL_ORDER["chapter"],
            findings,
            "chapter_structure_order",
        )
        first_input = chapter_text.find("\\input")
        pre_inputs = chapter_text if first_input == -1 else chapter_text[:first_input]
        breadcrumb_matches = list(re.finditer(r"\\breadcrumb\{", pre_inputs))
        if not breadcrumb_matches:
            add(findings, chapter, chapter_index, "missing_breadcrumb", "Chapter index must contain a \\breadcrumb{...} macro before routed inputs.")
        elif len(breadcrumb_matches) > 1:
            add(findings, chapter, chapter_index, "invalid_breadcrumb_count", "Chapter index must contain exactly one \\breadcrumb{...} before routed inputs.", line_at(chapter_text, breadcrumb_matches[1].start()))
        if require_roadmap and not re.search(r"Roadmap|roadmap", pre_inputs):
            add(findings, chapter, chapter_index, "missing_retired_roadmap", "Legacy roadmap requirement is disabled by default.")
        for relative in ("notes/index.tex", "proofs/index.tex", "proofs/exercises/index.tex"):
            if (chapter / relative).exists() and not is_routed(chapter_index, chapter / relative, chapter):
                add(findings, chapter, chapter_index, "unrouted_chapter_index", f"{relative} is not routed from chapter index.")

    notes_topics = topic_dirs(chapter / "notes")
    proofs_topics = topic_dirs(chapter / "proofs")
    for topic in sorted((notes_topics - proofs_topics) - NOTE_ONLY_TOPICS):
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

    proof_exercises_index = chapter / "proofs" / "exercises" / "index.tex"
    if proof_exercises_index.exists() and not is_routed(chapter / "proofs" / "index.tex", proof_exercises_index, chapter):
        add(findings, chapter, proof_exercises_index, "unrouted_proof_exercises_index", "proofs/exercises/index.tex is not routed from proofs/index.tex.")


def validate_toolkits(chapter: Path, findings: list[Finding]) -> None:
    notes_root = chapter / "notes"
    for path in tex_files(notes_root) if notes_root.exists() else []:
        if path.name == "index.tex":
            continue
        text = uncommented(read(path))
        toolkit = TOOLKIT_RE.search(text)
        if toolkit:
            add(
                findings,
                chapter,
                path,
                "toolkit_in_topic_body",
                "Toolkit boxes belong in notes/<section>/index.tex, not subsection/topic body files.",
                line_at(text, toolkit.start()),
            )


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


def validate_formal_tcolorbox_styles(chapter: Path, path: Path, findings: list[Finding]) -> None:
    text = uncommented(read(path))
    for match in TCOLORBOX_FORMAL_RE.finditer(text):
        env = match.group("env").lower()
        expected = TCOLORBOX_STYLE_BY_ENV.get(env)
        options = match.group("options") or ""
        back_match = re.search(r"colback\s*=\s*([A-Za-z0-9!]+)", options)
        frame_match = re.search(r"colframe\s*=\s*([A-Za-z0-9!]+)", options)
        actual_back = back_match.group(1) if back_match else None
        actual_frame = frame_match.group(1) if frame_match else None
        if expected:
            expected_back, expected_frame = expected
            if actual_back != expected_back or actual_frame != expected_frame:
                actual = f"colback={actual_back or '<missing>'}, colframe={actual_frame or '<missing>'}"
                expected_text = f"colback={expected_back}, colframe={expected_frame}"
                add(
                    findings,
                    chapter,
                    path,
                    "formal_box_style_mismatch",
                    f"{env} tcolorbox must use {expected_text}; found {actual}.",
                    line_at(text, match.start()),
                )
        add(
            findings,
            chapter,
            path,
            "raw_formal_tcolorbox",
            f"Use \\begin{{{env}box}}{{...}} around {env} instead of a raw formal tcolorbox.",
            line_at(text, match.start()),
        )
    for match in FORMAL_BOX_RE.finditer(text):
        wrapper = match.group("wrapper").lower()
        env = match.group("env").lower()
        expected_env = FORMAL_BOX_ENVS[wrapper]
        if env != expected_env:
            add(
                findings,
                chapter,
                path,
                "formal_box_environment_mismatch",
                f"{wrapper} must wrap {expected_env}, not {env}.",
                line_at(text, match.start()),
            )


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


def voice_text(body: str) -> str:
    text = re.sub(r"\\(?:label|hyperref|ref|citep?|url|href)\b(?:\[[^\]]*\])?(?:\{[^{}]*\}){0,2}", " ", body)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$^_\\]", " ", text)
    return re.sub(r"\s+", " ", text)


def validate_voice(chapter: Path, path: Path, findings: list[Finding]) -> None:
    if path.name.startswith("figure-"):
        return
    text = uncommented(read(path))
    for block in VOICE_BLOCK_RE.finditer(text):
        block_text = voice_text(block.group("body"))
        for pattern, reason in VOICE_BANNED_PATTERNS.items():
            match = re.search(pattern, block_text, re.IGNORECASE)
            if match:
                title = (block.group("title") or block.group("env")).strip()
                add(
                    findings,
                    chapter,
                    path,
                    "non_reference_voice",
                    f"{title} block uses {reason}: '{match.group(0)}'. Use impersonal reference voice.",
                    line_at(text, block.start("body")),
                )


def dependency_bodies(decoration: str) -> list[str]:
    return re.findall(r"\\begin\{dependencies\}(.*?)\\end\{dependencies\}", decoration, re.DOTALL)


def decoration_key(match: re.Match[str]) -> str:
    env = match.group("env").lower()
    if env == "dependencies":
        return "dependencies"
    title = (match.group("title") or "").strip().lower()
    return re.sub(r"\s+", " ", title)


def validate_formal_blocks(chapter: Path, blocks: list[FormalBlock], findings: list[Finding]) -> dict[str, FormalBlock]:
    by_label: dict[str, FormalBlock] = {}
    for block in blocks:
        if not block.label:
            add(findings, chapter, block.path, "missing_formal_label", f"{block.env} has no label.", block.line)
            continue
        by_label[block.label] = block
        if block.env in {"definition", "axiom"}:
            source = uncommented(read(block.path))
            block_start = source.find(block.text)
            wrapper_context = source[max(0, block_start - 500) : block_start] if block_start >= 0 else ""
            expected_wrapper = next((box for box, env in FORMAL_BOX_ENVS.items() if env == block.env), "")
            if f"\\begin{{{expected_wrapper}}}" not in wrapper_context:
                add(findings, chapter, block.path, "missing_required_box", f"{block.label} must be wrapped in {expected_wrapper} by artifact-matrix box rules.", block.line)
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
        if re.search(r"\\begin\{remark\*\}\[(Historical note|Comparison with Feferman)\]", block.decoration) and not re.search(r"\\cite[t|p]?\{", block.decoration):
            add(findings, chapter, block.path, "source_crosswalk_without_citation", f"{block.label} has a source/provenance block without a citation.", block.line)
        for examples in re.finditer(r"\\begin\{remark\*\}\[(Examples|Non-Examples|Exposition)\]([\s\S]*?)\\end\{remark\*\}", block.decoration):
            body = examples.group(2)
            if LABEL_RE.search(body) or re.search(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}", body):
                add(findings, chapter, block.path, "formal_claim_inside_expository_block", f"{examples.group(1)} block must not introduce labels or formal theorem-like environments.", block.line + line_at(block.decoration, examples.start()) - 1)
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
        seen_blocks: list[tuple[str, int, int]] = []
        for match in DECORATION_BLOCK_RE.finditer(block.decoration):
            key = decoration_key(match)
            if key not in DECORATION_ORDER:
                add(findings, chapter, block.path, "unknown_decoration_block", f"{block.label} has nonstandard decoration block '{key}'.", block.line + line_at(block.decoration, match.start()) - 1)
                continue
            if key in FORBIDDEN_DECORATION_BY_ENV.get(block.env, set()):
                add(findings, chapter, block.path, "forbidden_decoration_block", f"{block.env} must not use decoration block '{key}' by artifact-matrix rules.", block.line + line_at(block.decoration, match.start()) - 1)
            seen_blocks.append((key, DECORATION_ORDER[key], match.start()))
        seen_keys = {key for key, _, _ in seen_blocks}
        for child, parent in DEPENDENT_DECORATION_PARENTS.items():
            if child in seen_keys and parent not in seen_keys:
                add(findings, chapter, block.path, "missing_dependent_parent_block", f"{child} requires parent block {parent} for {block.label}.", block.line)
        for (left_key, left_rank, _), (right_key, right_rank, right_pos) in zip(seen_blocks, seen_blocks[1:]):
            if right_rank < left_rank:
                add(
                    findings,
                    chapter,
                    block.path,
                    "decoration_order",
                    f"{right_key} appears before {left_key} for {block.label}; use the canonical decoration order.",
                    block.line + line_at(block.decoration, right_pos) - 1,
                )
    return by_label


def validate_dependency_targets(chapter: Path, findings: list[Finding]) -> None:
    labels = all_labels(chapter)
    for path in tex_files(chapter):
        text = uncommented(read(path))
        for dep in re.finditer(r"\\begin\{dependencies\}([\s\S]*?)\\end\{dependencies\}", text):
            for target in HYPERREF_RE.findall(dep.group(1)):
                if target.split(":", 1)[0] not in DEPENDENCY_PREFIXES:
                    continue
                if target not in labels:
                    add(
                        findings,
                        chapter,
                        path,
                        "dependency_target_not_in_chapter",
                        f"Dependency target {target} is not defined in this chapter; verify prior-scope dependency or add the missing artifact.",
                        line_at(text, dep.start()),
                        severity="warning",
                    )


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
        proof_label_matches = list(re.finditer(r"\\label\{prf:([^{}]+)\}", text))
        proof_for_matches = list(PROOF_FOR_RE.finditer(text))
        if len(proof_label_matches) != 1:
            add(findings, chapter, path, "invalid_proof_label_count", "Proof file must contain exactly one proof-level prf: label.")
        if len(proof_for_matches) != 1:
            add(findings, chapter, path, "invalid_lra_proof_for_count", "Proof file must contain exactly one \\LRAProofFor{...} association.")
        for macro in PROHIBITED_PROOF_MACROS:
            if macro in text:
                add(findings, chapter, path, "prohibited_proof_macro", f"Proof file uses prohibited proof-structuring macro {macro}.")
        first_env = re.search(r"\\begin\{", text)
        proof_label_match = proof_label_matches[0] if proof_label_matches else None
        proof_for_match = proof_for_matches[0] if proof_for_matches else None
        if proof_label_match and first_env and proof_label_match.start() > first_env.start():
            add(findings, chapter, path, "proof_label_after_environment", "Proof label must appear outside and before all environments.", line_at(text, proof_label_match.start()))
        if proof_label_match and proof_for_match and proof_label_match.start() > proof_for_match.start():
            add(findings, chapter, path, "proof_label_after_proof_for", "Proof label must appear before \\LRAProofFor{...}.", line_at(text, proof_label_match.start()))
        restatement_matches = list(RESTATEMENT_RE.finditer(text))
        for env_match in restatement_matches:
            if LABEL_RE.search(env_match.group(2)):
                add(findings, chapter, path, "label_inside_restatement", "Starred theorem-like restatement must not contain labels.", line_at(text, env_match.start()))
        proof_env_matches = list(PROOF_BODY_RE.finditer(text))
        for proof_match in proof_env_matches:
            if LABEL_RE.search(proof_match.group(1)):
                add(findings, chapter, path, "label_inside_proof_environment", "Proof environments must not contain labels.", line_at(text, proof_match.start()))
        if proof_label_match and proof_for_match:
            proof_root = proof_label_match.group(1)
            proof_for_label = proof_for_match.group(1)
            if ":" in proof_for_label and proof_root != proof_for_label.split(":", 1)[1]:
                add(findings, chapter, path, "proof_label_mismatch", "Proof label root must match the associated theorem-like label root.", line_at(text, proof_label_match.start()))
            note_block = note_blocks.get(proof_for_label)
            if note_block:
                note_topic = note_topic_for_path(chapter, note_block.path)
                proof_topic = proof_topic_for_path(chapter, path)
                if note_topic and proof_topic and note_topic != proof_topic:
                    add(findings, chapter, path, "proof_topic_mismatch", f"Proof topic {proof_topic} does not match source note topic {note_topic}.")
            proof_for_prefix = proof_for_label.split(":", 1)[0] if ":" in proof_for_label else ""
            expected_env = RESTATEMENT_ENV_BY_PREFIX.get(proof_for_prefix)
            if expected_env and restatement_matches and restatement_matches[0].group("env") != expected_env:
                add(findings, chapter, path, "restatement_type_mismatch", f"Proof restatement must use {expected_env} for {proof_for_label}.", line_at(text, restatement_matches[0].start()))
        if proof_for_match and "\\begin{remark*}[Return]" in text:
            expected_ref = proof_for_match.group(1)
            return_start = text.find("\\begin{remark*}[Return]")
            return_end = text.find("\\end{remark*}", return_start)
            return_block = text[return_start:return_end] if return_end >= 0 else text[return_start:]
            if expected_ref not in HYPERREF_RE.findall(return_block):
                add(findings, chapter, path, "return_navigation_mismatch", "Return navigation must hyperref to the associated source label.", line_at(text, return_start))
        dep_bodies = dependency_bodies(text)
        if dep_bodies:
            for dep_body in dep_bodies:
                if "\\NoLocalDependencies" in dep_body:
                    continue
                refs = HYPERREF_RE.findall(dep_body)
                if not refs:
                    add(findings, chapter, path, "proof_dependencies_without_hyperref", "Proof dependencies must contain hyperref links or \\NoLocalDependencies.")
                for target in refs:
                    if target.split(":", 1)[0] not in DEPENDENCY_PREFIXES:
                        add(findings, chapter, path, "invalid_proof_dependency_target", f"Proof dependency targets non-statement label {target}.")
        clearpage_pos = text.rfind("\\clearpage")
        if clearpage_pos >= 0:
            trailer = "\n".join(line.strip() for line in text[clearpage_pos + len("\\clearpage") :].splitlines() if line.strip() and not line.strip().startswith("%"))
            if trailer:
                add(findings, chapter, path, "content_after_clearpage", "Proof file must not contain source content after terminal \\clearpage.", line_at(text, clearpage_pos))
        if proof_label_match:
            expected_name = f"prf-{proof_label_match.group(1)}.tex"
            if path.name != expected_name:
                add(findings, chapter, path, "proof_filename_label_mismatch", f"Proof filename must be {expected_name}.")
        validate_order(
            chapter,
            path,
            text,
            position_map(
                text,
                [
                    ("newpage", r"\\newpage"),
                    ("phantomsection", r"\\phantomsection"),
                    ("proof_label", r"\\label\{prf:"),
                    ("proof_for", r"\\LRAProofFor\{"),
                    ("return", r"\\begin\{remark\*\}\[Return\]"),
                    ("proof_vault", r"\\ProofVaultURL\{"),
                    ("restatement", r"\\begin\{(?:theorem|lemma|proposition|corollary)\*\}"),
                    ("professional", r"Professional Standard Proof"),
                    ("detailed", r"Detailed (?:Learning|Instructional) Proof"),
                    ("proof_structure", r"\\begin\{remark\*\}\[Proof structure\]"),
                    ("dependencies", r"\\begin\{dependencies\}"),
                    ("clearpage", r"\\clearpage"),
                ],
            ),
            STRUCTURAL_ORDER["proof"],
            findings,
            "proof_structure_order",
        )
        for token, code in [
            ("\\newpage", "missing_proof_newpage"),
            ("\\phantomsection", "missing_proof_phantomsection"),
            ("\\LRAProofFor{", "missing_lra_proof_for"),
            ("\\begin{remark*}[Return]", "missing_return_navigation"),
            ("Professional Standard Proof", "missing_professional_proof_layer"),
            ("\\begin{remark*}[Proof structure]", "missing_proof_structure"),
            ("\\begin{dependencies}", "missing_proof_dependencies"),
            ("\\clearpage", "missing_proof_clearpage"),
        ]:
            if token not in text:
                add(findings, chapter, path, code, f"Proof file missing {token}.")
        if not re.search(r"Detailed (?:Learning|Instructional) Proof", text, re.IGNORECASE):
            add(findings, chapter, path, "missing_detailed_learning_layer", "Proof file missing Detailed Learning/Instructional Proof.")
        if not re.search(r"\\begin\{(?:theorem|lemma|proposition|corollary)\*\}", text):
            add(findings, chapter, path, "missing_restatement", "Proof file missing starred theorem-like restatement.")
        if len(restatement_matches) != 1:
            add(findings, chapter, path, "invalid_restatement_count", "Proof file must contain exactly one starred theorem-like restatement.")
        professional_markers = [match for match in proof_env_matches if re.search(r"\\textbf\{Professional Standard Proof\.?\}", match.group(1), re.IGNORECASE)]
        detailed_markers = [
            match
            for match in proof_env_matches
            if re.search(r"\\textbf\{Detailed (?:Learning|Instructional) Proof\.?\}", match.group(1), re.IGNORECASE)
        ]
        if len(professional_markers) != 1:
            add(findings, chapter, path, "invalid_professional_proof_layer_count", "Proof file must contain exactly one Professional Standard Proof layer.")
        if len(detailed_markers) != 1:
            add(findings, chapter, path, "invalid_detailed_learning_layer_count", "Proof file must contain exactly one Detailed Learning/Instructional Proof layer.")
        if professional_markers and detailed_markers and professional_markers[0].start() > detailed_markers[0].start():
            add(findings, chapter, path, "proof_layer_order", "Professional proof layer must precede detailed instructional proof layer.", line_at(text, detailed_markers[0].start()))
        todo_matches = list(re.finditer(r"\bTODO\b", text, re.IGNORECASE))
        if todo_matches:
            allowed_spans: list[tuple[int, int]] = []
            allowed_spans.extend((match.start(), match.end()) for match in proof_env_matches)
            for match in re.finditer(r"\\begin\{remark\*\}\[Proof structure\]([\s\S]*?)\\end\{remark\*\}", text):
                allowed_spans.append((match.start(), match.end()))
            for match in re.finditer(r"\\begin\{dependencies\}([\s\S]*?)\\end\{dependencies\}", text):
                allowed_spans.append((match.start(), match.end()))
            for match in todo_matches:
                if not any(start <= match.start() <= end for start, end in allowed_spans):
                    add(findings, chapter, path, "todo_outside_stub_layers", "Proof stubs may use TODO only in proof bodies, proof-structure, or dependencies.", line_at(text, match.start()))
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
        ledger = exercises / "exercise-ledger.yaml"
        ledger_text = read(ledger) if ledger.exists() else ""
        ledger_paths = [
            match.group(1).strip()
            for match in re.finditer(r"^\s*path:\s*([^#\n]+)", ledger_text, re.MULTILINE)
        ]
        for ledger_path in ledger_paths:
            target = exercises / ledger_path.replace("/", "\\")
            if not target.exists():
                add(findings, chapter, ledger, "ledger_path_missing", f"Exercise ledger path does not exist: {ledger_path}.")
        for path in tex_files(exercises):
            if path.name == "index.tex":
                continue
            text = uncommented(read(path))
            if path.parent == exercises:
                add(findings, chapter, path, "flat_exercise_file", "Exercise set files should live under exercises/{topic}/ routing folders unless explicitly generated from a registry.")
            if "\\label{ex:" not in text:
                add(findings, chapter, path, "missing_exercise_label", "Exercise file has no ex: label.")
            if not EXERCISE_ENV_RE.search(text):
                add(findings, chapter, path, "missing_exercise_environment", "Exercise file must use the house exercise environment or macro.")
            if not is_routed(exercises / "index.tex", path, chapter):
                add(findings, chapter, path, "unrouted_exercise_file", "Exercise file is not routed from exercises/index.tex.")
            if ledger.exists():
                exercise_ids = LABEL_RE.findall(text)
                for exercise_id in exercise_ids:
                    if exercise_id.startswith("ex:") and exercise_id not in ledger_text:
                        add(findings, chapter, path, "exercise_label_missing_from_ledger", f"Exercise label {exercise_id} is not present in exercise-ledger.yaml.", severity="warning")
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


def validate_capstone(chapter: Path, findings: list[Finding]) -> None:
    capstone = chapter / "proofs" / "exercises" / f"capstone-{chapter.name}.tex"
    proof_index = chapter / "proofs" / "exercises" / "index.tex"
    if not capstone.exists():
        return
    text = uncommented(read(capstone))
    validate_order(
        chapter,
        capstone,
        text,
        position_map(
            text,
            [
                ("newpage", r"\\newpage"),
                ("phantomsection", r"\\phantomsection"),
                ("capstone_label", r"\\label\{cap:"),
                ("capstone_box", r"\\begin\{tcolorbox\}"),
                ("dependency_ceiling", r"\\begin\{remark\*\}\[Dependency ceiling\]"),
            ],
        ),
        STRUCTURAL_ORDER["capstone"],
        findings,
        "capstone_structure_order",
    )
    for token, code in [
        ("\\newpage", "missing_capstone_newpage"),
        ("\\phantomsection", "missing_capstone_phantomsection"),
        (f"\\label{{cap:{chapter.name}}}", "missing_capstone_label"),
        ("\\begin{tcolorbox}", "missing_capstone_box"),
        ("Problem", "missing_capstone_problem"),
        ("\\begin{remark*}[Dependency ceiling]", "missing_capstone_dependency_ceiling"),
    ]:
        if token not in text:
            add(findings, chapter, capstone, code, f"Capstone missing {token}.")
    if len(TCOLORBOX_RE.findall(text)) != 1:
        add(findings, chapter, capstone, "invalid_capstone_box_count", "Capstone must contain exactly one problem tcolorbox.")
    if proof_index.exists():
        inputs = ordered_inputs(proof_index)
        expected = latex_input_path(capstone)
        if expected not in inputs:
            add(findings, chapter, proof_index, "unrouted_capstone", "Standard capstone is not routed from proofs/exercises/index.tex.")
        elif inputs[-1] != expected:
            add(findings, chapter, proof_index, "capstone_not_last", "Capstone must be the last input in proofs/exercises/index.tex.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one chapter against LRA house rules.")
    parser.add_argument("--chapter", required=True, type=Path, help="Chapter root, e.g. volume-i/propositional-logic.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--generate-missing-capstone",
        action="store_true",
        help="Create a planned standard capstone stub when proofs/exercises/capstone-{chapter}.tex is missing.",
    )
    parser.add_argument(
        "--require-roadmap",
        action="store_true",
        help="Legacy compatibility only: require a roadmap in the chapter index.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chapter = args.chapter.resolve()
    findings: list[Finding] = []
    if not chapter.exists():
        findings.append(Finding("missing_chapter", "Chapter path does not exist.", str(chapter)))
    else:
        terms = canonical_terms(chapter)
        validate_chapter_registry(chapter, findings)
        validate_chapter_layout(chapter, findings, generate_missing_capstone=args.generate_missing_capstone, require_roadmap=args.require_roadmap)
        validate_unique_labels(chapter, findings)
        for path in tex_files(chapter):
            validate_latex_integrity(chapter, path, findings)
            validate_generated_artifacts(chapter, path, findings)
            validate_box_discipline(chapter, path, findings)
            validate_formal_tcolorbox_styles(chapter, path, findings)
            validate_block_discipline(chapter, path, findings)
            validate_figures(chapter, path, findings)
            validate_labels(chapter, path, findings)
            validate_voice(chapter, path, findings)
            validate_predicate_relation_scan(chapter, path, terms, findings)
        validate_note_structure(chapter, findings)
        validate_proof_structure(chapter, findings)
        validate_toolkits(chapter, findings)
        note_blocks = validate_formal_blocks(chapter, extract_formal_blocks(chapter), findings)
        validate_index_order(chapter, note_blocks, findings)
        validate_dependency_targets(chapter, findings)
        validate_proofs(chapter, note_blocks, findings)
        validate_exercises(chapter, findings)
        validate_capstone(chapter, findings)

    error_count = sum(1 for finding in findings if finding.severity == "error")
    warning_count = sum(1 for finding in findings if finding.severity == "warning")
    summary = {
        "chapter": str(chapter),
        "status": "FAIL" if error_count else "PASS",
        "error_count": error_count,
        "warning_count": warning_count,
        "findings": [asdict(finding) for finding in findings],
    }
    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print("Chapter house-rule validation summary")
        print(f"chapter: {chapter}")
        print(f"error_count: {error_count}")
        print(f"warning_count: {warning_count}")
        print(f"status: {summary['status']}")
        for finding in findings:
            print(f"{finding.severity.upper()} {finding.code} {finding.path}:{finding.line} - {finding.message}")
    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
