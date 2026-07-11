from __future__ import annotations

import re
from pathlib import Path

from core.finding import Finding, finding
from core.tex import read_text
from core.file_inventory import validator_files


FORMAL_ENVS = {"definition", "axiom", "theorem", "lemma", "proposition", "corollary"}
FORMAL_BOX_ENVS = {"definitionbox", "definitionalbox", "axiombox", "theorembox", "lemmabox", "propositionbox", "corollarybox"}
STARRED_RESTATEMENT_ENVS = {"theorem*", "lemma*", "proposition*", "corollary*"}
ALLOWED_NOTE_TOP_ENVS = FORMAL_ENVS | FORMAL_BOX_ENVS | {
    "remark*",
    "example*",
    "exposition",
    "dependencies",
    "tcolorbox",
    "toolkitbox",
    "modelbox",
    "signaturebox",
    "topicbox",
    "figure",
    "longtable",
    "tabular",
    "tabularx",
    "itemize",
    "enumerate",
    "description",
    "quote",
    "center",
    "tikzpicture",
    "lra-not-visible",
}
ALLOWED_PROOF_TOP_ENVS = {"remark*", "proof", "dependencies"} | STARRED_RESTATEMENT_ENVS
FORBIDDEN_PROOF_STRUCTURE_ENVS = {"topicbox", "exposition"}

BEGIN_ENV_RE = re.compile(r"\\begin\{([^{}]+)\}(?:\[[^\]]*\])?")
END_ENV_RE = re.compile(r"\\end\{([^{}]+)\}")
PLAIN_BLOCK_RE = re.compile(r"\\begin\{(remark|example)\}(?!\*)")
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
    "\\ProofVaultURL",
    "\\LRAExcludeFromPrintEditionBegin",
    "\\LRAExcludeFromPrintEditionEnd",
    "\\NoLocalDependencies",
    "\\DefinitionalRoot",
    "\\medskip",
    "\\smallskip",
    "\\bigskip",
    "\\vspace",
)


def validate(volume_root: Path, files) -> list[Finding]:
    findings: list[Finding] = []
    for tex in validator_files(volume_root, files):
        _validate_file(volume_root, tex, findings)
    return findings


def _validate_file(volume_root: Path, path: Path, findings: list[Finding]) -> None:
    rel = path.resolve().relative_to(volume_root.resolve()).as_posix()
    if Path(rel).name.startswith("figure-"):
        return
    is_note = "/notes/" in f"/{rel}"
    is_proof = "/proofs/" in f"/{rel}" and "/proofs/exercises/" not in f"/{rel}"
    if not (is_note or is_proof):
        return

    allowed = ALLOWED_PROOF_TOP_ENVS if is_proof else ALLOWED_NOTE_TOP_ENVS
    stack: list[str] = []
    for line_no, raw in enumerate(read_text(path).splitlines(), 1):
        line = _strip_comment(raw)
        stripped = line.lstrip()
        if PLAIN_BLOCK_RE.search(stripped):
            findings.append(
                finding(
                    "plain_remark_or_example",
                    "Use remark* or example* for house prose/example blocks.",
                    path,
                    volume_root,
                    line_no,
                )
            )
        begin = BEGIN_ENV_RE.match(stripped)
        if begin:
            env = begin.group(1)
            if not stack and env not in allowed:
                if is_proof and env in FORBIDDEN_PROOF_STRUCTURE_ENVS:
                    findings.append(
                        finding(
                            "topicbox_or_exposition_in_proof",
                            "Proof files must not use topicbox or exposition; keep proof files to restatement, proof layers, remarks, and dependencies.",
                            path,
                            volume_root,
                            line_no,
                        )
                    )
                elif is_note and env == "proof":
                    findings.append(
                        finding(
                            "proof_inside_note",
                            "Proof environment appears in a note file; move substantial proof content to the proof vault.",
                            path,
                            volume_root,
                            line_no,
                            "review",
                        )
                    )
                else:
                    findings.append(
                        finding(
                            "unexpected_top_level_environment",
                            f"Unexpected top-level environment {env}.",
                            path,
                            volume_root,
                            line_no,
                        )
                    )
            stack.append(env)
        if not stack and not _top_level_allowed_line(raw):
            findings.append(
                finding(
                    "top_level_prose",
                    "Prose must be inside a formal, remark*, example*, proof, or dependencies block.",
                    path,
                    volume_root,
                    line_no,
                )
            )
        end = END_ENV_RE.match(stripped)
        if end and stack:
            stack.pop()


def _strip_comment(line: str) -> str:
    escaped = False
    out = []
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


def _top_level_allowed_line(line: str) -> bool:
    stripped = _strip_comment(line).strip()
    return not stripped or stripped.startswith("%") or stripped.startswith(TOP_LEVEL_COMMANDS)
