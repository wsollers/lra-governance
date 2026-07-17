#!/usr/bin/env python3
"""Build and compare deterministic semantic AST witnesses for formal TeX blocks.

This tool is intentionally an ensemble coordinator, not a theorem prover.  It
extracts formal blocks, decomposes each block into governed components, builds
several imperfect AST/fact witnesses, and compares their structural claims.
Optional parser backends contribute only when their dependencies/runtime are
available.
"""

from __future__ import annotations

import argparse
import ast as py_ast
import os
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

from compare_semantic_ast_extractors import (
    displayed_math_extract,
    predicate_operator_names,
    strip_comments,
    surface_regex_extract,
)
from semantic_chapter_sweep import FormalBlock, formal_blocks, remark_bodies


DISPLAY_RE = re.compile(r"\\\[(?P<body>.*?)\\\]", re.S)
INLINE_MATH_RE = re.compile(r"\\\((?P<body>.*?)\\\)|\$(?P<dollar>[^$]+)\$", re.S)
QUANTIFIER_RE = re.compile(
    r"\\(?P<kind>forall|exists)\s*(?P<body>.*?)(?=(?:\\forall|\\exists|\\Rightarrow|\\Longrightarrow|\\implies|\\land|\\lor|\.|,?\s*\)|,?\s*\]|\Z))",
    re.S,
)
LET_RE = re.compile(
    r"\b(?P<kind>Let|Suppose|Assume|Given|Where)\b(?P<body>.*?)(?=(?:\.|;|\n|$))",
    re.I | re.S,
)
MATHBB_RE = re.compile(r"\\mathbb\{(?P<name>[A-Za-z]+)\}")
MATHCAL_RE = re.compile(r"\\mathcal\{(?P<name>[A-Za-z]+)\}")
FUNCTION_CALL_RE = re.compile(r"(?<!\\)(?P<name>[A-Za-z][A-Za-z0-9]*)\s*\((?P<args>[^()]*)\)")
HYPERREF_RE = re.compile(r"\\hyperref\[(?P<label>[^\]]+)\]")
DISPLAY_ENV_RE = re.compile(r"\\(?:begin|end)\{(?:aligned|align\*?|gathered|gather\*?|equation\*?|split|multline\*?)\}")
TEXT_COMMAND_RE = re.compile(r"\\text\{(?P<body>[^{}]*)\}")
RELATION_SPLIT_RE = re.compile(
    r"(?:\\Longleftrightarrow|\\Leftrightarrow|\\iff|\\Longrightarrow|\\Rightarrow|\\implies|\\land|\\lor|\\leq|\\geq|\\neq|\\ne(?!g)|=|<|>)"
)
SEMANTIC_OPERATOR_RE = re.compile(
    r"\\(?P<name>sup|inf|min|max)\s*(?P<arg>\([^)]*\)|\{[^{}]*\}|[A-Za-z][A-Za-z0-9]*)?"
    r"|\\operatorname\{(?P<op>[A-Za-z][A-Za-z0-9]*)\}\s*(?P<oparg>\([^)]*\))?"
)
PLACEHOLDER_SYMBOLS = tuple("UVWXYZ")
PREDICATE_DEPENDENCY_OVERRIDES = {
    "UpperBound": "def:real-upper-bound",
    "LowerBound": "def:real-lower-bound",
    "BoundedAbove": "def:bounded-above",
    "BoundedBelow": "def:bounded-below",
    "Bounded": "def:bounded",
    "LeastUpperBound": "def:supremum",
    "GreatestLowerBound": "def:infimum",
    "GreatestElement": "def:maximum",
    "LeastElement": "def:minimum",
    "LeastUpperBoundProperty": "def:least-upper-bound-property",
    "HasLeastUpperBoundProperty": "def:least-upper-bound-property",
}
STRUCTURE_DEPENDENCY_OVERRIDES = {
    "OrderedSet": "def:ordered-set",
    "PreorderedSet": "def:preordered-set",
    "PartiallyOrderedSet": "def:partially-ordered-set",
    "TotallyOrderedSet": "def:totally-ordered-set",
    "WellOrderedSet": "def:well-ordered-set",
}
DEPENDENCY_LABEL_ALIASES = {
    "def:real-upper-bound": ["def:upper-bound"],
    "def:real-lower-bound": ["def:lower-bound"],
    "def:replacement-image": ["def:image-set", "ax:replacement"],
}


@dataclass
class AstCandidate:
    source: str
    available: bool = True
    notes: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "available": self.available,
            "notes": self.notes,
            "facts": self.facts,
        }


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML root must be a mapping")
    return data


def write_payload(path: Path | None, payload: dict[str, Any], fmt: str) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n" if fmt == "json" else yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def first_display(text: str) -> str:
    match = DISPLAY_RE.search(text)
    return match.group("body").strip() if match else text.strip()


def all_displays(text: str) -> list[str]:
    return [match.group("body").strip() for match in DISPLAY_RE.finditer(text)]


def inline_math(text: str) -> list[str]:
    values: list[str] = []
    for match in INLINE_MATH_RE.finditer(text):
        values.append((match.group("body") or match.group("dollar") or "").strip())
    return [value for value in values if value]


def component_tex(block: FormalBlock) -> dict[str, Any]:
    remarks = remark_bodies(block.text)
    displays = all_displays(block.text)
    return {
        "full": block.text,
        "displays": displays,
        "inline_math": inline_math(block.text),
        "remarks": {title: bodies for title, bodies in sorted(remarks.items())},
        "standard_quantified": [first_display(body) for title, bodies in remarks.items() if "standard quantified" in title for body in bodies],
        "predicate_reading": [first_display(body) for title, bodies in remarks.items() if "predicate reading" in title for body in bodies],
        "negated_quantified": [first_display(body) for title, bodies in remarks.items() if "negated quantified" in title or "negation" in title for body in bodies],
        "contrapositive": [first_display(body) for title, bodies in remarks.items() if "contrapositive" in title for body in bodies],
        "source_alignment": [body for title, bodies in remarks.items() if "source" in title or "provenance" in title for body in bodies],
    }


def clean_var(raw: str, fallback: str) -> str:
    value = re.sub(r"\\(?:,|!|:|\s)+", "", raw)
    value = re.sub(r"[^A-Za-z\\]+", "", value).strip()
    return value or fallback


def quantified_variables_from_body(body: str, kind: str) -> tuple[list[str], str | None]:
    domain_match = re.search(r"\\(?:in|subseteq|subset)\s*(?P<domain>[^;,.\\]+|\\[A-Za-z]+\{[^}]+\}|\\mathbb\{[^}]+\}|\\mathcal\{[^}]+\})", body)
    domain = domain_match.group("domain").strip() if domain_match else None
    before_domain = re.split(r"\\in|\\subseteq|\\subset|:", body, maxsplit=1)[0]
    before_domain = re.split(r"\\;|;|\\quad|\\text|\\bigl|\\Bigl|\\left|\[|\(", before_domain, maxsplit=1)[0]
    variables = [clean_var(item.strip(), f"{kind}_{index + 1}") for index, item in enumerate(before_domain.split(",")) if item.strip()]
    return variables or [f"{kind}_1"], domain


def quantifiers_from_latex(latex: str) -> list[dict[str, Any]]:
    quantifiers: list[dict[str, Any]] = []
    for match in QUANTIFIER_RE.finditer(latex):
        kind = match.group("kind")
        variables, domain = quantified_variables_from_body(match.group("body"), kind)
        quantifiers.append({"kind": kind, "variables": variables, "variable_count": len(variables), "domain": domain})
    return quantifiers


def let_assumptions(text: str) -> list[dict[str, str]]:
    assumptions = []
    for match in LET_RE.finditer(strip_comments(text)):
        body = re.sub(r"\s+", " ", match.group("body")).strip()
        if body:
            assumptions.append({"kind": match.group("kind").lower(), "text": body})
    return assumptions


def structures_from_text(text: str) -> list[dict[str, str]]:
    structures: list[dict[str, str]] = []
    for match in MATHBB_RE.finditer(text):
        structures.append({"surface": match.group(0), "kind": "mathbb", "name": match.group("name")})
    for match in MATHCAL_RE.finditer(text):
        structures.append({"surface": match.group(0), "kind": "mathcal", "name": match.group("name")})
    for phrase in re.findall(r"\b(?:ordered field|metric space|topological space|normed space|vector space|real line)\b", text, flags=re.I):
        structures.append({"surface": phrase, "kind": "prose_structure", "name": phrase.lower()})
    return sorted({json.dumps(item, sort_keys=True): item for item in structures}.values(), key=lambda item: (item["kind"], item["name"]))


def function_calls(text: str) -> list[dict[str, Any]]:
    calls = []
    for match in FUNCTION_CALL_RE.finditer(text):
        name = match.group("name")
        if name in {"operatorname", "begin", "end", "label", "mathbb", "mathcal"}:
            continue
        args = [arg.strip() for arg in match.group("args").split(",") if arg.strip()]
        calls.append({"name": name, "arity": len(args), "arguments": args})
    return calls


def normalize_tex_expression_fragment(fragment: str) -> dict[str, Any] | None:
    r"""Normalize one theorem/display fragment into a parser-sized expression.

    This is intentionally conservative.  Unsupported semantic operators such as
    ``\sup`` and ``\operatorname{GreatestLowerBound}`` are replaced with stable
    placeholder symbols, and the mapping back to the original TeX is recorded.
    The expression parser witnesses therefore test the algebraic shell without
    pretending they understood theorem-level semantics.
    """

    original = fragment
    text = strip_comments(fragment).strip()
    text = re.sub(r"\\(?:bigl|bigr|Bigl|Bigr|left|right)", "", text)
    text = re.sub(r"\\(?:,|;|!|quad|qquad)\s*", " ", text)
    text = re.sub(r"\\mathbb\{([A-Za-z]+)\}", r"\1", text)
    text = re.sub(r"\\mathcal\{([A-Za-z]+)\}", r"\1", text)
    text = text.strip().rstrip(".,;")
    if not text:
        return None
    if re.search(r"\\neg\b", text):
        return None
    if re.search(r"\\(?:forall|exists)\b|\\begin\b|\\end\b|\\text\b", text):
        return None
    if re.search(r"\\(?:in|subseteq|subset)\b", text) or ":" in text:
        return None

    placeholders: list[dict[str, str]] = []

    def placeholder(match: re.Match[str]) -> str:
        name = match.group("name") or match.group("op") or "expr"
        surface = match.group(0).strip()
        index = len(placeholders)
        symbol = PLACEHOLDER_SYMBOLS[index] if index < len(PLACEHOLDER_SYMBOLS) else f"Q{index}"
        placeholders.append({"symbol": symbol, "name": name, "surface": surface})
        return symbol

    text = SEMANTIC_OPERATOR_RE.sub(placeholder, text)
    text = text.replace("^", "**")
    text = re.sub(r"\\(?:cdot|times)", "*", text)
    text = re.sub(r"\\[A-Za-z]+", "", text)
    text = text.replace("{", "(").replace("}", ")")
    text = re.sub(r"\s+", "", text)
    if not text or "\\" in text or "&" in text:
        return None
    if not re.search(r"[A-Za-z0-9]", text):
        return None
    return {"original": original.strip(), "normalized": text, "placeholders": placeholders}


def normalized_expression_witness_inputs(displays: Iterable[str]) -> dict[str, Any]:
    """Split theorem-style display TeX into expression parser witness inputs."""

    fragments: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    seen: set[str] = set()
    for display in displays:
        without_env = DISPLAY_ENV_RE.sub("", display)
        lines = re.split(r"\\\\", without_env)
        for raw_line in lines:
            line = raw_line.replace("&", " ").strip()
            if not line:
                continue
            text_bodies = [match.group("body").strip() for match in TEXT_COMMAND_RE.finditer(line)]
            if any(re.match(r"(?i)\s*(Let|Suppose|Assume|Given|Where)\b", body) for body in text_bodies):
                skipped.append({"input": raw_line.strip(), "reason": "prose-assumption-line"})
                continue
            if re.search(r"\\mathsf\{|\\(?:subseteq|subset)\b", line):
                skipped.append({"input": raw_line.strip(), "reason": "ambient-or-set-builder-line"})
                continue
            line = TEXT_COMMAND_RE.sub("", line).strip()
            if not line:
                continue
            pieces = [piece.strip() for piece in RELATION_SPLIT_RE.split(line) if piece.strip()]
            if not pieces:
                pieces = [line]
            for piece in pieces:
                normalized = normalize_tex_expression_fragment(piece)
                if normalized is None:
                    skipped.append({"input": piece.strip(), "reason": "not-expression-parser-shaped"})
                    continue
                key = f"{normalized['normalized']}\0{normalized['original']}"
                if key in seen:
                    continue
                seen.add(key)
                fragments.append(normalized)
    return {"fragments": fragments, "skipped": skipped}


def connective_shape(text: str) -> dict[str, Any]:
    return {
        "has_iff": bool(re.search(r"\\iff|\\Longleftrightarrow|\bif and only if\b|\bequivalent(?:ly)?\b", text, re.I)),
        "has_implies": bool(re.search(r"\\implies|\\Rightarrow|\\Longrightarrow", text)),
        "has_negation": bool(re.search(r"\\neg|\\not|\\nleq|\\notin|\bnot\b|\bfails?\b", text, re.I)),
        "iff_count": len(re.findall(r"\\iff|\\Longleftrightarrow", text)),
        "implies_count": len(re.findall(r"\\implies|\\Rightarrow|\\Longrightarrow", text)),
    }


def standard_quantified_block_findings(block: FormalBlock, components: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    standard_blocks = components.get("standard_quantified") or []
    if not standard_blocks:
        return findings
    standard_text = "\n".join(standard_blocks)
    support_texts: list[str] = []
    for key, value in components.items():
        if key in {"standard_quantified", "full", "inline_math"}:
            continue
        if isinstance(value, list):
            support_texts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            for bodies in value.values():
                if isinstance(bodies, list):
                    support_texts.extend(str(item) for item in bodies)
    support_text = "\n".join(support_texts)
    source_text = block.text

    def add(code: str, message: str) -> None:
        findings.append(
            {
                "code": code,
                "severity": "error",
                "message": message,
                "field": "components.standard_quantified",
            }
        )

    standard_quantifiers = quantifiers_from_latex(standard_text)
    source_has_quantifier_cues = bool(re.search(r"\\forall|\\exists|\bfor every\b|\bfor all\b|\bthere exists\b|\bevery\b", source_text, re.I))
    support_has_quantifiers = bool(re.search(r"\\forall|\\exists", support_text))
    standard_has_prose_let = bool(re.search(r"\\text\{\s*(?:Let|Suppose|Assume|Given|Where)\b|\\text\{[^}]*\b(?:nonempty|bounded|where|such that)\b", standard_text, re.I))
    standard_connectives = connective_shape(standard_text)
    support_connectives = connective_shape(support_text)

    if standard_has_prose_let:
        add(
            "STANDARD_QUANTIFIED_CONTAINS_PROSE_LET",
            "Standard quantified block contains prose/Let-style text; it looks like a restatement rather than a quantified normalization.",
        )
    if source_has_quantifier_cues and not standard_quantifiers:
        add(
            "STANDARD_QUANTIFIED_LACKS_BINDERS",
            "Source/support text contains quantifier cues, but the standard quantified block exposes no explicit quantified binders.",
        )
    if support_has_quantifiers and not standard_quantifiers:
        add(
            "SUPPORT_BLOCK_HAS_STRONGER_QUANTIFIER_STRUCTURE",
            "A support block contains explicit quantifiers while the standard quantified block contains none.",
        )
    if support_connectives.get("has_implies") and not standard_connectives.get("has_implies"):
        add(
            "PREDICATE_READING_HAS_IMPLICATION_BUT_STANDARD_DOES_NOT",
            "Support/predicate-reading blocks contain implication structure absent from the standard quantified block.",
        )
    if (
        not standard_quantifiers
        and not standard_connectives.get("has_implies")
        and not standard_connectives.get("has_iff")
        and bool(re.search(r"=|\\ne|<|>|\\leq|\\geq", standard_text))
        and bool(let_assumptions(source_text))
    ):
        add(
            "STANDARD_QUANTIFIED_ONLY_RESTATES_CONCLUSION",
            "Standard quantified block appears to restate only an equation/comparison conclusion while source assumptions remain outside the formal shape.",
        )
    return findings


def strip_tex_wrappers(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^\$|\$$", "", value)
    value = re.sub(r"\\[;,!]\s*", "", value)
    return value.strip()


def first_sentence(text: str) -> str:
    clean = strip_comments(text)
    clean = re.sub(r"\\begin\{[^}]+\}(?:\[[^\]]+\])?(?:\{[^}]+\})?", " ", clean)
    clean = re.sub(r"\\label\{[^}]+\}", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    match = re.search(r"(.+?\.)", clean)
    return match.group(1).strip() if match else clean


def statement_preamble(text: str) -> str:
    clean = strip_comments(text)
    clean = re.sub(r"\\begin\{[^}]+\}(?:\[[^\]]+\])?(?:\{[^}]+\})?", " ", clean)
    clean = re.sub(r"\\label\{[^}]+\}", " ", clean)
    clean = clean.split(r"\[", 1)[0]
    return re.sub(r"\s+", " ", clean).strip()


def first_conclusion_display(block: FormalBlock, components: dict[str, Any]) -> str | None:
    displays = components.get("displays") or []
    if displays:
        return strip_tex_wrappers(str(displays[0]))
    return None


def detect_let_domain(sentence: str) -> tuple[str, str] | None:
    match = re.search(r"Let\s+\$(?P<var>[A-Za-z][A-Za-z0-9]*)\\subseteq(?P<domain>[^$]+)\$", sentence)
    if match:
        return match.group("var"), strip_tex_wrappers(match.group("domain"))
    match = re.search(r"Let\s+\$(?P<var>[A-Za-z][A-Za-z0-9]*)\\in(?P<domain>[^$]+)\$", sentence)
    if match:
        return match.group("var"), strip_tex_wrappers(match.group("domain"))
    return None


def detect_reflected_set(sentence: str) -> tuple[str, str] | None:
    match = re.search(r"\$(?P<set>-[A-Za-z][A-Za-z0-9]*)=(?P<body>\\\{[^$]+?\\\})\$", sentence)
    if match:
        return strip_tex_wrappers(match.group("set")), strip_tex_wrappers(match.group("body"))
    return None


def generated_standard_quantified_suggestion(block: FormalBlock, components: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not any(
        finding["code"]
        in {
            "STANDARD_QUANTIFIED_CONTAINS_PROSE_LET",
            "STANDARD_QUANTIFIED_LACKS_BINDERS",
            "STANDARD_QUANTIFIED_ONLY_RESTATES_CONCLUSION",
        }
        for finding in findings
    ):
        return None

    sentence = first_sentence(block.text)
    preamble = statement_preamble(block.text)
    hypothesis_text = re.split(r"\bThen\b", preamble, maxsplit=1, flags=re.I)[0]
    let_domain = detect_let_domain(preamble) or detect_let_domain(sentence)
    conclusion = first_conclusion_display(block, components)
    if not let_domain or not conclusion:
        return {
            "status": "not_generated",
            "reason": "The source statement did not match the conservative Let/domain plus displayed-conclusion heuristic.",
            "source_sentence": preamble or sentence,
        }

    variable, domain = let_domain
    assumptions: list[str] = []
    notes: list[str] = ["Generated by conservative Python heuristics; requires mathematical review before use."]
    if re.search(r"\bnonempty\b", hypothesis_text, re.I):
        assumptions.append(rf"{variable}\ne\varnothing")
    if re.search(r"\bbounded below\b", hypothesis_text, re.I):
        assumptions.append(rf"\operatorname{{BoundedBelow}}({variable},\mathbb{{R}})")
    if re.search(r"\bbounded above\b", hypothesis_text, re.I):
        assumptions.append(rf"\operatorname{{BoundedAbove}}({variable},\mathbb{{R}})")

    conclusion_parts: list[str] = []
    reflected = detect_reflected_set(preamble)
    if reflected:
        reflected_set, _ = reflected
        if re.search(rf"\${re.escape(reflected_set)}=.*?bounded above", preamble, re.I):
            conclusion_parts.append(rf"\operatorname{{BoundedAbove}}({reflected_set},\mathbb{{R}})")
            notes.append(f"Detected reflected-set bounded-above conclusion for {reflected_set}.")
        elif "bounded above" in preamble.lower():
            conclusion_parts.append(rf"\operatorname{{BoundedAbove}}({reflected_set},\mathbb{{R}})")
            notes.append(f"Inferred bounded-above conclusion for detected reflected set {reflected_set}.")
    conclusion_parts.append(conclusion.rstrip("."))

    assumption_tex = r"\land ".join(assumptions) if assumptions else r"\top"
    if len(conclusion_parts) == 1:
        conclusion_tex = conclusion_parts[0]
    else:
        conclusion_tex = r"\bigl(" + (r"\land ".join(conclusion_parts)) + r"\bigr)"
    latex = (
        "\\[\n"
        f"\\forall {variable}\\subseteq {domain}\\;"
        "\\Bigl(\n"
        f"  {assumption_tex}\n"
        r"  \Longrightarrow"
        "\n"
        rf"  {conclusion_tex}"
        "\n"
        "\\Bigr).\n"
        "\\]\n"
    )
    return {
        "status": "generated_suggestion_requires_review",
        "source": "python_conservative_heuristic",
        "source_sentence": preamble or sentence,
        "latex": latex,
        "assumptions": assumptions,
        "conclusions": conclusion_parts,
        "notes": notes,
    }


def nltk_standard_quantified_suggestion(block: FormalBlock, components: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not any(finding["code"].startswith("STANDARD_QUANTIFIED") for finding in findings):
        return None
    if importlib.util.find_spec("nltk") is None:
        return {
            "status": "unavailable",
            "source": "nltk_prose",
            "reason": "nltk is not installed in this Python environment.",
        }
    import nltk

    preamble = statement_preamble(block.text)
    try:
        tokens = nltk.word_tokenize(preamble)
        tagged = nltk.pos_tag(tokens)
    except LookupError as exc:
        return {
            "status": "unavailable",
            "source": "nltk_prose",
            "reason": f"nltk data missing: {exc}",
        }

    lower = [token.lower() for token in tokens]
    quantifier_cues = [token for token in lower if token in {"let", "for", "every", "all", "each", "any", "exists", "some"}]
    assumption_cues = [token for token in lower if token in {"nonempty", "bounded", "below", "above", "suppose", "assume", "given"}]
    base = generated_standard_quantified_suggestion(block, components, findings)
    if not base or base.get("status") != "generated_suggestion_requires_review":
        return {
            "status": "not_generated",
            "source": "nltk_prose",
            "reason": "NLTK extracted prose cues, but the conservative theorem-level template did not match.",
            "tokens": tokens,
            "tagged_tokens": tagged[:80],
            "quantifier_cues": quantifier_cues,
            "assumption_cues": assumption_cues,
        }
    suggestion = dict(base)
    suggestion["source"] = "nltk_prose_assisted"
    suggestion["notes"] = [
        "NLTK supplied token/POS and cue extraction; theorem-level LaTeX assembly uses the conservative Python template.",
        *base.get("notes", []),
    ]
    suggestion["nltk"] = {
        "tokens": tokens,
        "tagged_tokens": tagged[:80],
        "quantifier_cues": quantifier_cues,
        "assumption_cues": assumption_cues,
    }
    return suggestion


def latex2sympy_standard_quantified_suggestion(block: FormalBlock, components: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not any(finding["code"].startswith("STANDARD_QUANTIFIED") for finding in findings):
        return None
    if importlib.util.find_spec("latex2sympy2") is None:
        return {
            "status": "unavailable",
            "source": "latex2sympy",
            "reason": "latex2sympy2 is not installed in this Python environment.",
        }
    try:
        module = __import__("latex2sympy2", fromlist=["latex2sympy"])
    except Exception as exc:  # noqa: BLE001 - optional witness may fail at import time.
        return {
            "status": "unavailable",
            "source": "latex2sympy",
            "reason": f"latex2sympy2 import failed: {type(exc).__name__}: {exc}",
        }
    parser = getattr(module, "latex2sympy", None)
    if parser is None:
        return {
            "status": "unavailable",
            "source": "latex2sympy",
            "reason": "latex2sympy2.latex2sympy is unavailable.",
        }

    parsed: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    witness_inputs = normalized_expression_witness_inputs((components.get("displays") or [])[:3])
    for expr in witness_inputs["fragments"]:
        try:
            parsed.append(
                {
                    "input": expr["original"],
                    "normalized": expr["normalized"],
                    "placeholders": expr["placeholders"],
                    "repr": repr(parser(expr["normalized"])),
                }
            )
        except Exception as exc:  # noqa: BLE001 - witness records parser failure.
            failures.append({"input": expr["original"], "normalized": expr["normalized"], "error": type(exc).__name__, "message": str(exc)[:300]})

    base = generated_standard_quantified_suggestion(block, components, findings)
    if not base or base.get("status") != "generated_suggestion_requires_review":
        return {
            "status": "not_generated",
            "source": "latex2sympy",
            "reason": "latex2sympy ran as an expression witness, but the conservative theorem-level template did not match.",
            "normalized_inputs": witness_inputs,
            "parsed": parsed,
            "failures": failures,
        }
    suggestion = dict(base)
    suggestion["source"] = "latex2sympy_assisted"
    suggestion["notes"] = [
        "latex2sympy supplied expression-level parse evidence where possible; theorem-level quantifier/assumption assembly uses the conservative Python template.",
        *base.get("notes", []),
    ]
    suggestion["latex2sympy"] = {"normalized_inputs": witness_inputs, "parsed": parsed, "failures": failures}
    return suggestion


def generated_standard_quantified_suggestions(block: FormalBlock, components: dict[str, Any], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    suggestions = [
        generated_standard_quantified_suggestion(block, components, findings),
        nltk_standard_quantified_suggestion(block, components, findings),
        latex2sympy_standard_quantified_suggestion(block, components, findings),
    ]
    return [suggestion for suggestion in suggestions if suggestion is not None]


def package_root_from_artifact(artifact: Path | None) -> Path | None:
    if artifact is None:
        return None
    artifact = artifact.resolve()
    if artifact.name != "artifact.yaml":
        return artifact.parent
    return artifact.parent.parent if artifact.parent.parent.exists() else artifact.parent


def latex_symbol_replace(text: str, symbol: str, replacement: str) -> str:
    if not symbol:
        return text
    return re.sub(rf"(?<![A-Za-z\\]){re.escape(symbol)}(?![A-Za-z])", lambda _match: replacement, text)


def predicate_name_to_label_slug(name: str) -> str:
    slug = re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower()
    return f"def:{slug}"


def definition_label_matches_predicate(label: str | None, predicate_name: str) -> bool:
    if label is None:
        return False
    if predicate_name_to_label_slug(predicate_name) == label:
        return True
    return (label, predicate_name) in {
        ("def:supremum", "LeastUpperBound"),
        ("def:infimum", "GreatestLowerBound"),
    }


def default_notation_registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "notation.yaml"


def load_operator_bridge_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or default_notation_registry_path()
    if not registry_path.exists():
        return {"operator_aliases": {}, "operator_bridges": [], "registry_path": str(registry_path)}
    data = read_yaml(registry_path)
    aliases: dict[str, dict[str, Any]] = {}
    for item in data.get("notation", []) or []:
        alias = item.get("operator_alias") if isinstance(item, dict) else None
        symbol = item.get("symbol") if isinstance(item, dict) else None
        if alias and symbol:
            aliases[str(symbol)] = {
                "notation_id": item.get("id"),
                "symbol": symbol,
                **alias,
            }
    return {
        "operator_aliases": aliases,
        "operator_bridges": data.get("operator_bridges", []) or [],
        "registry_path": str(registry_path),
    }


def load_predicate_unfolding_definitions(package_root: Path | None) -> dict[str, dict[str, Any]]:
    """Load deterministic predicate-to-quantified-definition unfoldings."""

    if package_root is None or not package_root.exists():
        return {}
    definitions: dict[str, dict[str, Any]] = {}
    for artifact_path in sorted(package_root.glob("*/artifact.yaml")):
        try:
            artifact = read_yaml(artifact_path)
        except Exception:  # noqa: BLE001 - ignore malformed sibling drafts.
            continue
        identity = artifact.get("identity") or {}
        if identity.get("kind") != "definition":
            continue
        logical_forms = artifact.get("logical_forms") or {}
        predicate_latex = str((logical_forms.get("predicate_reading") or {}).get("latex") or "")
        standard_latex = str((logical_forms.get("standard_quantified") or {}).get("latex") or "")
        if not predicate_latex or not standard_latex:
            continue
        for match in re.finditer(r"\\operatorname\{(?P<name>[A-Za-z][A-Za-z0-9]*)\}\((?P<args>[^()]*)\)", predicate_latex):
            name = match.group("name")
            if not definition_label_matches_predicate(identity.get("label"), name):
                continue
            parameters = [arg.strip() for arg in match.group("args").split(",") if arg.strip()]
            definitions[name] = {
                "predicate": name,
                "label": identity.get("label"),
                "artifact": str(artifact_path),
                "parameters": parameters,
                "standard_quantified": standard_latex,
            }
    return definitions


def split_predicate_args(raw: str) -> list[str]:
    args: list[str] = []
    current: list[str] = []
    depth = 0
    for char in raw:
        if char in "({[":
            depth += 1
        elif char in ")}]" and depth:
            depth -= 1
        if char == "," and depth == 0:
            value = "".join(current).strip()
            if value:
                args.append(value)
            current = []
        else:
            current.append(char)
    value = "".join(current).strip()
    if value:
        args.append(value)
    return args


def instantiate_unfolding(template: str, parameters: list[str], arguments: list[str]) -> str:
    instantiated = template.strip().rstrip(".")
    mapping: dict[str, str] = {}
    for parameter, argument in zip(parameters, arguments, strict=False):
        mapping[parameter] = argument
    if "P" in mapping and "S" not in mapping:
        mapping["S"] = mapping["P"]
    for parameter in sorted(mapping, key=len, reverse=True):
        instantiated = latex_symbol_replace(instantiated, parameter, mapping[parameter])
    return instantiated


def operator_to_predicate_bridge(latex: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry if registry is not None else load_operator_bridge_registry()
    aliases = registry.get("operator_aliases") or {}
    used: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []

    def predicate_call(symbol: str, result: str, set_arg: str, ambient: str) -> str | None:
        alias = aliases.get(symbol)
        if not alias:
            missing.append({"surface": symbol, "reason": "operator alias not available"})
            return None
        predicate = alias.get("result_predicate")
        if not predicate:
            missing.append({"surface": symbol, "reason": "operator alias has no result_predicate"})
            return None
        return rf"\operatorname{{{predicate}}}({result},{set_arg},{ambient})"

    def replace_sup_neg_inf(match: re.Match[str], bridge: dict[str, Any]) -> str:
        sup_set = match.group("sup_set").strip()
        inf_set = match.group("inf_set").strip()
        witness = str(bridge.get("witness_symbol") or "i")
        ambient = str(bridge.get("ambient_argument_default") or r"\mathbb{R}")
        parts: list[str] = []
        for expansion in bridge.get("expansions", []) or []:
            symbol = str(expansion.get("from_operator") or "")
            result = str(expansion.get("result") or "").replace("<witness>", witness)
            set_arg = str(expansion.get("set") or "").replace("<left_set>", sup_set).replace("<right_set>", inf_set)
            call = predicate_call(symbol, result, set_arg, ambient)
            if call:
                parts.append(call)
        if len(parts) != len(bridge.get("expansions", []) or []):
            return match.group(0)
        used.append(
            {
                "operator": str(bridge.get("id") or bridge.get("pattern") or "operator_bridge"),
                "surface": match.group(0),
                "introduced_witness": witness,
                "supremum_set": sup_set,
                "infimum_set": inf_set,
                "registry_path": str(registry.get("registry_path") or ""),
            }
        )
        return rf"(\exists {witness}\in {ambient})\bigl(" + r"\land".join(parts) + r"\bigr)"

    bridged = latex
    for bridge in registry.get("operator_bridges", []) or []:
        if bridge.get("pattern") != "sup_set_equals_negative_inf_set":
            continue
        left_symbol = str(bridge.get("left_operator") or r"\sup")
        right_symbol = str(bridge.get("right_operator") or r"\inf")
        pattern = rf"{re.escape(left_symbol)}\((?P<sup_set>[^()]*)\)\s*=\s*-{re.escape(right_symbol)}\s*(?P<inf_set>[A-Za-z][A-Za-z0-9]*)"
        bridged = re.sub(pattern, lambda match, bridge=bridge: replace_sup_neg_inf(match, bridge), bridged)
    if re.search(r"\\(?:sup|inf)\b", bridged):
        for match in re.finditer(r"\\(?:sup|inf)\b[^\\\s)\]]*", bridged):
            missing.append({"surface": match.group(0), "reason": "operator pattern not recognized"})
    return {
        "status": "bridged" if used else "not_bridged",
        "latex": bridged,
        "used_operators": used,
        "unbridged_operators": missing,
        "registry_path": str(registry.get("registry_path") or ""),
    }


def unfold_predicates_in_latex(
    latex: str,
    definitions: dict[str, dict[str, Any]],
    operator_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    used: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    changed = False
    operator_bridge = operator_to_predicate_bridge(latex, operator_registry)
    working_latex = operator_bridge["latex"]
    changed = operator_bridge["status"] == "bridged"

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        name = match.group("name")
        args = split_predicate_args(match.group("args"))
        definition = definitions.get(name)
        if definition is None:
            missing.append({"predicate": name, "surface": match.group(0), "reason": "definition artifact not available"})
            return match.group(0)
        parameters = definition.get("parameters") or []
        if len(args) < len(parameters):
            missing.append({"predicate": name, "surface": match.group(0), "reason": "arity mismatch"})
            return match.group(0)
        expanded = instantiate_unfolding(definition["standard_quantified"], parameters, args)
        changed = True
        used.append(
            {
                "predicate": name,
                "surface": match.group(0),
                "definition_label": definition["label"],
                "definition_artifact": definition["artifact"],
                "expanded": expanded,
            }
        )
        return rf"\bigl({expanded}\bigr)"

    unfolded = re.sub(r"\\operatorname\{(?P<name>[A-Za-z][A-Za-z0-9]*)\}\((?P<args>[^()]*)\)", replace, working_latex)
    return {
        "status": "unfolded" if changed else "not_unfolded",
        "latex": unfolded,
        "operator_bridge": operator_bridge,
        "used_definitions": used,
        "missing_definitions": missing,
    }


def attach_predicate_unfoldings(suggestions: list[dict[str, Any]], artifact: Path | None) -> None:
    definitions = load_predicate_unfolding_definitions(package_root_from_artifact(artifact))
    for suggestion in suggestions:
        latex = suggestion.get("latex")
        if not latex or suggestion.get("status") != "generated_suggestion_requires_review":
            continue
        suggestion["predicate_unfolding"] = unfold_predicates_in_latex(str(latex), definitions)


def camel_to_kebab(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower()


def dependency_label_for_predicate(name: str) -> str:
    return PREDICATE_DEPENDENCY_OVERRIDES.get(name, f"def:{camel_to_kebab(name)}")


def predicate_id_for_name(name: str) -> str:
    return f"pred:{camel_to_kebab(name)}"


def dependency_label_for_structure(name: str) -> str:
    return STRUCTURE_DEPENDENCY_OVERRIDES.get(name, f"def:{camel_to_kebab(name)}")


def dependency_labels_from_artifact(artifact: Path | None) -> set[str]:
    if artifact is None or not artifact.exists():
        return set()
    try:
        data = read_yaml(artifact)
    except Exception:  # noqa: BLE001 - dependency audit should not crash the ensemble.
        return set()
    edges = ((data.get("relationships") or {}).get("dependency_edges") or [])
    labels = {str(edge.get("target")) for edge in edges if edge.get("target")}
    return labels


def introduced_predicate_ids_from_artifact(artifact: Path | None) -> set[str]:
    if artifact is None or not artifact.exists():
        return set()
    try:
        data = read_yaml(artifact)
    except Exception:  # noqa: BLE001 - dependency audit should not crash the ensemble.
        return set()
    introduced: set[str] = set()
    for item in ((data.get("notation") or {}).get("introduced") or []):
        if isinstance(item, dict) and item.get("registry_predicate"):
            introduced.add(str(item["registry_predicate"]))
    reading = (data.get("logical_forms") or {}).get("predicate_reading") or {}
    if (data.get("identity") or {}).get("kind") == "definition":
        for predicate_id in reading.get("registry_predicates", []) or []:
            introduced.add(str(predicate_id))
    return introduced


def source_dependency_labels(text: str) -> set[str]:
    return {match.group("label") for match in HYPERREF_RE.finditer(text)}


def predicate_reading_dependency_inventory(components: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    predicate_readings = "\n".join(str(item) for item in components.get("predicate_reading") or [])
    predicates = sorted(set(re.findall(r"\\operatorname\{(?P<name>[A-Za-z][A-Za-z0-9]*)\}", predicate_readings)))
    structures = sorted(set(re.findall(r"\\mathsf\{(?P<name>[A-Za-z][A-Za-z0-9]*)\}", predicate_readings)))
    return {
        "predicates": [
            {"name": name, "expected_dependency": dependency_label_for_predicate(name)}
            for name in predicates
        ],
        "structures": [
            {"name": name, "expected_dependency": dependency_label_for_structure(name)}
            for name in structures
        ],
    }


def verify_predicate_reading_dependencies(block: FormalBlock, components: dict[str, Any], artifact: Path | None) -> dict[str, Any]:
    declared = source_dependency_labels(block.text) | dependency_labels_from_artifact(artifact)
    introduced_predicates = introduced_predicate_ids_from_artifact(artifact)
    inventory = predicate_reading_dependency_inventory(components)
    required: list[dict[str, str]] = []
    for kind in ("predicates", "structures"):
        for item in inventory[kind]:
            required.append({"kind": kind[:-1], **item})
    missing = []
    for item in required:
        expected = item["expected_dependency"]
        acceptable = {expected, *DEPENDENCY_LABEL_ALIASES.get(expected, [])}
        if item["kind"] == "predicate" and predicate_id_for_name(item["name"]) in introduced_predicates:
            continue
        if expected != block.label and not (acceptable & declared):
            missing.append(item)
    return {
        "status": "pass" if not missing else "fail",
        "declared_dependencies": sorted(declared),
        "required_dependencies": required,
        "missing_dependencies": missing,
        "suggested_dependency_additions": sorted({item["expected_dependency"] for item in missing}),
    }


def naive_facts(block: FormalBlock, components: dict[str, Any]) -> dict[str, Any]:
    math_text = "\n".join(components["standard_quantified"] or components["displays"] or [block.text])
    full = block.text
    predicates = sorted(predicate_operator_names(full))
    quantifiers = quantifiers_from_latex(math_text)
    return {
        "label": block.label,
        "environment_kind": block.env,
        "title": block.title,
        "quantifiers": quantifiers,
        "quantifier_sequence": [item["kind"] for item in quantifiers],
        "quantifier_variable_counts": {
            "forall": sum(item["variable_count"] for item in quantifiers if item["kind"] == "forall"),
            "exists": sum(item["variable_count"] for item in quantifiers if item["kind"] == "exists"),
        },
        "connectives": connective_shape(math_text + "\n" + full),
        "predicates": [{"name": name, "arity": None} for name in predicates],
        "structures": structures_from_text(full),
        "function_calls": function_calls(full),
        "let_assumptions": let_assumptions(full),
    }


def candidate_naive(block: FormalBlock, components: dict[str, Any]) -> AstCandidate:
    return AstCandidate("local_naive_driver", facts=naive_facts(block, components))


def comparison_core_text(block: FormalBlock, components: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("standard_quantified", "predicate_reading"):
        for item in components.get(key) or []:
            if item:
                parts.append("\\[\n" + item + "\n\\]")
    return "\n".join(parts) if parts else block.text


def candidate_source_regex(block: FormalBlock, components: dict[str, Any]) -> AstCandidate:
    facts = surface_regex_extract(comparison_core_text(block, components))
    return AstCandidate(
        "surface_regex",
        available=facts.available,
        notes=facts.notes,
        facts={
            "label": facts.label,
            "environment_kind": facts.environment_kind,
            "title": facts.title,
            "connectives": {
                "has_iff": facts.has_iff,
                "has_implies": facts.has_implies,
                "has_negation": facts.has_negation,
            },
            "quantifier_presence": {"forall": facts.has_forall, "exists": facts.has_exists},
            "predicates": [{"name": name, "arity": None} for name in sorted(facts.predicates)],
            "dependencies": sorted(facts.dependencies),
            "support_blocks": sorted(facts.support_blocks),
        },
    )


def candidate_displayed_math(block: FormalBlock, components: dict[str, Any]) -> AstCandidate:
    facts = displayed_math_extract(comparison_core_text(block, components))
    return AstCandidate(
        "displayed_math_regex",
        available=facts.available,
        notes=facts.notes,
        facts={
            "connectives": {
                "has_iff": facts.has_iff,
                "has_implies": facts.has_implies,
                "has_negation": facts.has_negation,
            },
            "quantifier_presence": {"forall": facts.has_forall, "exists": facts.has_exists},
            "predicates": [{"name": name, "arity": None} for name in sorted(facts.predicates)],
        },
    )


def candidate_nltk(block: FormalBlock) -> AstCandidate:
    if importlib.util.find_spec("nltk") is None:
        return AstCandidate("nltk_prose", available=False, notes=["nltk is not installed"])
    import nltk

    clean = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", strip_comments(block.text))
    try:
        tokens = nltk.word_tokenize(clean)
        tagged = nltk.pos_tag(tokens)
    except LookupError as exc:
        return AstCandidate("nltk_prose", available=False, notes=[f"nltk data missing: {exc}"])
    lowered = [token.lower() for token in tokens]
    return AstCandidate(
        "nltk_prose",
        facts={
            "quantifier_words": {
                "forall": sum(1 for token in lowered if token in {"every", "all", "each", "any"}),
                "exists": sum(1 for token in lowered if token in {"exists", "some"}),
            },
            "assumption_words": [token for token in lowered if token in {"let", "suppose", "assume", "given", "where"}],
            "tagged_tokens": tagged[:80],
        },
    )


def candidate_sympy(components: dict[str, Any]) -> AstCandidate:
    if importlib.util.find_spec("sympy") is None:
        return AstCandidate("sympy", available=False, notes=["sympy is not installed"])
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

    transformations = standard_transformations + (implicit_multiplication_application,)
    parsed = []
    failures = []
    witness_inputs = normalized_expression_witness_inputs(components["displays"][:5])
    for expr in witness_inputs["fragments"]:
        simple = expr["normalized"]
        try:
            parsed.append(
                {
                    "input": expr["original"],
                    "normalized": simple,
                    "placeholders": expr["placeholders"],
                    "srepr": str(parse_expr(simple, transformations=transformations, evaluate=False)),
                }
            )
        except Exception as exc:  # noqa: BLE001 - parser witness should record failure, not crash
            failures.append({"input": expr["original"], "normalized": simple, "error": type(exc).__name__})
    return AstCandidate("sympy", facts={"normalized_inputs": witness_inputs, "parsed": parsed, "failures": failures})


def candidate_latex2sympy(components: dict[str, Any]) -> AstCandidate:
    module_name = "latex2sympy2"
    if importlib.util.find_spec(module_name) is None:
        return AstCandidate("latex2sympy", available=False, notes=["latex2sympy2 is not installed"])
    try:
        module = __import__(module_name, fromlist=["latex2sympy"])
    except Exception as exc:  # noqa: BLE001 - optional witness may fail at import time.
        return AstCandidate(
            "latex2sympy",
            available=False,
            notes=[f"latex2sympy2 import failed: {type(exc).__name__}: {exc}"],
        )
    parser = getattr(module, "latex2sympy", None)
    if parser is None:
        return AstCandidate("latex2sympy", available=False, notes=["latex2sympy2.latex2sympy is unavailable"])
    parsed = []
    failures = []
    witness_inputs = normalized_expression_witness_inputs(components["displays"][:5])
    for expr in witness_inputs["fragments"]:
        try:
            parsed.append(
                {
                    "input": expr["original"],
                    "normalized": expr["normalized"],
                    "placeholders": expr["placeholders"],
                    "repr": repr(parser(expr["normalized"])),
                }
            )
        except Exception as exc:  # noqa: BLE001
            failures.append({"input": expr["original"], "normalized": expr["normalized"], "error": type(exc).__name__})
    return AstCandidate("latex2sympy", facts={"normalized_inputs": witness_inputs, "parsed": parsed, "failures": failures})


def candidate_python_ast(components: dict[str, Any]) -> AstCandidate:
    parsed = []
    failures = []
    for call in function_calls("\n".join(components["displays"]))[:10]:
        expr = f"{call['name']}({', '.join(f'v{index}' for index, _ in enumerate(call['arguments']))})"
        try:
            tree = py_ast.parse(expr, mode="eval")
            parsed.append({"input": expr, "ast": py_ast.dump(tree, include_attributes=False)})
        except SyntaxError as exc:
            failures.append({"input": expr, "error": str(exc)})
    return AstCandidate("python_ast", facts={"parsed": parsed, "failures": failures})


def candidate_sage(components: dict[str, Any]) -> AstCandidate:
    if not any(components["displays"]):
        return AstCandidate("sage_parser", available=False, notes=["no displayed math fragments"])
    sage = "sage"
    try:
        probe = subprocess.run([sage, "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        return AstCandidate("sage_parser", available=False, notes=["sage executable is not available"])
    if probe.returncode != 0:
        return AstCandidate("sage_parser", available=False, notes=["sage executable is not available"])
    # Keep this adapter intentionally tiny; a future Sage image can replace it
    # with a richer JSON exporter.
    expr = (components["displays"][0] or "").replace("^", "**")
    script = (
        "from sage.all import *\n"
        "from sage.misc.parser import Parser\n"
        "p=Parser(make_var=var, implicit_multiplication=True)\n"
        f"print(repr(p.parse({expr!r})))\n"
    )
    run = subprocess.run([sage, "-python", "-c", script], capture_output=True, text=True)
    if run.returncode != 0:
        return AstCandidate("sage_parser", available=False, notes=[run.stderr.strip()[:500]])
    return AstCandidate("sage_parser", facts={"parsed": [{"input": components["displays"][0], "repr": run.stdout.strip()}]})


def walk_ast(node: Any) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_ast(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_ast(value)


def candidate_artifact(path: Path) -> AstCandidate:
    data = read_yaml(path)
    nodes = list(walk_ast(data))
    quantifiers = []
    predicates = []
    structures = []
    for node in nodes:
        kind = node.get("kind")
        if kind in {"forall", "exists", "exists_unique"}:
            binder = node.get("binder") if isinstance(node.get("binder"), dict) else {}
            quantifiers.append(
                {
                    "kind": "exists" if kind == "exists_unique" else kind,
                    "variables": [str(binder.get("symbol") or binder.get("binder_id") or "")],
                    "variable_count": 1,
                    "domain": binder.get("domain") or node.get("restriction"),
                }
            )
        if kind == "predicate":
            args = node.get("arguments") if isinstance(node.get("arguments"), list) else []
            predicates.append({"name": str(node.get("predicate_id") or ""), "arity": len(args)})
        if kind in {"structure", "constant"} and (node.get("structure_id") or node.get("name")):
            structures.append({"name": str(node.get("structure_id") or node.get("name")), "kind": kind})
    facts = {
        "label": (data.get("identity") or {}).get("label"),
        "environment_kind": (data.get("identity") or {}).get("kind"),
        "title": (data.get("identity") or {}).get("title"),
        "quantifiers": quantifiers,
        "quantifier_sequence": [item["kind"] for item in quantifiers],
        "quantifier_variable_counts": {
            "forall": sum(item["variable_count"] for item in quantifiers if item["kind"] == "forall"),
            "exists": sum(item["variable_count"] for item in quantifiers if item["kind"] == "exists"),
        },
        "connectives": {
            "has_iff": any(node.get("kind") == "iff" for node in nodes),
            "has_implies": any(node.get("kind") == "implies" for node in nodes),
            "has_negation": any(node.get("kind") == "not" for node in nodes),
        },
        "predicates": predicates,
        "structures": structures,
    }
    return AstCandidate("semantic_artifact", facts=facts)


def simple_derivations(facts: dict[str, Any]) -> dict[str, Any]:
    connectives = facts.get("connectives") or {}
    return {
        "mechanical_negation_available": bool(facts.get("quantifiers") or connectives),
        "contrapositive_available": bool(connectives.get("has_implies")),
        "converse_available": bool(connectives.get("has_implies")),
        "inverse_available": bool(connectives.get("has_implies")),
        "equivalence_split_available": bool(connectives.get("has_iff")),
    }


def compare_candidates(candidates: list[AstCandidate]) -> tuple[str, int, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    available = [candidate for candidate in candidates if candidate.available]
    baselines = [candidate for candidate in available if candidate.source in {"local_naive_driver", "semantic_artifact"}]
    baseline = baselines[0] if baselines else (available[0] if available else None)
    if baseline is None:
        return "blocked", 0, [{"code": "NO_AST_CANDIDATES", "severity": "blocking", "message": "No AST candidates were available."}]
    base = baseline.facts

    def add(code: str, severity: str, message: str, field: str) -> None:
        findings.append({"code": code, "severity": severity, "message": message, "field": field})

    base_q_counts = base.get("quantifier_variable_counts") or {}
    for candidate in available:
        if candidate is baseline:
            continue
        facts = candidate.facts
        q_presence = facts.get("quantifier_presence") or {}
        q_counts = facts.get("quantifier_variable_counts") or {}
        for kind in ("forall", "exists"):
            if q_presence.get(kind) and not base_q_counts.get(kind):
                add("QUANTIFIER_MISSING_FROM_BASELINE", "error", f"{candidate.source} saw {kind} quantifier cues absent from {baseline.source}.", "quantifiers")
            if q_counts.get(kind, 0) and base_q_counts.get(kind, 0) and q_counts[kind] != base_q_counts[kind]:
                add("QUANTIFIER_VARIABLE_COUNT_DISAGREEMENT", "error", f"{candidate.source} counted {q_counts[kind]} {kind} variables but {baseline.source} counted {base_q_counts[kind]}.", "quantifier_variable_counts")
        for key in ("has_iff", "has_implies", "has_negation"):
            actual = (facts.get("connectives") or {}).get(key)
            expected = (base.get("connectives") or {}).get(key)
            if actual and not expected:
                add("CONNECTIVE_MISSING_FROM_BASELINE", "error", f"{candidate.source} saw {key} absent from {baseline.source}.", "connectives")

    # Artifact candidates should match the local naive/block-derived counts.
    naive = next((candidate for candidate in available if candidate.source == "local_naive_driver"), None)
    artifact = next((candidate for candidate in available if candidate.source == "semantic_artifact"), None)
    if naive and artifact:
        for kind in ("forall", "exists"):
            left = (naive.facts.get("quantifier_variable_counts") or {}).get(kind, 0)
            right = (artifact.facts.get("quantifier_variable_counts") or {}).get(kind, 0)
            if left != right:
                add("ARTIFACT_QUANTIFIER_VARIABLE_COUNT_MISMATCH", "error", f"Source TeX binds {left} {kind} variable(s), but artifact AST exposes {right}.", "quantifier_variable_counts")
        for key in ("has_iff", "has_implies", "has_negation"):
            left = (naive.facts.get("connectives") or {}).get(key)
            right = (artifact.facts.get("connectives") or {}).get(key)
            if left and not right:
                add("ARTIFACT_CONNECTIVE_MISSING", "error", f"Source TeX exposes {key}, but artifact AST does not.", "connectives")

    severity = {"blocking": 4, "error": 3, "warning": 2, "info": 1}
    score = sum(severity.get(item["severity"], 0) for item in findings)
    result = "fail" if any(item["severity"] in {"blocking", "error"} for item in findings) else ("pass_with_warnings" if findings else "pass")
    return result, score, findings


def structural_component_findings(block: FormalBlock, components: dict[str, Any]) -> list[dict[str, Any]]:
    return standard_quantified_block_findings(block, components)


def query_for_block(block: FormalBlock) -> str:
    return " ".join(item for item in [block.title, block.label.replace(":", " ")] if item)


def source_alignment(block: FormalBlock, args: argparse.Namespace) -> dict[str, Any]:
    roots = [path.resolve() for path in args.knowledge_root]
    source_profiles = args.source_profiles_root.resolve() if args.source_profiles_root else None
    source_indexes = [path.resolve() for path in args.source_index]
    if not roots and not source_profiles and not source_indexes:
        return {"status": "not_run", "reason": "no knowledge/source-profile indexes configured"}
    tool = Path(__file__).resolve().parent / "find_internal_theorem_evidence.py"
    command = [sys.executable, str(tool), "--query", query_for_block(block), "--format", "json", "--limit", str(args.source_limit)]
    for root in roots:
        command.extend(["--knowledge-root", str(root)])
    if source_profiles:
        command.extend(["--source-profiles-root", str(source_profiles)])
    for index in source_indexes:
        command.extend(["--source-index", str(index)])
    volume_key = args.volume or "volume-iii"
    command.extend(["--volume", volume_key])
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=env)
    if completed.returncode != 0:
        return {"status": "tool_error", "stderr": completed.stderr}
    payload = json.loads(completed.stdout)
    return {
        "status": "matched" if payload.get("hit_count") else "candidate_author_created_or_unindexed",
        "query": payload.get("query"),
        "hit_count": payload.get("hit_count"),
        "hits": payload.get("hits", []),
        "inputs": payload.get("inputs", {}),
    }


def report_for_block(block: FormalBlock, args: argparse.Namespace, artifact: Path | None = None) -> dict[str, Any]:
    components = component_tex(block)
    candidates = [
        candidate_naive(block, components),
        candidate_source_regex(block, components),
        candidate_displayed_math(block, components),
        candidate_nltk(block),
        candidate_sympy(components),
        candidate_latex2sympy(components),
        candidate_python_ast(components),
        candidate_sage(components),
    ]
    if artifact:
        candidates.append(candidate_artifact(artifact))
    result, score, findings = compare_candidates(candidates)
    structural_findings = structural_component_findings(block, components)
    findings.extend(structural_findings)
    if structural_findings and result == "pass":
        result = "fail"
    elif structural_findings and result == "pass_with_warnings":
        result = "fail"
    score += 3 * len(structural_findings)
    naive = next(candidate for candidate in candidates if candidate.source == "local_naive_driver")
    standard_quantified_suggestions = generated_standard_quantified_suggestions(block, components, findings)
    attach_predicate_unfoldings(standard_quantified_suggestions, artifact)
    dependency_verification = verify_predicate_reading_dependencies(block, components, artifact)
    for missing in dependency_verification["missing_dependencies"]:
        findings.append(
            {
                "code": "PREDICATE_READING_DEPENDENCY_MISSING",
                "severity": "error",
                "message": (
                    f"Predicate reading uses {missing['kind']} {missing['name']} but dependency "
                    f"{missing['expected_dependency']} is not declared."
                ),
                "field": "dependencies",
            }
        )
    if dependency_verification["missing_dependencies"] and result != "fail":
        result = "fail"
    score += 100 * len(dependency_verification["missing_dependencies"])
    standard_quantified_suggestion = next(
        (
            suggestion
            for suggestion in standard_quantified_suggestions
            if suggestion.get("source") == "python_conservative_heuristic"
        ),
        None,
    )
    return {
        "label": block.label,
        "kind": block.env,
        "title": block.title,
        "source_file": block.repo_relative_path,
        "line_start": block.line_start,
        "line_end": block.line_end,
        "result": result,
        "score": score,
        "components": components,
        "ast_candidates": [candidate.as_json() for candidate in candidates],
        "comparison_findings": findings,
        "standard_quantified_suggestion": standard_quantified_suggestion,
        "standard_quantified_suggestions": standard_quantified_suggestions,
        "dependency_verification": dependency_verification,
        "mechanical_derivations": simple_derivations(naive.facts),
        "source_alignment": source_alignment(block, args),
    }


def select_blocks(target: Path, repo_root: Path, labels: set[str], limit: int | None) -> list[FormalBlock]:
    blocks = formal_blocks(target, repo_root)
    if labels:
        blocks = [block for block in blocks if block.label in labels]
    if limit is not None:
        blocks = blocks[:limit]
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and compare deterministic semantic AST witnesses.")
    parser.add_argument("--target", type=Path, default=Path("volume-iii.tex"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--artifact", type=Path, help="Optional artifact.yaml to compare against a single selected block.")
    parser.add_argument("--knowledge-root", action="append", type=Path, default=[])
    parser.add_argument("--source-profiles-root", type=Path)
    parser.add_argument("--source-index", action="append", type=Path, default=[])
    parser.add_argument("--source-limit", type=int, default=5)
    parser.add_argument("--volume", help="Source-profile volume key, e.g. volume-iii. Defaults from repo name when possible.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    target = args.target.resolve()
    if args.source_profiles_root is None:
        sibling_source_profiles = repo_root.parent / "lra-source-profiles"
        if sibling_source_profiles.exists():
            args.source_profiles_root = sibling_source_profiles
    if args.volume is None and re.match(r"lra-volume-[ivx]+$", repo_root.name):
        args.volume = repo_root.name.removeprefix("lra-")
    blocks = select_blocks(target, repo_root, set(args.label), args.limit)
    if args.artifact and len(blocks) != 1:
        raise SystemExit("--artifact requires exactly one selected formal block")
    reports = [report_for_block(block, args, args.artifact.resolve() if args.artifact else None) for block in blocks]
    reports.sort(key=lambda item: (-int(item["score"]), item["label"]))
    payload = {
        "schema_version": "lra.semantic-ast-ensemble/1.0",
        "target": str(target),
        "repo_root": str(repo_root),
        "block_count": len(blocks),
        "reports": reports,
    }
    write_payload(args.output, payload, args.format)
    return 1 if any(report["result"] == "fail" for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
