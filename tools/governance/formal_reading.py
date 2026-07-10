r"""Trigger-dictionary loader for the formal_reading_required rule.

Trigger set = a fixed LOGIC FLOOR (symbols + English logic words) + CONCEPT SURFACE
FORMS for canonical predicates/objects/structures. The registry has no explicit
`surface_forms` field yet, so forms are derived from the CamelCase `name`
(CauchySequence -> "cauchy sequence"). Names are regex-extracted, NOT yaml-parsed,
because predicates.yaml can contain unquoted scalars (e.g. `formal: |x - c| < r`)
that break yaml.safe_load; regex extraction is robust to that. An explicit
`surface_forms:` list is honoured when present and parseable.

A small COMMON_NOUN_STOPLIST suppresses single-word derived forms too colloquial to
trigger safely. Multi-word and explicit forms are never stoplisted. Favours few false
alarms over completeness: a missed trigger is acceptable, a false alarm is not.
"""
from __future__ import annotations
import re
from pathlib import Path
from functools import lru_cache

LOGIC_FLOOR_WORDS = [
    "for all", "for every", "for each", "there exists", "there is a unique",
    "unique", "uniquely", "implies", "if and only if", "iff", "equivalent",
    "necessary", "sufficient", "for some",
]
LOGIC_FLOOR_SYMBOLS = [
    r"\forall", r"\exists", r"\implies", r"\iff", r"\Longleftrightarrow",
    r"\Rightarrow", r"\Leftrightarrow", r"\neg", r"\land", r"\lor", r"\equiv",
    "\u2200", "\u2203", "\u21d2", "\u21d4", "\u00ac", "\u2227", "\u2228", "\u2261",
]
# single-word derived forms too colloquial to trigger safely (until explicit surface_forms exist)
COMMON_NOUN_STOPLIST = {
    "set", "term", "function", "variable", "point", "element", "relation",
    "sequence", "limit", "order", "field", "space", "map", "value", "bound",
    "number", "formula", "language", "model", "structure", "operation", "symbol",
    "constant", "domain", "range", "image", "graph", "system", "form", "class",
}
_NAME_RE = re.compile(r"^\s*-?\s*name:\s*([A-Za-z][A-Za-z0-9]*)\s*$", re.M)

def camel_to_words(name: str) -> str:
    # CauchySequence -> "cauchy sequence"; WellFormedFormula -> "well formed formula"
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return s.lower().strip()

def _ingest_text(text: str, forms: set, rep: dict):
    for name in _NAME_RE.findall(text):
        rep["total_entries"] += 1
        form = camel_to_words(name)
        if (" " not in form) and (form in COMMON_NOUN_STOPLIST or len(form) < 4):
            rep["stoplisted_single_word"] += 1; continue
        forms.add(form); rep["derived_from_name"] += 1

def load_concept_surface_forms(canonical_dir):
    """Return (sorted surface forms, gap report). Regex-extracts predicate (and, when
    present, structure) names from the canonical files and derives surface forms."""
    canonical_dir = Path(canonical_dir)
    forms: set = set()
    rep = {"total_entries": 0, "derived_from_name": 0, "stoplisted_single_word": 0,
           "explicit_surface_forms": 0, "structures_yaml_present": False}
    pred = canonical_dir / "predicates.yaml"
    if pred.exists():
        _ingest_text(pred.read_text(encoding="utf-8"), forms, rep)
    struct = canonical_dir / "structures.yaml"
    if struct.exists():
        rep["structures_yaml_present"] = True
        _ingest_text(struct.read_text(encoding="utf-8"), forms, rep)
    rep["form_count"] = len(forms)
    return sorted(forms), rep

@lru_cache(maxsize=4096)
def _word_re(form: str):
    pat = re.escape(form).replace(r"\ ", r"[\s-]+")   # space -> space-or-hyphen
    return re.compile(r"(?<![\w-])" + pat + r"(?![\w-])", re.I)

_LOGIC_WORD_RES = [(w, re.compile(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", re.I))
                   for w in LOGIC_FLOOR_WORDS]

def find_triggers(text: str, surface_forms) -> list:
    """Whole-word, hyphen/space-tolerant, case-insensitive trigger detection."""
    hits = []
    for w, rx in _LOGIC_WORD_RES:
        if rx.search(text): hits.append(w)
    for sym in LOGIC_FLOOR_SYMBOLS:
        if sym in text: hits.append(sym)
    for form in surface_forms:
        if _word_re(form).search(text): hits.append(form)
    return hits

def has_formal_reading(decoration: str) -> bool:
    return bool(re.search(r"\\begin\{remark\*?\}\[Standard quantified statement\]", decoration, re.I))

def has_predicate_reading(decoration: str) -> bool:
    return bool(re.search(r"\\begin\{remark\*?\}\[Predicate reading\]", decoration, re.I))

def standard_quantified_statement_bodies(decoration: str) -> list[str]:
    return [
        match.group("body")
        for match in re.finditer(
            r"\\begin\{remark\*?\}\[Standard quantified statement\](?P<body>[\s\S]*?)\\end\{remark\*?\}",
            decoration,
            re.I,
        )
    ]

def count_quantified_binders(text: str) -> int:
    r"""Count variables bound by \forall and \exists in a quantified display."""
    text = re.sub(r"\\(?:,|;|:|quad|qquad|enspace|thinspace|medspace|!)", " ", text)
    text = re.sub(r"\\text\{[^{}]*\}", " ", text)
    spans = list(re.finditer(r"\\(?:forall|exists)\b", text))
    count = 0
    for index, match in enumerate(spans):
        start = match.end()
        end = spans[index + 1].start() if index + 1 < len(spans) else len(text)
        segment = text[start:end]
        segment = re.split(
            r"\\(?:Rightarrow|Longrightarrow|Leftrightarrow|Longleftrightarrow|implies|iff|land|lor)\b|[.;:]",
            segment,
            maxsplit=1,
        )[0]
        segment = re.split(r"\\in\b|\\notin\b|\\subseteq\b|\\leq\b|\\geq\b|=|<|>|\\mid\b|\|", segment, maxsplit=1)[0]
        segment = re.sub(r"\\[A-Za-z]+", " ", segment)
        segment = segment.replace("{", " ").replace("}", " ")
        names = re.findall(r"[A-Za-z](?:_\{[^{}]+\}|_[A-Za-z0-9]+)?(?:\^\{[^{}]+\}|\^[A-Za-z0-9]+)?", segment)
        count += len(names)
    return count

def is_marked_simple(text: str) -> bool:
    return "lra:simple" in text.lower()
