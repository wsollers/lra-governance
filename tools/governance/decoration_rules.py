#!/usr/bin/env python3
"""LRA decoration rule engine (composable).

Each rule is a small pure function registered via @rule (block rules) or
@file_rule (whole-file rules). A runner applies every applicable rule. Adding a
rule = adding one function; each is independently testable. Existing checks from
audit_latex_decoration.py port in as rule functions (logic moved, not rewritten).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable

from rules.decoration import dependencies_block, interpretation_block, labels
from rules.proofs import proof_stub_state
from rules.routing import print_edition_inputs

# ---- canonical vocabulary (from common/boxes.tex + decoration-box-standards) ----
AUDITED_ENVS = {"definition":"def","axiom":"ax","theorem":"thm","lemma":"lem",
                "proposition":"prop","corollary":"cor"}
BOX_MACRO = {e: e+"box" for e in AUDITED_ENVS}          # definition -> definitionbox, ...
STATEMENT_PREFIXES = {"def","ax","thm","lem","prop","cor"}

# ---- data types ----
@dataclass
class Issue:
    code: str; message: str; severity: str = "warning"; line: int = 0

@dataclass
class Block:
    environment: str; title: str; line_start: int; line_end: int
    text: str; decoration: str; prelines: list[str]

@dataclass
class Context:
    """Per-run config. Volume overlays can flip these (e.g. plain-style Vol IV)."""
    require_box: bool = False             # opt-in audit for statements explicitly expected to be boxed
    unwrapped_severity: str = "warning"   # severity when require_box and none found
    predicates: set[str] = field(default_factory=set)
    breadcrumb_max_leading_exposition: int = 0  # 'very first content' = 0; set 1 to allow one exposition
    toolkit_max_leading_exposition: int = 1     # toolkit may sit one exposition after its \subsection
    formal_reading: bool = True                 # run formal_reading_required
    concept_surface_forms: list = field(default_factory=list)  # predicate/object/structure surface forms

# ---- block-level rule registry ----
Rule = Callable[[Block, Context], Iterable[Issue]]
_RULES: list[tuple[str, frozenset, Rule]] = []
def rule(id: str, envs):
    def deco(fn: Rule):
        _RULES.append((id, frozenset(envs), fn)); return fn
    return deco
def run_rules(block: Block, ctx: Context) -> list[Issue]:
    out: list[Issue] = []
    for _id, envs, fn in _RULES:
        if block.environment in envs:
            out.extend(fn(block, ctx))
    return out

# ---- parsing (ported from audit_latex_decoration.py) ----
BEGIN_RE = re.compile(r"\\begin\{(?P<env>" + "|".join(map(re.escape, AUDITED_ENVS)) + r")\}(?:\[(?P<title>[^\]]*)\])?")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
def _line(text, idx): return text.count("\n",0,idx)+1
def extract_blocks(text: str) -> list[Block]:
    blocks=[]
    for m in BEGIN_RE.finditer(text):
        env=m.group("env"); title=(m.group("title") or "").strip()
        em=re.compile(r"\\end\{%s\}"%re.escape(env)).search(text, m.end())
        if not em: continue
        body=text[m.start():em.end()]
        nxt=BEGIN_RE.search(text, em.end()); deco=text[em.end():(nxt.start() if nxt else len(text))]
        prelines=text[:m.start()].splitlines()[-10:]
        blocks.append(Block(env,title,_line(text,m.start()),_line(text,em.end()),body,deco,prelines))
    return blocks

def _has(deco, names):
    low=deco.lower(); return any(n in low for n in names)
def _dep_window(deco):
    mm=re.search(r"\\begin\{remark\*?\}\[Dependencies\](?P<b>.*?)\\end\{remark\*?\}",deco,re.DOTALL|re.I)
    return mm.group("b") if mm else ""

def _adapt(findings):
    if not findings:
        return
    for finding in findings:
        yield Issue(finding.code, finding.message, finding.severity, finding.line)

# ================= BLOCK RULES =================

# --- the discovered box rule (semantic / raw-old / wrong / neither) ---
def _classify_wrapper(prelines: list[str], env: str) -> str:
    expected = BOX_MACRO[env]
    for line in reversed(prelines):
        s=line.strip()
        if not s: continue
        if re.search(r"\\begin\{"+re.escape(expected)+r"\}", line): return "semantic"
        if env == "definition" and re.search(r"\\begin\{definitionalbox\}", line): return "semantic"
        if re.search(r"\\begin\{tcolorbox\}", line):                 return "raw"
        if re.search(r"\\begin\{(?:definition|definitional|axiom|theorem|lemma|proposition|corollary)box\}", line):
            return "wrong_box"
        if re.search(r"\\end\{", line):                              return "none"
        if re.search(r"\\begin\{", line):                            return "none"
        # else: tcolorbox option continuation / prose -> keep scanning within window
    return "none"

@rule("math_box_wrapper", AUDITED_ENVS)
def math_box_wrapper(b: Block, ctx: Context):
    w=_classify_wrapper(b.prelines, b.environment)
    if w=="semantic": return
    if w=="raw":
        yield Issue("raw_tcolorbox_wrapper",
            f"{b.environment} is wrapped in a hand-rolled tcolorbox; use "
            f"\\begin{{{BOX_MACRO[b.environment]}}}{{...}} from common/boxes.tex (no inline colback/arc/6pt).",
            "error", b.line_start)
    elif w=="wrong_box":
        yield Issue("wrong_box_macro",
            f"{b.environment} is boxed with a non-matching box macro; expected {BOX_MACRO[b.environment]}.",
            "error", b.line_start)
    else:  # none
        if ctx.require_box:
            yield Issue("unwrapped_math_env",
                f"{b.environment} is not wrapped in {BOX_MACRO[b.environment]} (neither semantic box nor legacy tcolorbox). "
                f"Use require_box only for targeted audits of statements explicitly expected to be boxed.",
                ctx.unwrapped_severity, b.line_start)

# --- ported verbatim from analyze_block() (logic unchanged, relocated) ---
@rule("missing_label", AUDITED_ENVS)
def missing_label(b: Block, ctx: Context):
    yield from _adapt(labels.check_missing_label(b, ctx))

@rule("wrong_label_prefix", AUDITED_ENVS)
def wrong_label_prefix(b: Block, ctx: Context):
    yield from _adapt(labels.check_label_prefix(b, ctx))

@rule("missing_interpretation", AUDITED_ENVS)
def missing_interpretation(b: Block, ctx: Context):
    yield from _adapt(interpretation_block.check(b, ctx))

@rule("missing_dependencies", AUDITED_ENVS)
def missing_dependencies(b: Block, ctx: Context):
    yield from _adapt(dependencies_block.check(b, ctx))

# (remaining analyze_block checks port the same way: one function each.)

from formal_reading import (
    count_quantified_binders,
    find_triggers,
    has_formal_reading,
    has_predicate_reading,
    is_marked_simple,
    standard_quantified_statement_bodies,
)

@rule("formal_reading_required", AUDITED_ENVS)
def formal_reading_required(b: Block, ctx: Context):
    """Every formal statement needs a Standard quantified statement.
    Trigger hits still catch invalid lra:simple markers."""
    if not ctx.formal_reading:
        return
    triggers = find_triggers(b.text, ctx.concept_surface_forms)
    uniq = sorted(set(triggers))
    simple = is_marked_simple(b.text + b.decoration)
    reading = has_formal_reading(b.decoration)
    if simple and triggers:
        yield Issue("simple_but_triggers",
            f"Marked simple but invokes {uniq[:4]}; naming a registered concept or logic "
            f"operator means it is not simple.", "error", b.line_start)
    if not reading:
        yield Issue("formal_reading_missing",
            "Formal statement has no Standard quantified statement formal reading.",
            "error", b.line_start)

# ================= FILE-LEVEL RULES =================
# Whole-file invariants: breadcrumb/toolkit placement, structural-roadmap purge.
# Signature (text, info, ctx) -> Issues. `info.kind` is computed by the CLI via
# _targeting (chapter_index | section_note | other); tests construct it directly.

@dataclass
class FileInfo:
    path: str
    kind: str = "other"      # "chapter_index" | "section_note" | "other"

FileRule = Callable[[str, FileInfo, "Context"], Iterable[Issue]]
_FILE_RULES: list[tuple[str, FileRule]] = []
def file_rule(id: str):
    def deco(fn: FileRule):
        _FILE_RULES.append((id, fn)); return fn
    return deco
def run_file_rules(text: str, info: FileInfo, ctx: Context) -> list[Issue]:
    out: list[Issue] = []
    for _id, fn in _FILE_RULES:
        out.extend(fn(text, info, ctx))
    return out

# --- positional event scan (shared by breadcrumb + toolkit placement) ---
# Events are (kind, line, level). Machinery/comments/blank skipped. exposition and
# toolkitbox collapse to a single ('exposition'|'toolkit', start_line, '') event.
_MACHINERY = re.compile(
    r"\\(input|include|LRAExcludeFromPrintEditionBegin|LRAExcludeFromPrintEditionEnd|label|index|phantomsection|addcontentsline|clearpage|newpage|FloatBarrier)\b"
)
_HEADING   = re.compile(r"\\(chapter|section|subsection|subsubsection)\b")
_ENV_BEG   = re.compile(r"\\begin\{(exposition|toolkitbox)\}")
_ENV_END   = re.compile(r"\\end\{(exposition|toolkitbox)\}")
_BREAD     = re.compile(r"\\breadcrumb\{")
_ENV_NAME  = {"exposition":"exposition","toolkitbox":"toolkit"}

def _events(text: str):
    events=[]; cur_env=None; env_line=0
    for n,line in enumerate(text.splitlines(),1):
        s=line.strip()
        if cur_env:
            m=_ENV_END.search(line)
            if m and m.group(1)==cur_env:
                events.append((_ENV_NAME[cur_env], env_line, "")); cur_env=None
            continue
        if not s or s.startswith("%"): continue
        mb=_ENV_BEG.search(line)
        if mb: cur_env=mb.group(1); env_line=n; continue
        if _MACHINERY.search(line) and not _BREAD.search(line): continue
        mh=_HEADING.search(line)
        if mh: events.append(("heading", n, mh.group(1))); continue
        if _BREAD.search(line): events.append(("breadcrumb", n, "")); continue
        if re.search(r"\\stubstatus\b", line): events.append(("stubstatus", n, "")); continue
        events.append(("content", n, ""))
    return events

# ---------- breadcrumb: present, very-first-content, chapter-index only ----------
@file_rule("proof_stub_structure_blank")
def proof_stub_structure_blank(text: str, info: FileInfo, ctx: Context):
    yield from _adapt(proof_stub_state.check(text, info, ctx))

@file_rule("print_edition_inputs")
def print_edition_input_routes(text: str, info: FileInfo, ctx: Context):
    yield from _adapt(print_edition_inputs.check(text, info, ctx))

@file_rule("breadcrumb_placement")
def breadcrumb_placement(text: str, info: FileInfo, ctx: Context):
    ev=_events(text)
    bc=[e for e in ev if e[0]=="breadcrumb"]
    if info.kind != "chapter_index":
        for e in bc:
            yield Issue("breadcrumb_misplaced",
                "Breadcrumb attaches only at the chapter entry-point index.tex; found one here.",
                "error", e[1])
        return
    if not bc:
        yield Issue("breadcrumb_missing",
            "Chapter entry-point index.tex has no \\breadcrumb{...}; it must be the first content.",
            "error"); return
    if len(bc) > 1:
        yield Issue("breadcrumb_duplicate",
            f"Chapter index has {len(bc)} breadcrumbs; exactly one is allowed.", "error", bc[1][1])
    first_idx=next(i for i,e in enumerate(ev) if e[0]=="breadcrumb")
    before=ev[:first_idx]
    headings=[e for e in before if e[0]=="heading"]
    expos=[e for e in before if e[0]=="exposition"]
    contents=[e for e in before if e[0]=="content"]
    if len(headings) > 1:
        yield Issue("breadcrumb_not_first","More than one heading precedes the breadcrumb.","error",bc[0][1])
    if contents:
        yield Issue("breadcrumb_not_first",
            "Non-heading content precedes the breadcrumb; it must be the very first content.","error",contents[0][1])
    if len(expos) > ctx.breadcrumb_max_leading_exposition:
        yield Issue("breadcrumb_leading_exposition",
            f"{len(expos)} exposition block(s) precede the breadcrumb; max allowed is "
            f"{ctx.breadcrumb_max_leading_exposition} (strict 'very first content').","error",expos[0][1])

@file_rule("breadcrumb_format")
def breadcrumb_format(text: str, info: FileInfo, ctx: Context):
    if re.search(r"\\begin\{tcolorbox\}", text) and "colback=breadcrumb" in text \
       and "\\breadcrumb{" not in text:
        yield Issue("breadcrumb_hand_rolled",
            "Breadcrumb is a hand-rolled tcolorbox (breadcrumb palette) instead of the \\breadcrumb{...} macro.","error")

# ---------- chapter index: chapter, label, breadcrumb, notes, proofs, capstone ----------
_CHAPTER_LINE_RE = re.compile(r"\\chapter(?!\*)(?:\[[^\]]*\])?\{.*\}$")
_LABEL_LINE_RE = re.compile(r"\\label\{(?:ch|chap):[a-z0-9-]+\}$")
_BREADCRUMB_LINE_RE = re.compile(r"\\breadcrumb\{.*\}\{.*\}\{.*\}\{.*\}$")

def _chapter_root_from_index(posix: str) -> str | None:
    parts = posix.split("/")
    if len(parts) < 3 or parts[-1] != "index.tex":
        return None
    for i, part in enumerate(parts[:-1]):
        if re.fullmatch(r"volume-(?:i|ii|iii|iv|v|vi|vii|viii)", part):
            return "/".join(parts[i:-1])
    return None

def _significant_lines(text: str):
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = _strip_comment(raw).strip()
        if stripped:
            yield line_no, stripped

@file_rule("chapter_index_shape")
def chapter_index_shape(text: str, info: FileInfo, ctx: Context):
    if info.kind != "chapter_index":
        return
    root = _chapter_root_from_index(_posix(info))
    if root is None:
        return
    expected = [
        ("chapter", _CHAPTER_LINE_RE, "non-starred \\chapter{...}"),
        ("label", _LABEL_LINE_RE, "\\label{chap:...} or \\label{ch:...}"),
        ("breadcrumb", _BREADCRUMB_LINE_RE, "\\breadcrumb{...}{...}{...}{...}"),
        ("notes_input", re.compile(rf"\\input\{{{re.escape(root)}/notes/index\}}$"), f"\\input{{{root}/notes/index}}"),
        ("exclude_begin", re.compile(r"\\LRAExcludeFromPrintEditionBegin$"), "\\LRAExcludeFromPrintEditionBegin"),
        ("proofs_heading", re.compile(r"\\section\*\{Proofs\}$"), "\\section*{Proofs}"),
        ("proofs_input", re.compile(rf"\\input\{{{re.escape(root)}/proofs/index\}}$"), f"\\input{{{root}/proofs/index}}"),
        ("capstone_heading", re.compile(r"\\section\*\{Capstone\}$"), "\\section*{Capstone}"),
        ("capstone_input", re.compile(rf"\\input\{{{re.escape(root)}/proofs/exercises/index\}}$"), f"\\input{{{root}/proofs/exercises/index}}"),
        ("exclude_end", re.compile(r"\\LRAExcludeFromPrintEditionEnd$"), "\\LRAExcludeFromPrintEditionEnd"),
    ]
    lines = list(_significant_lines(text))
    if len(lines) != len(expected):
        detail = "; ".join(pattern for _, _, pattern in expected)
        line = lines[min(len(lines), len(expected))][0] if len(lines) > len(expected) else 0
        yield Issue(
            "chapter_index_shape",
            f"Chapter index must contain exactly this skeleton, with no extra rendered content: {detail}.",
            "error",
            line,
        )
        return
    for (line_no, line), (name, pattern, expected_text) in zip(lines, expected):
        if not pattern.fullmatch(line):
            yield Issue(
                "chapter_index_shape",
                f"Chapter index layer {name} should be {expected_text}.",
                "error",
                line_no,
            )

# ---------- toolkit: may exist only in notes routers, right after heading (<=1 exposition) ----------
@file_rule("toolkit_placement")
def toolkit_placement(text: str, info: FileInfo, ctx: Context):
    topic, role = _notes_topic_and_role(_posix(info))
    ev=_events(text)
    for i,(kind,ln,lvl) in enumerate(ev):
        if kind != "toolkit": continue
        if role not in {"topic_index", "notes_index"}:
            yield Issue("toolkit_not_in_notes_router",
                "Toolkit boxes belong in notes/<topic>/index.tex routers, not note body files or chapter routers.",
                "error", ln)
            continue
        j=i-1; expos=0
        while j>=0 and ev[j][0] in {"exposition", "toolkit"}:
            if ev[j][0] == "exposition":
                expos+=1
            j-=1
        prev = ev[j] if j>=0 else None
        if expos > ctx.toolkit_max_leading_exposition:
            yield Issue("toolkit_leading_exposition",
                f"{expos} exposition block(s) between subsection and toolkit; max allowed is "
                f"{ctx.toolkit_max_leading_exposition}.","error",ln)
        if prev is None or not (prev[0]=="heading" and prev[2] in ("section", "subsection")):
            yield Issue("toolkit_misplaced",
                "Toolkit must sit at the top of a section or \\subsection (at most one exposition between); "
                "found in another position.","error",ln)

@file_rule("toolkit_content")
def toolkit_content(text: str, info: FileInfo, ctx: Context):
    for m in re.finditer(r"\\begin\{toolkitbox\}.*?\\end\{toolkitbox\}", text, re.DOTALL):
        body = m.group(0)
        line = text.count("\n",0,m.start())+1
        tabulars = list(_tabulars(body))
        if not tabulars:
            yield Issue(
                "toolkit_missing_table",
                "Toolkit boxes must contain a two-column quick-reference table.",
                "error",
                line,
            )
        for tabular_start, spec, table_body in tabulars:
            table_line = text.count("\n", 0, m.start() + tabular_start) + 1
            if _tabular_column_count(spec) != 2:
                yield Issue(
                    "toolkit_table_not_two_columns",
                    "Toolkit quick-reference tables must have exactly two columns: linked name and Meaning.",
                    "error",
                    table_line,
                )
            headers = _table_headers(table_body)
            if len(headers) < 2:
                yield Issue(
                    "toolkit_table_header_missing",
                    "Toolkit quick-reference tables must start with headers for linked name and Meaning.",
                    "error",
                    table_line,
                )
            else:
                if _normalize_header(headers[0]) != "name":
                    yield Issue(
                        "toolkit_first_column_not_name",
                        "Toolkit quick-reference tables must use Name as the first column header.",
                        "error",
                        table_line,
                    )
                if _normalize_header(headers[1]) != "meaning":
                    yield Issue(
                        "toolkit_second_column_not_meaning",
                        "Toolkit quick-reference tables must use Meaning as the second column header.",
                        "error",
                        table_line,
                    )
        if re.search(r"\\begin\{(definition|theorem|lemma|proposition|corollary|axiom|proof)\}", body):
            yield Issue("toolkit_contains_formal",
                "Toolkit box contains a formal environment; a toolkit orients (lists labels) and "
                "must not state definitions, theorems, or proofs.","error", line)
        if re.search(r"\\textbf\{Detail\}", body):
            yield Issue("toolkit_detail_column",
                "Toolkit quick-reference tables must put the hyperref on the leading concept/row label "
                "and omit the Detail column.","error", line)
        elif re.search(
            r"&\s*\\hyperref\[[^\]]+\]\{[^{}]*(?:Def|Thm|Prop|Lem|Cor|Ax|Rem|Ex|downarrow|Down)[^{}]*\}\s*\\\\",
            body,
        ):
            yield Issue("toolkit_detail_link_cell",
                "Toolkit quick-reference links belong on the leading concept/row label, not in a trailing detail cell.",
                "error", line)


def _tabulars(body: str):
    begin = r"\begin{tabular}"
    end = r"\end{tabular}"
    position = 0
    while True:
        start = body.find(begin, position)
        if start == -1:
            return
        spec_start = body.find("{", start + len(begin))
        if spec_start == -1:
            return
        spec_end = _balanced_group_end(body, spec_start)
        if spec_end is None:
            return
        end_start = body.find(end, spec_end)
        if end_start == -1:
            return
        yield start, body[spec_start + 1 : spec_end - 1], body[spec_end:end_start]
        position = end_start + len(end)


def _balanced_group_end(text: str, start: int) -> int | None:
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif char == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _tabular_column_count(spec: str) -> int:
    count = 0
    index = 0
    while index < len(spec):
        char = spec[index]
        if char in "lcr":
            count += 1
            index += 1
        elif char in "pmb" and index + 1 < len(spec) and spec[index + 1] == "{":
            end = _balanced_group_end(spec, index + 1)
            count += 1
            index = end if end is not None else index + 1
        elif char in "| @!<>":
            index += 1
        else:
            index += 1
    return count


def _table_headers(table_body: str) -> list[str]:
    match = re.search(r"(?P<row>.*?)(?:\\\\|\\cr)", table_body, re.DOTALL)
    if not match:
        return []
    return re.findall(r"\\textbf\{([^}]+)\}", match.group("row"))


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip()).lower()

@file_rule("toolkit_format")
def toolkit_format(text: str, info: FileInfo, ctx: Context):
    for m in re.finditer(r"\\begin\{tcolorbox\}\[(.*?)\]", text, re.DOTALL):
        if "oolkit" in m.group(1):
            yield Issue("toolkit_hand_rolled",
                "Toolkit rendered as a raw tcolorbox; use \\begin{toolkitbox}{...} from structural-presentations.tex.",
                "error", text.count("\n",0,m.start())+1)

# ---------- retired roadmap / role: removed globally ----------
_ROADMAP = re.compile(r"[Ss]tructural\s+[Rr]oadmap")
_ROLE    = re.compile(r"[Ss]tructural\s+[Rr]ole")
@file_rule("structural_roadmap_purge")
def structural_roadmap_purge(text: str, info: FileInfo, ctx: Context):
    for n,line in enumerate(text.splitlines(),1):
        if _ROADMAP.search(line):
            yield Issue("structural_roadmap_present",
                "Retired roadmap text is present; remove the block or wording.","error",n)
        if _ROLE.search(line):
            yield Issue("structural_role_present",
                "Retired role text is present; remove the block or wording.","error",n)

# ============================================================
# Integrated structural rule coverage.
#   block_discipline   -> top_level_prose, unexpected_top_level_environment,
#                         plain_remark_or_example, unclosed_environment
#   label_quality      -> weak_label_slug, ocr_like_label (prefix/presence stay
#                         with the engine's existing label rule -- no duplication)
#   capstone_structure -> missing_capstone_{phantomsection,label,box,theorem,
#                         dependencies_to_state,dependencies_to_prove,
#                         dependency_ceiling,dependencies}, invalid_capstone_box_count
# Cross-file capstone routing (unrouted_capstone, capstone_not_last) is deferred to
# the routing fold-in; it needs chapter context this per-file engine lacks.
# ============================================================
_FORMAL_BOX_ENVS = {"definitionbox","definitionalbox","axiombox","theorembox","lemmabox","propositionbox","corollarybox"}
_STARRED_RESTATEMENT_ENVS = {"theorem*","lemma*","proposition*","corollary*"}
_ALLOWED_NOTE_TOP_ENVS = _FORMAL_BOX_ENVS | {
    "remark*","example*","exposition","dependencies","tcolorbox","toolkitbox","modelbox",
    "signaturebox","topicbox","figure","longtable","tabular","tabularx","itemize",
    "enumerate","description","quote","center","tikzpicture","lra-not-visible",
} | set(AUDITED_ENVS)
_ALLOWED_PROOF_TOP_ENVS = {"remark*", *_STARRED_RESTATEMENT_ENVS, "proof", "dependencies"}
_BEGIN_ENV_RE = re.compile(r"\\begin\{([^{}]+)\}(?:\[[^\]]*\])?")
_END_ENV_RE   = re.compile(r"\\end\{([^{}]+)\}")
_PLAIN_BLOCK_RE = re.compile(r"\\begin\{(remark|example)\}(?!\*)")
_TOP_LEVEL_COMMANDS = ("\\chapter","\\section","\\subsection","\\subsubsection",
    "\\paragraph","\\input","\\include","\\label","\\newpage","\\clearpage",
    "\\phantomsection","\\noindent","\\FloatBarrier","\\LRAProofFor",
    "\\LRAExcludeFromPrintEditionBegin","\\LRAExcludeFromPrintEditionEnd","\\NoLocalDependencies","\\DefinitionalRoot",
    "\\medskip","\\smallskip","\\bigskip","\\vspace")
_IGNORED_LABEL_PREFIXES = {"ch","sec","subsec","toc"}
_BAD_LABEL_PARTS = {"the","following","this","with","therefore","and","or","let","denote","page"}
_TCOLORBOX_RE = re.compile(r"\\begin\{tcolorbox\}(?:\[[\s\S]*?\])?")

def _strip_comment(line: str) -> str:
    escaped=False; out=[]
    for ch in line:
        if ch=="\\":
            escaped=not escaped; out.append(ch); continue
        if ch=="%" and not escaped: break
        escaped=False; out.append(ch)
    return "".join(out)

def strip_latex_comments(text: str) -> str:
    """Strip LaTeX line comments while preserving line numbers."""
    return "\n".join(_strip_comment(line) for line in text.splitlines())

def _uncommented(text: str) -> str:
    return strip_latex_comments(text)

def _line_at(text: str, pos: int) -> int:
    return text.count("\n",0,pos)+1

def _top_level_allowed_line(line: str) -> bool:
    s=_strip_comment(line).strip()
    return (not s) or s.startswith("%") or s.startswith(_TOP_LEVEL_COMMANDS)

@file_rule("block_discipline")
def block_discipline(text: str, info: FileInfo, ctx: Context):
    posix = info.path.replace("\\","/")
    if posix.split("/")[-1].startswith("figure-"):
        return
    is_note  = "/notes/" in posix
    is_proof = "/proofs/" in posix and "/proofs/exercises/" not in posix
    if not (is_note or is_proof):
        return
    allowed = _ALLOWED_PROOF_TOP_ENVS if is_proof else _ALLOWED_NOTE_TOP_ENVS
    stack=[]
    for line_no, raw in enumerate(text.splitlines(),1):
        line=_strip_comment(raw)
        if _PLAIN_BLOCK_RE.search(line):
            yield Issue("plain_remark_or_example","Use remark* or example* for house prose/example blocks.","error",line_no)
        b=_BEGIN_ENV_RE.match(line)
        if b:
            env=b.group(1)
            if not stack and env not in allowed:
                if is_note and env == "proof":
                    yield Issue("proof_inside_note",
                        "Proof environment appears in a note file; move substantial proof content to the proof vault.",
                        "review", line_no)
                    stack.append(env)
                    continue
                yield Issue("unexpected_top_level_environment",f"Unexpected top-level environment {env}.","error",line_no)
            stack.append(env)
        if not stack and not _top_level_allowed_line(raw):
            yield Issue("top_level_prose","Prose must be inside a formal, remark*, example*, proof, or dependencies block.","error",line_no)
        e=_END_ENV_RE.match(line)
        if e and stack:
            stack.pop()
    if stack:
        yield Issue("unclosed_environment",f"Unclosed environment(s): {', '.join(stack)}.","error",0)

@file_rule("label_quality")
def label_quality(text: str, info: FileInfo, ctx: Context):
    body=_uncommented(text)
    for m in LABEL_RE.finditer(body):
        label=m.group(1)
        if ":" not in label:
            continue
        prefix,slug=label.split(":",1)
        if prefix in _IGNORED_LABEL_PREFIXES:
            continue
        line=_line_at(body, m.start())
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", slug):
            yield Issue("weak_label_slug",f"Label slug should be lowercase kebab-case with readable terms: {label}.","warning",line)
        if any(part in _BAD_LABEL_PARTS for part in slug.split("-")):
            yield Issue("ocr_like_label",f"Label appears to include prose/OCR filler: {label}.","warning",line)

@file_rule("capstone_structure")
def capstone_structure(text: str, info: FileInfo, ctx: Context):
    posix = info.path.replace("\\","/")
    name = posix.rsplit("/",1)[-1]
    if "/proofs/exercises/" not in posix or not name.startswith("capstone-"):
        return
    chapter_name = name[len("capstone-"):-len(".tex")]
    body=_uncommented(text)
    for token, code in [
        ("\\phantomsection","missing_capstone_phantomsection"),
        (f"\\label{{cap:{chapter_name}}}","missing_capstone_label"),
        ("\\begin{tcolorbox}","missing_capstone_box"),
        ("Theorem","missing_capstone_theorem"),
        ("\\begin{remark*}[Dependencies to state]","missing_capstone_dependencies_to_state"),
        ("\\begin{remark*}[Dependencies to prove]","missing_capstone_dependencies_to_prove"),
        ("\\begin{remark*}[Dependency ceiling]","missing_capstone_dependency_ceiling"),
        ("\\begin{dependencies}","missing_capstone_dependencies"),
    ]:
        if token not in body:
            yield Issue(code, f"Capstone missing {token}.","error",0)
    if len(_TCOLORBOX_RE.findall(body)) != 1:
        yield Issue("invalid_capstone_box_count","Capstone must contain exactly one theorem tcolorbox.","error",0)
    if "\\textbf{Problem.}" in body:
        yield Issue("capstone_problem_label","Capstone theorem box must be posed as a theorem, not as a problem prompt.","error",0)

# ============================================================
# Integrated structural identity coverage for chapter/section/subsection
# headings and labels.
#   chapter_identity       -> missing_chapter_heading, starred_chapter_heading,
#                             missing_chapter_label
#   section_router_heading -> starred_section_router_heading,
#                             missing_section_router_heading,
#                             section_router_heading_not_first,
#                             section_heading_after_input,
#                             unstarred_subsection_router_heading
#   note_body_heading      -> unstarred_subsection_body_heading
# Stale-chrome checks from the same monster functions (breadcrumb/toolkit
# tcolorbox, retired roadmap, chapter-structure prose) are intentionally NOT
# ported: the engine supersedes them via the \breadcrumb{}/\toolkitbox macros and
# structural_roadmap_purge. Routing checks remain in audit_volume_layout.
# ============================================================
_STARRED_CHAPTER_RE      = re.compile(r"\\chapter\*(?:\[[^\]]*\])?\{[^{}]+\}")
_SECTION_HEADING_RE      = re.compile(r"\\section(?!\*)(?:\[[^\]]*\])?\{")
_STARRED_SECTION_RE      = re.compile(r"\\section\*(?:\[[^\]]*\])?\{[^{}]+\}")
_UNSTARRED_SUBSECTION_RE = re.compile(r"\\sub(?:sub)?section(?:\[[^\]]*\])?\{[^{}]+\}")
_STARRED_SUBSECTION_RE   = re.compile(r"\\subsection\*(?:\[[^\]]*\])?\{[^{}]+\}")

def _posix(info: "FileInfo") -> str:
    return info.path.replace("\\", "/")

def _notes_topic_and_role(posix: str):
    """For a .../notes/<topic>/<file> path return (topic, role) with role in
    {topic_index, body, ignore}; otherwise (None, None). Mirrors the monster's
    per-topic-index / per-body-file split."""
    parts = posix.split("/")
    if "notes" not in parts:
        return (None, None)
    i = parts.index("notes")
    if len(parts) - i == 2 and parts[i + 1] == "index.tex":
        return ("", "notes_index")
    if len(parts) - i != 3:            # need exactly notes/<topic>/<file>
        return (None, None)
    topic, fname = parts[i + 1], parts[i + 2]
    if fname == "index.tex":
        return (topic, "topic_index")
    if fname.startswith("figure-") or not fname.endswith(".tex"):
        return (topic, "ignore")
    return (topic, "body")

@file_rule("chapter_identity")
def chapter_identity(text: str, info: FileInfo, ctx: Context):
    if info.kind != "chapter_index":
        return
    t = _uncommented(text)
    m = _STARRED_CHAPTER_RE.search(t)
    if m:
        yield Issue("starred_chapter_heading",
            "Chapter routers must use non-starred \\chapter{...}; chapters must appear in the table of contents.",
            "error", _line_at(t, m.start()))
    if "\\chapter" not in t:
        yield Issue("missing_chapter_heading", "Missing chapter heading.", "error", 0)
    if "\\label{ch:" not in t and "\\label{chap:" not in t:
        yield Issue("missing_chapter_label", "Missing chapter label.", "error", 0)

@file_rule("section_router_heading")
def section_router_heading(text: str, info: FileInfo, ctx: Context):
    topic, role = _notes_topic_and_role(_posix(info))
    if role != "topic_index":
        return
    t = _uncommented(text)
    first_input = t.find("\\input")
    section = _SECTION_HEADING_RE.search(t)
    starred = _STARRED_SECTION_RE.search(t)
    if starred:
        yield Issue("starred_section_router_heading",
            "Topic routers must use non-starred \\section{...} so sections appear in the table of contents.",
            "error", _line_at(t, starred.start()))
    if not section:
        yield Issue("missing_section_router_heading",
            f"notes/{topic}/index.tex must begin routed content with \\section{{...}}.", "error", 0)
    elif t[: section.start()].strip():
        yield Issue("section_router_heading_not_first",
            "Topic routers must begin with the non-starred \\section{...} heading.",
            "error", _line_at(t, section.start()))
    elif first_input >= 0 and section.start() > first_input:
        yield Issue("section_heading_after_input",
            "Topic router section heading must appear before routed body inputs.",
            "error", _line_at(t, section.start()))

@file_rule("note_body_heading")
def note_body_heading(text: str, info: FileInfo, ctx: Context):
    topic, role = _notes_topic_and_role(_posix(info))
    if role != "body":
        return
    t = _uncommented(text)
    sub = _UNSTARRED_SUBSECTION_RE.search(t)
    if sub:
        yield Issue("unstarred_subsection_body_heading",
            "Topic body files must use starred subsection headings so the table of contents remains a chapter-section spine.",
            "error", _line_at(t, sub.start()))

# ============================================================
# Integrated prose, reference-voice, and LaTeX integrity coverage.
#   reference_voice          -> non_reference_voice            (was validate_voice)
#   latex_integrity          -> mismatched_environment, unbalanced_display_math,
#                               unbalanced_tcolorbox           (was validate_latex_integrity
#                               + validate_box_discipline; unclosed_environment and
#                               unmatched_environment_end are NOT re-emitted -- block_discipline
#                               already owns unclosed_environment)
#   formal_block_decoration  -> the content checks of validate_formal_blocks that the engine
#                               does not already cover: missing_standard_quantified_statement,
#                               dependency_without_hyperref, invalid_dependency_target,
#                               source_crosswalk_without_citation, formal_claim_inside_expository_block,
#                               missing_proof_navigation, decoration_order, unknown_decoration_block,
#                               forbidden_decoration_block, missing_dependent_parent_block.
#               (missing_interpretation/missing_dependencies stay with the existing block rules;
#                missing_formal_label->missing_label, label_prefix_mismatch->wrong_label_prefix,
#                missing_required_box->math_box_wrapper. No duplication.)
# ============================================================
_HYPERREF_RE = re.compile(r"\\hyperref\[([^\]]+)\]")
_DEPENDENCY_PREFIXES = {"def","ax","thm","lem","prop","cor"}
_PROOF_ENVS = {"theorem","lemma","proposition","corollary"}
_DECORATION_ORDER = {
    "proof_link":10,"standard quantified statement":20,
    "predicate reading":30,"negated quantified statement":40,"negation predicate reading":50,
    "failure modes":60,"contrapositive quantified statement":70,
    "contrapositive predicate reading":80,"interpretation":100,"notation":102,"historical note":105,
    "comparison with feferman":105,"exposition":110,"examples":120,"non-examples":130,"dependencies":140,
}
_LEGACY_DECORATION_ORDER = {
    "definition predicate reading": _DECORATION_ORDER["predicate reading"],
    "failure mode decomposition": _DECORATION_ORDER["failure modes"],
}
_DEPENDENT_DECORATION_PARENTS = {
    "negation predicate reading":"negated quantified statement",
    "contrapositive predicate reading":"contrapositive quantified statement",
}
_FORBIDDEN_DECORATION_BY_ENV = {
    "definition":{"contrapositive quantified statement","contrapositive predicate reading"},
    "axiom":{"contrapositive quantified statement","contrapositive predicate reading","examples","non-examples"},
    "theorem":{"examples","non-examples"},"lemma":{"examples","non-examples"},
    "proposition":{"examples","non-examples"},"corollary":{"examples","non-examples"},
}
_DECORATION_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|dependencies)\}(?:\[(?P<title>[^\]]+)\])?", re.IGNORECASE)
def _decoration_key(m):
    env=m.group("env").lower()
    if env=="dependencies": return "dependencies"
    return re.sub(r"\s+"," ",(m.group("title") or "").strip().lower())
def _dependency_bodies(dec):
    return re.findall(r"\\begin\{dependencies\}(.*?)\\end\{dependencies\}", dec, re.DOTALL)

_VOICE_BLOCK_RE = re.compile(
    r"\\begin\{(?P<env>remark\*|example\*|exposition)\}(?:\[(?P<title>[^\]]+)\])?(?P<body>[\s\S]*?)\\end\{(?P=env)\}",
    re.IGNORECASE)
_VOICE_BANNED_PATTERNS = {
    r"\bwe\b":"first-person plural", r"\bus\b":"first-person plural", r"\bour\b":"first-person plural",
    r"\bours\b":"first-person plural", r"\bourselves\b":"first-person plural",
    r"\byou\b":"direct reader address", r"\byour\b":"direct reader address", r"\byours\b":"direct reader address",
    r"\byourself\b":"direct reader address", r"\byourselves\b":"direct reader address",
    r"\bstudents?\b":"classroom voice", r"\breaders?\b":"reader-address voice",
    r"\blearners?\b":"classroom voice", r"\binstructors?\b":"classroom voice",
    r"\bteachers?\b":"classroom voice", r"\bclassrooms?\b":"classroom voice",
    r"\bcourse\b":"course-transcript voice", r"\blecture\b":"course-transcript voice",
    r"\blesson\b":"workbook voice", r"\bworkbook\b":"workbook voice", r"\bworksheet\b":"workbook voice",
    r"\bhomework\b":"workbook voice",
}
def _voice_text(body):
    t=re.sub(r"\\(?:label|hyperref|ref|citep?|url|href)\b(?:\[[^\]]*\])?(?:\{[^{}]*\}){0,2}"," ",body)
    t=re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?"," ",t)
    t=re.sub(r"[{}$^_\\]"," ",t)
    return re.sub(r"\s+"," ",t)

@file_rule("reference_voice")
def reference_voice(text: str, info: FileInfo, ctx: Context):
    name=_posix(info).rsplit("/",1)[-1]
    if name.startswith("figure-"): return
    t=_uncommented(text)
    for blk in _VOICE_BLOCK_RE.finditer(t):
        body=_voice_text(blk.group("body"))
        for pattern, reason in _VOICE_BANNED_PATTERNS.items():
            mm=re.search(pattern, body, re.IGNORECASE)
            if mm:
                title=(blk.group("title") or blk.group("env")).strip()
                yield Issue("non_reference_voice",
                    f"{title} block uses {reason}: '{mm.group(0)}'. Use impersonal reference voice.",
                    "warning", _line_at(t, blk.start("body")))

@file_rule("latex_integrity")
def latex_integrity(text: str, info: FileInfo, ctx: Context):
    t=_uncommented(text)
    stack=[]
    for m in re.finditer(r"\\(begin|end)\{([^{}]+)\}", t):
        kind, env = m.group(1), m.group(2)
        if kind=="begin":
            stack.append((env, m.start()))
        elif not stack:
            pass  # unmatched_environment_end: not ported
        else:
            oenv, _ = stack.pop()
            if oenv != env:
                yield Issue("mismatched_environment", f"Opened {oenv} but closed {env}.",
                            "error", _line_at(t, m.start()))
    # unclosed_environment intentionally not emitted (block_discipline owns it)
    display_opens = len(re.findall(r"(?<!\\)\\\[", t))
    display_closes = len(re.findall(r"(?<!\\)\\\]", t))
    if display_opens != display_closes:
        yield Issue("unbalanced_display_math",
                    "Display math delimiters \\[ and \\] are not balanced.", "error", 0)
    if len(re.findall(r"\\begin\{tcolorbox\}", t)) != len(re.findall(r"\\end\{tcolorbox\}", t)):
        yield Issue("unbalanced_tcolorbox", "tcolorbox begin/end count is not balanced.", "error", 0)

@file_rule("formal_block_decoration")
def formal_block_decoration(text: str, info: FileInfo, ctx: Context):
    if "/notes/" not in _posix(info):
        return
    t=_uncommented(text)
    for b in extract_blocks(t):
        labels=LABEL_RE.findall(b.text)
        if not labels:
            continue                       # unlabeled -> missing_label (block rule) owns it; skip decoration checks
        label=labels[0]; dec=b.decoration; win=b.text+"\n"+dec; ln=b.line_start
        if not re.search(r"\\begin\{remark\*\}\[Standard quantified statement\]", dec):
            yield Issue("missing_standard_quantified_statement",
                f"{label} lacks Standard quantified statement block.", "error", ln)
        else:
            binder_count=sum(count_quantified_binders(body) for body in standard_quantified_statement_bodies(dec))
            if binder_count >= 2 and not has_predicate_reading(dec):
                yield Issue("predicate_reading_missing",
                    f"{label} has {binder_count} quantified binders but lacks a Predicate reading block.",
                    "error", ln)
        for body in _dependency_bodies(dec):
            for item in re.finditer(r"\\item(.*)", body):
                refs=_HYPERREF_RE.findall(item.group(1))
                if not refs:
                    yield Issue("dependency_without_hyperref",
                        f"{label} dependency item lacks hyperref.", "error", ln)
                for target in refs:
                    if target.split(":",1)[0] not in _DEPENDENCY_PREFIXES:
                        yield Issue("invalid_dependency_target",
                            f"{label} dependency targets non-statement label {target}.", "error", ln)
        if re.search(r"\\begin\{remark\*\}\[(Historical note|Comparison with Feferman)\]", dec) \
           and not re.search(r"\\cite[t|p]?\{", dec):
            yield Issue("source_crosswalk_without_citation",
                f"{label} has a source/provenance block without a citation.", "error", ln)
        for ex in re.finditer(r"\\begin\{remark\*\}\[(Examples|Non-Examples|Exposition)\]([\s\S]*?)\\end\{remark\*\}", dec):
            body=ex.group(2)
            if LABEL_RE.search(body) or re.search(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}", body):
                yield Issue("formal_claim_inside_expository_block",
                    f"{ex.group(1)} block must not introduce labels or formal theorem-like environments.",
                    "error", ln + _line_at(dec, ex.start()) - 1)
        if b.environment in _PROOF_ENVS and ":" in label:
            proof_target=f"prf:{label.split(':',1)[1]}"
            if proof_target not in _HYPERREF_RE.findall(win):
                yield Issue("missing_proof_navigation",
                    f"{label} lacks navigation to {proof_target}.", "error", ln)
        order_checks=[("proof_link",r"\\hyperref\[prf:"),
                      ("standard_quantified_statement",r"\[Standard quantified statement\]"),
                      ("interpretation",r"\[Interpretation\]"),
                      ("dependencies",r"\\begin\{dependencies\}")]
        positions=[(nm, re.search(pat,win).start()) for nm,pat in order_checks if re.search(pat,win)]
        for (lname,lpos),(rname,rpos) in zip(positions, positions[1:]):
            if rpos < lpos:
                yield Issue("decoration_order", f"{rname} appears before {lname} for {label}.", "error", ln)
        seen=[]
        for m in _DECORATION_BLOCK_RE.finditer(dec):
            key=_decoration_key(m)
            rank=_DECORATION_ORDER.get(key)
            if rank is None and key in _LEGACY_DECORATION_ORDER:
                rank=_LEGACY_DECORATION_ORDER[key]
                yield Issue(f"legacy_{key.replace(' ', '_')}",
                    f"{label} uses legacy decoration block '{key}'; migrate to the canonical block title.",
                    "error", ln + _line_at(dec, m.start()) - 1)
            if rank is None:
                yield Issue("unknown_decoration_block",
                    f"{label} has nonstandard decoration block '{key}'.",
                    "error", ln + _line_at(dec, m.start()) - 1)
                continue
            if key in _FORBIDDEN_DECORATION_BY_ENV.get(b.environment, set()):
                yield Issue("forbidden_decoration_block",
                    f"{b.environment} must not use decoration block '{key}' by artifact-matrix rules.",
                    "error", ln + _line_at(dec, m.start()) - 1)
            if key == "failure modes":
                yield from _check_failure_modes_block(dec, m, label, ln)
            seen.append((key, rank, m.start()))
        seen_keys={k for k,_,_ in seen}
        for child,parent in _DEPENDENT_DECORATION_PARENTS.items():
            if child in seen_keys and parent not in seen_keys:
                yield Issue("missing_dependent_parent_block",
                    f"{child} requires parent block {parent} for {label}.", "error", ln)
        for (lk,lr,_),(rk,rr,rp) in zip(seen, seen[1:]):
            if rr < lr:
                yield Issue("decoration_order",
                    f"{rk} appears before {lk} for {label}; use the canonical decoration order.",
                    "error", ln + _line_at(dec, rp) - 1)

def _check_failure_modes_block(dec, match, label, line):
    body_match=re.search(r"\\begin\{remark\*\}\[Failure modes\](?P<body>[\s\S]*?)\\end\{remark\*\}", dec[match.start():], re.IGNORECASE)
    if not body_match:
        return
    body=body_match.group("body")
    block_line=line + _line_at(dec, match.start()) - 1
    if not re.search(r"\\begin\{description\}", body):
        yield Issue("failure_modes_missing_description",
            f"{label} Failure modes block must use a description list.", "error", block_line)
        return
    items=list(re.finditer(r"\\item\[(?P<title>[^\]]+)\](?P<body>[\s\S]*?)(?=\\item\[|\\end\{description\})", body))
    if not items or items[0].group("title").strip().lower().rstrip(".") != "exposition":
        yield Issue("failure_modes_missing_exposition_item",
            f"{label} Failure modes block must start with \\item[Exposition.].", "error", block_line)
    for item in items:
        if item.group("title").strip().lower().rstrip(".") == "exposition":
            continue
        displays=re.findall(r"\\\[[\s\S]*?\\\]", item.group("body"))
        item_line=block_line + _line_at(body, item.start()) - 1
        if not displays:
            yield Issue("failure_mode_missing_quantified_display",
                f"{label} failure mode '{item.group('title').strip()}' lacks a quantified display.",
                "error", item_line)
        if has_predicate_reading(dec) and len(displays) < 2:
            yield Issue("failure_mode_missing_predicate_display",
                f"{label} failure mode '{item.group('title').strip()}' lacks a predicate-reading display.",
                "error", item_line)
