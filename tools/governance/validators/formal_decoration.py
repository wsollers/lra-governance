from __future__ import annotations

import re
from pathlib import Path

from core.formal_blocks import formal_blocks_for_file
from core.finding import Finding, finding
from core.tex import read_stripped_text
from core.file_inventory import validator_files
from formal_reading import count_quantified_binders, has_formal_reading, has_predicate_reading, standard_quantified_statement_bodies


LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
PROOF_HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>prf:[^\]]+)\]", re.IGNORECASE)
DECORATION_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|dependencies)\}(?:\[(?P<title>[^\]]+)\])?",
    re.IGNORECASE,
)
EXPOSITORY_BLOCK_RE = re.compile(
    r"\\begin\{remark\*\}\[(Examples|Non-Examples|Exposition)\]([\s\S]*?)\\end\{remark\*\}",
    re.IGNORECASE,
)
FORMAL_INNER_RE = re.compile(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}", re.IGNORECASE)
CITATION_RE = re.compile(r"\\cite(?:t|p)?\{")
SOURCE_CROSSWALK_RE = re.compile(
    r"\\begin\{remark\*\}\[(?P<title>Historical note|Source comparison)\]"
    r"(?P<body>[\s\S]*?)"
    r"\\end\{remark\*\}",
    re.IGNORECASE,
)
FORMAL_BOX_RE = re.compile(
    r"\\begin\{(?P<env>definitionbox|definitionalbox|axiombox|theorembox|lemmabox|propositionbox|corollarybox)\}"
    r"(?:\{[^{}]*\})?"
    r"(?P<body>[\s\S]*?)"
    r"\\end\{(?P=env)\}",
    re.IGNORECASE,
)
DECORATION_INSIDE_FORMAL_RE = re.compile(
    r"\\begin\{(?:remark\*|example\*|dependencies)\}"
    r"|\\textbf\{(?:"
    r"Standard quantified statement|"
    r"Predicate reading|"
    r"Negated quantified statement|"
    r"Negation predicate reading|"
    r"Failure modes|"
    r"Contrapositive quantified statement|Contrapositive predicate reading|"
    r"Interpretation|Exposition|Examples|Non-Examples|Dependencies"
    r")\.?\}",
    re.IGNORECASE,
)

DECORATION_ORDER = {
    "proof_link": 10,
    "standard quantified statement": 20,
    "predicate reading": 30,
    "negated quantified statement": 40,
    "negation predicate reading": 50,
    "failure modes": 60,
    "contrapositive quantified statement": 70,
    "contrapositive predicate reading": 80,
    "interpretation": 100,
    "notation": 102,
    "historical note": 105,
    "source comparison": 105,
    "exposition": 110,
    "examples": 120,
    "non-examples": 130,
    "dependencies": 140,
}
DEPENDENT_DECORATION_PARENTS = {
    "negation predicate reading": "negated quantified statement",
    "contrapositive predicate reading": "contrapositive quantified statement",
}
FAILURE_MODE_DECOMPOSITION_TRIGGERS = {
    "negated quantified statement",
    "negation predicate reading",
    "contrapositive quantified statement",
    "contrapositive predicate reading",
}
REPEATABLE_DECORATION_BLOCKS = {"failure modes", "exposition", "examples", "non-examples"}
FORBIDDEN_DECORATION_BY_ENV = {
    "definition": {"contrapositive quantified statement", "contrapositive predicate reading"},
    "axiom": {"contrapositive quantified statement", "contrapositive predicate reading", "examples", "non-examples"},
    "theorem": {"examples", "non-examples"},
    "lemma": {"examples", "non-examples"},
    "proposition": {"examples", "non-examples"},
    "corollary": {"examples", "non-examples"},
}


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        rel = tex.resolve().relative_to(volume_root.resolve()).as_posix()
        if "/notes/" not in f"/{rel}":
            continue
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    text = read_stripped_text(path)
    _check_decoration_inside_formal_blocks(volume_root, path, text, findings)
    for block in formal_blocks_for_file(path):
        block_text = block.body
        label = block.label or _first_label(block_text)
        if not label:
            continue
        env = block.env
        line = block.line
        decoration = text[block.end:block.next_boundary]
        _check_proof_navigation(volume_root, path, block_text, label, env, line, findings)
        _check_source_citations(volume_root, path, decoration, label, line, findings)
        _check_expository_formal_claims(volume_root, path, decoration, label, line, findings)
        _check_decoration_blocks(volume_root, path, decoration, label, env, line, findings)


def _check_decoration_inside_formal_blocks(
    volume_root: Path,
    path: Path,
    text: str,
    findings: list[Finding],
) -> None:
    for block in formal_blocks_for_file(path):
        _check_decoration_inside_span(
            volume_root,
            path,
            text,
            block.begin,
            block.end,
            block.env,
            findings,
        )
    for match in FORMAL_BOX_RE.finditer(text):
        _check_decoration_inside_span(
            volume_root,
            path,
            text,
            match.start(),
            match.end(),
            match.group("env").lower(),
            findings,
        )


def _check_decoration_inside_span(
    volume_root: Path,
    path: Path,
    text: str,
    start: int,
    end: int,
    env: str,
    findings: list[Finding],
) -> None:
    body = text[start:end]
    match = DECORATION_INSIDE_FORMAL_RE.search(body)
    if not match:
        return
    findings.append(
        finding(
            "decoration_block_inside_formal_block",
            f"{env} contains a decoration/support block; close the formal block before quantified, predicate, negation, failure-mode, interpretation, example, or dependency blocks.",
            path,
            volume_root,
            _line_at(text, start + match.start()),
        )
    )


def _check_proof_navigation(
    volume_root: Path,
    path: Path,
    block_text: str,
    label: str,
    env: str,
    line: int,
    findings: list[Finding],
) -> None:
    if env not in {"theorem", "lemma", "proposition", "corollary"}:
        return
    if ":" not in label:
        return
    expected = f"prf:{label.split(':', 1)[1]}"
    links = [
        link
        for link in PROOF_HYPERREF_RE.finditer(block_text)
        if "go to proof" in block_text[link.end():link.end() + 160].lower()
    ]
    if not links:
        findings.append(
            finding(
                "missing_go_to_proof_link",
                f"{label} must contain \\hyperref[{expected}]{{\\textit{{Go to proof.}}}} inside the {env} body.",
                path,
                volume_root,
                line,
            )
        )
        return
    if any(link.group("label") == expected for link in links):
        return
    actual = ", ".join(link.group("label") for link in links)
    findings.append(
        finding(
            "wrong_go_to_proof_target",
            f"{label} proof navigation must target {expected}; found {actual}.",
            path,
            volume_root,
            line,
        )
    )


def _check_source_citations(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    line: int,
    findings: list[Finding],
) -> None:
    for match in SOURCE_CROSSWALK_RE.finditer(decoration):
        title = match.group("title")
        body = match.group("body")
        block_line = line + _line_at(decoration, match.start()) - 1
        if not CITATION_RE.search(body):
            findings.append(
                finding(
                    "source_crosswalk_without_citation",
                    f"{label} has a source/provenance block without a citation.",
                    path,
                    volume_root,
                    block_line,
                )
            )
            continue
        if title.lower() == "source comparison" and not _ends_with_citation(body):
            findings.append(
                finding(
                    "source_comparison_citation_not_at_bottom",
                    f"{label} Source comparison block must end with a citation command.",
                    path,
                    volume_root,
                    block_line,
                )
            )


def _check_expository_formal_claims(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    line: int,
    findings: list[Finding],
) -> None:
    for match in EXPOSITORY_BLOCK_RE.finditer(decoration):
        body = match.group(2)
        if LABEL_RE.search(body) or FORMAL_INNER_RE.search(body):
            findings.append(
                finding(
                    "formal_claim_inside_expository_block",
                    f"{match.group(1)} block for {label} must not introduce labels or formal theorem-like environments.",
                    path,
                    volume_root,
                    line + _line_at(decoration, match.start()) - 1,
                )
            )


def _check_decoration_blocks(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    env: str,
    line: int,
    findings: list[Finding],
) -> None:
    seen: list[tuple[str, int, int]] = []
    if has_formal_reading(decoration):
        binder_count = sum(count_quantified_binders(body) for body in standard_quantified_statement_bodies(decoration))
        if binder_count >= 2 and not has_predicate_reading(decoration):
            findings.append(
                finding(
                    "predicate_reading_missing",
                    f"{label} has {binder_count} quantified binders but lacks a Predicate reading block.",
                    path,
                    volume_root,
                    line,
                )
            )
    for match in DECORATION_BLOCK_RE.finditer(decoration):
        key = _decoration_key(match)
        block_line = line + _line_at(decoration, match.start()) - 1
        rank = DECORATION_ORDER.get(key)
        if rank is None:
            findings.append(
                finding(
                    "unknown_decoration_block",
                    f"{label} has nonstandard decoration block '{key}'.",
                    path,
                    volume_root,
                    block_line,
                )
            )
            continue
        if key in FORBIDDEN_DECORATION_BY_ENV.get(env, set()):
            findings.append(
                finding(
                    "forbidden_decoration_block",
                    f"{env} must not use decoration block '{key}' by artifact-matrix rules.",
                    path,
                    volume_root,
                    block_line,
                )
            )
        if key == "failure modes":
            _check_failure_modes_block(volume_root, path, decoration, match, label, line, findings)
        seen.append((key, rank, match.start()))

    seen_keys = {key for key, _rank, _pos in seen}
    _check_duplicate_decoration_blocks(volume_root, path, decoration, label, line, seen, findings)
    for child, parent in DEPENDENT_DECORATION_PARENTS.items():
        if child in seen_keys and parent not in seen_keys:
            findings.append(
                finding(
                    "missing_dependent_parent_block",
                    f"{child} requires parent block {parent} for {label}.",
                    path,
                    volume_root,
                    line,
                )
            )
    if seen_keys & FAILURE_MODE_DECOMPOSITION_TRIGGERS:
        if "failure modes" not in seen_keys:
            findings.append(
                finding(
                    "missing_failure_mode_decomposition",
                    f"{label} has negation or contrapositive support but lacks a Failure modes decomposition block.",
                    path,
                    volume_root,
                    line,
                )
            )
        elif not _has_named_failure_mode_branch(decoration):
            findings.append(
                finding(
                    "failure_mode_decomposition_missing_branch",
                    f"{label} has negation or contrapositive support, so its Failure modes block must include at least one named non-exposition branch.",
                    path,
                    volume_root,
                    line,
                )
            )
    for (left_key, left_rank, _left_pos), (right_key, right_rank, right_pos) in zip(seen, seen[1:]):
        if right_rank < left_rank:
            findings.append(
                finding(
                    "decoration_order",
                    f"{right_key} appears before {left_key} for {label}; use the canonical decoration order.",
                    path,
                    volume_root,
                    line + _line_at(decoration, right_pos) - 1,
                )
            )


def _check_duplicate_decoration_blocks(
    volume_root: Path,
    path: Path,
    decoration: str,
    label: str,
    line: int,
    seen: list[tuple[str, int, int]],
    findings: list[Finding],
) -> None:
    first_seen: dict[str, int] = {}
    for key, _rank, pos in seen:
        if key in REPEATABLE_DECORATION_BLOCKS:
            continue
        if key not in first_seen:
            first_seen[key] = pos
            continue
        findings.append(
            finding(
                "duplicate_decoration_block",
                f"{label} has more than one {key} block; keep one block of each canonical support type.",
                path,
                volume_root,
                line + _line_at(decoration, pos) - 1,
            )
        )


def _has_named_failure_mode_branch(decoration: str) -> bool:
    for body_match in re.finditer(
        r"\\begin\{remark\*\}\[Failure modes\](?P<body>[\s\S]*?)\\end\{remark\*\}",
        decoration,
        re.IGNORECASE,
    ):
        body = body_match.group("body")
        for item in re.finditer(r"\\item\[(?P<title>[^\]]+)\]", body):
            title = item.group("title").strip().lower().rstrip(".")
            if title != "exposition":
                return True
    return False


def _check_failure_modes_block(
    volume_root: Path,
    path: Path,
    decoration: str,
    match,
    label: str,
    line: int,
    findings: list[Finding],
) -> None:
    body_match = re.search(r"\\begin\{remark\*\}\[Failure modes\](?P<body>[\s\S]*?)\\end\{remark\*\}", decoration[match.start():], re.IGNORECASE)
    if not body_match:
        return
    body = body_match.group("body")
    block_line = line + _line_at(decoration, match.start()) - 1
    if not re.search(r"\\begin\{description\}", body):
        findings.append(
            finding(
                "failure_modes_missing_description",
                f"{label} Failure modes block must use a description list.",
                path,
                volume_root,
                block_line,
            )
        )
        return
    items = list(re.finditer(r"\\item\[(?P<title>[^\]]+)\](?P<body>[\s\S]*?)(?=\\item\[|\\end\{description\})", body))
    if not items or items[0].group("title").strip().lower().rstrip(".") != "exposition":
        findings.append(
            finding(
                "failure_modes_missing_exposition_item",
                f"{label} Failure modes block must start with \\item[Exposition.].",
                path,
                volume_root,
                block_line,
            )
        )
    if items and all(item.group("title").strip().lower().rstrip(".") == "exposition" for item in items):
        findings.append(
            finding(
                "failure_modes_exposition_only",
                f"{label} Failure modes block contains only exposition; move it to Interpretation/Exposition or use the negated quantified statement instead.",
                path,
                volume_root,
                block_line,
                severity="review",
            )
        )
    for item in items:
        if item.group("title").strip().lower().rstrip(".") == "exposition":
            continue
        item_body = item.group("body")
        item_line = block_line + _line_at(body, item.start()) - 1
        displays = re.findall(r"\\\[[\s\S]*?\\\]", item_body)
        if not displays:
            findings.append(
                finding(
                    "failure_mode_missing_quantified_display",
                    f"{label} failure mode '{item.group('title').strip()}' lacks a quantified display.",
                    path,
                    volume_root,
                    item_line,
                )
            )
        if has_predicate_reading(decoration) and len(displays) < 2:
            findings.append(
                finding(
                    "failure_mode_missing_predicate_display",
                    f"{label} failure mode '{item.group('title').strip()}' lacks a predicate-reading display.",
                    path,
                    volume_root,
                    item_line,
                )
            )


def _first_label(text: str) -> str:
    match = LABEL_RE.search(text)
    return match.group(1) if match else ""


def _decoration_key(match) -> str:
    env = match.group("env").lower()
    if env == "dependencies":
        return "dependencies"
    return re.sub(r"\s+", " ", (match.group("title") or "").strip().lower())


def _ends_with_citation(body: str) -> bool:
    stripped = body.strip()
    return bool(re.search(r"\\cite(?:t|p)?\{[^{}]+\}\.?\s*$", stripped))


def _line_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1
