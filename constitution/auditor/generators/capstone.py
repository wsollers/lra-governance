"""Generate capstone text; stub mode is deterministic, full mode is authored."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from auditor import client, loader


TOOLS = Path(__file__).resolve().parents[3] / "tools" / "governance"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from generators.capstone_stub import render_capstone_stub  # noqa: E402
from validators.capstones import validate_text as validate_capstone_text  # noqa: E402
from validators.latex_integrity import validate_text as validate_latex_text  # noqa: E402


_SUBJECT = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_FORMAL_ENV = re.compile(
    r"\\begin\{(definition|axiom|theorem|lemma|proposition|corollary)\}"
    r"(?:\[([^\]]*)\])?(.*?)\\end\{\1\}",
    re.DOTALL,
)
_LABEL = re.compile(r"\\label\{((?:def|ax|thm|lem|prop|cor):[a-z0-9-]+)\}")
_PROOF_LINK = re.compile(r"\\hyperref\[prf:[^\]]+\]\{(?:[^{}]|\{[^{}]*\})*\}")
_HYPERREF_START = re.compile(r"\\hyperref\[([^\]]+)\]")
_DEPENDENCIES = re.compile(
    r"\\begin\{dependencies\}(.*?)\\end\{dependencies\}",
    re.DOTALL,
)
_REQUIRED_PAYLOAD_FIELDS = (
    "theorem",
    "what_it_says",
    "architecture_of_proof",
    "components",
    "scope_and_honest_limits",
    "instantiation_toward_program",
)
_FORBIDDEN_AUTHORED_TOKENS = (
    r"\label",
    r"\begin{tcolorbox}",
    r"\end{tcolorbox}",
    r"\begin{dependencies}",
    r"\end{dependencies}",
    r"\clearpage",
    r"\phantomsection",
    r"\textbf{Problem.}",
)


class FullCapstoneGenerationError(ValueError):
    def __init__(self, findings: list[dict[str, str]]):
        self.findings = findings
        details = "; ".join(
            f"{item['code']}: {item['message']}"
            for item in findings
            if item["severity"] == "error"
        )
        super().__init__(f"Generated full capstone failed deterministic validation: {details}")


def generate_capstone(
    chapter_subject: str,
    chapter_display_title: str,
    chapter_registry: list[dict],
    chapter_environments: list[dict],
    mode: str = "stub",
    dependencies: list[tuple[str, str]] | None = None,
    *,
    state_dependencies: list[tuple[str, str]] | None = None,
    proof_dependencies: list[tuple[str, str]] | None = None,
    chapter_source_records: list[dict[str, str]] | None = None,
) -> str:
    if mode == "stub":
        if state_dependencies or proof_dependencies or chapter_source_records:
            raise ValueError("full-capstone inputs are not accepted in stub mode")
        return render_capstone_stub(chapter_subject, chapter_display_title, dependencies)
    if mode != "full":
        raise ValueError("mode must be stub or full")
    if dependencies:
        raise ValueError(
            "full mode requires separate state_dependencies and proof_dependencies"
        )

    request = build_full_capstone_request(
        chapter_subject=chapter_subject,
        chapter_display_title=chapter_display_title,
        chapter_registry=chapter_registry,
        chapter_environments=chapter_environments,
        chapter_source_records=chapter_source_records or [],
        state_dependencies=state_dependencies or [],
        proof_dependencies=proof_dependencies or [],
    )
    payload = client.call(
        loader.prompt("generate_capstone"),
        "## Validated Full-Capstone Authoring Request\n\n"
        + "```json\n"
        + json.dumps(request, indent=2, ensure_ascii=True)
        + "\n```",
        expect_json=True,
    )
    authored = validate_authored_payload(payload)
    latex = render_full_capstone(request, authored)
    findings = validate_full_capstone_output(latex, request)
    if any(item["severity"] == "error" for item in findings):
        raise FullCapstoneGenerationError(findings)
    return latex


def extract_chapter_source_records(chapter_path: Path) -> list[dict[str, str]]:
    """Extract exact current-chapter formal statements from routed notes source."""
    notes = chapter_path / "notes"
    if not notes.is_dir():
        raise ValueError(f"chapter notes directory is missing: {notes}")
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in sorted(notes.rglob("*.tex")):
        if path.name == "index.tex":
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        for match in _FORMAL_ENV.finditer(text):
            labels = _LABEL.findall(match.group(3))
            if len(labels) != 1:
                continue
            label = labels[0]
            if label in seen:
                raise ValueError(f"duplicate formal label while extracting capstone input: {label}")
            body = _LABEL.sub("", match.group(3))
            body = _PROOF_LINK.sub("", body).strip()
            records.append(
                {
                    "label": label,
                    "type": match.group(1),
                    "display_title": (match.group(2) or label).strip(),
                    "statement_body": body,
                    "source": path.relative_to(chapter_path).as_posix(),
                }
            )
            seen.add(label)
    return records


def build_full_capstone_request(
    *,
    chapter_subject: str,
    chapter_display_title: str,
    chapter_registry: list[dict],
    chapter_environments: list[dict],
    chapter_source_records: list[dict[str, str]],
    state_dependencies: list[tuple[str, str]],
    proof_dependencies: list[tuple[str, str]],
) -> dict[str, Any]:
    if not _SUBJECT.fullmatch(chapter_subject or ""):
        raise ValueError("chapter_subject must be lowercase ASCII words separated by hyphens")
    title = chapter_display_title.strip()
    if not title:
        raise ValueError("chapter_display_title is required")
    _require_ascii(title, "chapter_display_title")

    ceiling = _compact_registry_ceiling(chapter_subject, chapter_registry)
    sources = _source_index(chapter_source_records)
    _cross_check_environment_index(chapter_environments, sources)
    state = _dependency_records(state_dependencies, sources, "state")
    proof = _dependency_records(proof_dependencies, sources, "proof")
    if not state:
        raise ValueError("full capstone requires at least one dependency to state")
    if not proof:
        raise ValueError("full capstone requires at least one dependency to prove")
    selected_labels = list(dict.fromkeys([item["label"] for item in state + proof]))
    if len(selected_labels) < 2:
        raise ValueError("full capstone must synthesize at least two distinct chapter results")

    return {
        "chapter_subject": chapter_subject,
        "chapter_display_title": title,
        "capstone_label": f"cap:{chapter_subject}",
        "registry_ceiling": ceiling,
        "state_dependencies": state,
        "proof_dependencies": proof,
        "selected_source_statements": [sources[label] for label in selected_labels],
        "output_schema": {
            "theorem": "nonempty ASCII LaTeX string",
            "what_it_says": "nonempty ASCII LaTeX string",
            "architecture_of_proof": "nonempty ASCII LaTeX string; no complete proof",
            "components": [
                {"statement": "nonempty ASCII LaTeX string", "strategy": "trailhead only"}
            ],
            "scope_and_honest_limits": "nonempty ASCII LaTeX string",
            "instantiation_toward_program": "nonempty ASCII LaTeX string",
        },
    }


def validate_authored_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("full-capstone authoring response must be a JSON object")
    if set(payload) != set(_REQUIRED_PAYLOAD_FIELDS):
        missing = sorted(set(_REQUIRED_PAYLOAD_FIELDS) - set(payload))
        extra = sorted(set(payload) - set(_REQUIRED_PAYLOAD_FIELDS))
        raise ValueError(f"full-capstone response fields mismatch; missing={missing}; extra={extra}")

    authored: dict[str, Any] = {}
    for field in _REQUIRED_PAYLOAD_FIELDS:
        if field == "components":
            continue
        authored[field] = _authored_text(payload[field], field)

    components = payload["components"]
    if not isinstance(components, list) or len(components) < 2:
        raise ValueError("full-capstone response requires at least two structured components")
    authored["components"] = []
    for index, component in enumerate(components, 1):
        if not isinstance(component, dict) or set(component) != {"statement", "strategy"}:
            raise ValueError(f"component {index} must contain only statement and strategy")
        authored["components"].append(
            {
                "statement": _authored_text(component["statement"], f"component {index} statement"),
                "strategy": _authored_text(component["strategy"], f"component {index} strategy"),
            }
        )
    return authored


def render_full_capstone(request: dict[str, Any], authored: dict[str, Any]) -> str:
    state_items = _dependency_items(request["state_dependencies"])
    proof_items = _dependency_items(request["proof_dependencies"])
    all_dependencies = []
    seen = set()
    for record in request["state_dependencies"] + request["proof_dependencies"]:
        if record["label"] not in seen:
            all_dependencies.append(record)
            seen.add(record["label"])
    dependency_items = _dependency_items(all_dependencies)
    ceiling_titles = ", ".join(entry["display_title"] for entry in request["registry_ceiling"])
    component_items = "\n".join(
        f"  \\item {item['statement']} \\emph{{Strategy:}} {item['strategy']}"
        for item in authored["components"]
    )
    return (
        "\\phantomsection\n"
        f"\\label{{{request['capstone_label']}}}\n\n"
        "\\begin{tcolorbox}[\n"
        "  colback=gray!6,\n"
        "  colframe=gray!40,\n"
        "  arc=2pt,\n"
        "  left=8pt, right=8pt, top=6pt, bottom=6pt,\n"
        "  title={\\small\\textbf{Capstone Theorem}},\n"
        "  fonttitle=\\small\\bfseries\n"
        "]\n"
        "\\textbf{Theorem.}\n"
        f"{authored['theorem']}\n"
        "\\end{tcolorbox}\n\n"
        "\\begin{remark*}[What it says]\n"
        f"{authored['what_it_says']}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Architecture of the proof]\n"
        f"{authored['architecture_of_proof']}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Components]\n"
        "\\begin{enumerate}\n"
        f"{component_items}\n"
        "\\end{enumerate}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Scope and honest limits]\n"
        f"{authored['scope_and_honest_limits']}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Instantiation toward the program]\n"
        f"{authored['instantiation_toward_program']}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependencies to state]\n"
        "\\begin{itemize}\n"
        f"{state_items}\n"
        "\\end{itemize}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependencies to prove]\n"
        "\\begin{itemize}\n"
        f"{proof_items}\n"
        "\\end{itemize}\n"
        "\\end{remark*}\n\n"
        "\\begin{remark*}[Dependency ceiling]\n"
        f"Only results routed in these chapters may be used: {ceiling_titles}.\n"
        "\\end{remark*}\n\n"
        "\\begin{dependencies}\n"
        "\\begin{itemize}\n"
        f"{dependency_items}\n"
        "\\end{itemize}\n"
        "\\end{dependencies}\n\n"
        "\\clearpage\n"
    )


def validate_full_capstone_output(
    latex: str,
    request: dict[str, Any],
) -> list[dict[str, str]]:
    findings = [
        {
            "severity": item.severity,
            "code": item.code,
            "message": item.message,
            "evidence": item.path,
        }
        for item in (
            validate_capstone_text(latex, chapter_subject=request["chapter_subject"])
            + validate_latex_text(latex)
        )
    ]

    def fail(code: str, message: str, evidence: str = "") -> None:
        findings.append(
            {"severity": "error", "code": code, "message": message, "evidence": evidence}
        )

    try:
        latex.encode("ascii")
    except UnicodeEncodeError as exc:
        fail("non_ascii_output", "Full-capstone source must be ASCII LaTeX.", str(exc))
    if "TODO" in latex or "UNRESOLVED_DEPENDENCY" in latex:
        fail("incomplete_full_capstone", "Full-capstone output must not contain unresolved placeholders.")

    blocks = _DEPENDENCIES.findall(latex)
    observed = _dependency_pairs("\n".join(blocks))
    expected = []
    seen = set()
    for record in request["state_dependencies"] + request["proof_dependencies"]:
        pair = (record["label"], _normalize_space(record["display"]))
        if record["label"] not in seen:
            expected.append(pair)
            seen.add(record["label"])
    if len(blocks) != 1 or observed != expected:
        fail(
            "capstone_dependency_records_mismatch",
            "Capstone dependency links must exactly match the caller-approved union and order.",
            f"expected={expected}; found={observed}; blocks={len(blocks)}",
        )
    if not latex.rstrip().endswith(r"\clearpage"):
        fail("capstone_terminal_clearpage", "Full capstone must end with clearpage.")
    return findings


def _compact_registry_ceiling(subject: str, registry: list[dict]) -> list[dict[str, str]]:
    compact = []
    found = False
    seen = set()
    for entry in registry:
        entry_subject = str(entry.get("subject", "")).strip()
        display = str(entry.get("display_title", "")).strip()
        if not _SUBJECT.fullmatch(entry_subject) or not display:
            raise ValueError("chapter registry entries require subject and display_title")
        if entry_subject in seen:
            raise ValueError(f"duplicate chapter registry subject: {entry_subject}")
        _require_ascii(display, f"registry display title for {entry_subject}")
        compact.append({"subject": entry_subject, "display_title": display})
        seen.add(entry_subject)
        if entry_subject == subject:
            found = True
            break
    if not found:
        raise ValueError(f"chapter subject is missing from ordered chapter registry: {subject}")
    return compact


def _source_index(records: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed = {}
    for record in records:
        label = str(record.get("label", "")).strip()
        if not _LABEL.fullmatch(rf"\label{{{label}}}"):
            raise ValueError(f"invalid extracted formal label: {label}")
        if label in indexed:
            raise ValueError(f"duplicate extracted formal label: {label}")
        compact = {
            "label": label,
            "type": str(record.get("type", "")).strip(),
            "display_title": str(record.get("display_title", "")).strip(),
            "statement_body": str(record.get("statement_body", "")).strip(),
            "source": str(record.get("source", "")).strip(),
        }
        if not compact["statement_body"]:
            raise ValueError(f"empty extracted statement body: {label}")
        for key, value in compact.items():
            _require_ascii(value, f"source record {label} {key}")
        indexed[label] = compact
    return indexed


def _cross_check_environment_index(
    environments: list[dict],
    sources: dict[str, dict[str, str]],
) -> None:
    if not environments:
        return
    indexed_labels = {
        str(record.get("label", "")).strip()
        for record in environments
        if record.get("label")
    }
    missing = sorted(indexed_labels - set(sources))
    if missing:
        raise ValueError(
            "chapter environment index refers to statements missing from notes source: "
            + ", ".join(missing)
        )


def _dependency_records(
    dependencies: list[tuple[str, str]],
    sources: dict[str, dict[str, str]],
    role: str,
) -> list[dict[str, str]]:
    records = []
    seen = set()
    for raw_label, raw_display in dependencies:
        label = raw_label.strip()
        display = raw_display.strip()
        if label in seen:
            raise ValueError(f"duplicate {role} dependency: {label}")
        if label not in sources:
            raise ValueError(f"{role} dependency is not a current-chapter source statement: {label}")
        if not display:
            raise ValueError(f"{role} dependency display is empty: {label}")
        _require_ascii(display, f"{role} dependency display")
        _reject_structural_tokens(display, f"{role} dependency display")
        records.append({"label": label, "display": display})
        seen.add(label)
    return records


def _authored_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    text = value.strip()
    _require_ascii(text, field)
    _reject_structural_tokens(text, field)
    return text


def _reject_structural_tokens(text: str, field: str) -> None:
    for token in _FORBIDDEN_AUTHORED_TOKENS:
        if token in text:
            raise ValueError(f"{field} contains caller-owned structural token {token}")


def _dependency_items(records: list[dict[str, str]]) -> str:
    return "\n".join(
        f"  \\item \\hyperref[{record['label']}]{{{record['display']}}}"
        for record in records
    )


def _dependency_pairs(text: str) -> list[tuple[str, str]]:
    pairs = []
    for match in _HYPERREF_START.finditer(text):
        start = match.end()
        while start < len(text) and text[start].isspace():
            start += 1
        end = _balanced_group_end(text, start)
        display = text[start + 1:end - 1] if end is not None else ""
        pairs.append((match.group(1), _normalize_space(display)))
    return pairs


def _balanced_group_end(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _require_ascii(value: str, field: str) -> None:
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field} must use ASCII/LaTeX source") from exc
