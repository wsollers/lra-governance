#!/usr/bin/env python3
"""Create compile-safe proof STUBS for theorem-like statements that lack one.

Chains after identify_missing_proofs.py (imports its find_missing + helpers, so
the two agree by construction). For each obligation with status 'missing' it:
  - transplants the theorem title + statement + dependency block from the notes,
  - emits the full 11-layer stub (both proof bodies TODO, blank Proof structure),
    matching tools/governance/audit_proof_layout.py -> compliant_stub,
  - writes proofs/{topic}/prf-{root}.tex,
  - wires it into proofs/{topic}/index.tex (creating that index + wiring it into
    proofs/index.tex when the topic folder is new).
Status 'unindexed' (file already on disk but not routed) only gets the index wired.

Dry-run by default; --apply to write. Line endings follow the source notes file.
Never overwrites an existing proof file.
"""
from __future__ import annotations
import argparse, re
from pathlib import Path
import identify_missing_proofs as idp

STUB_TEMPLATE = r"""\newpage
\phantomsection
\label{prf:%%ROOT%%}
\LRAProofFor{%%THMLABEL%%}

\begin{remark*}[Return]
\hyperref[%%THMLABEL%%]{Return to Theorem (%%TITLE%%).}
\end{remark*}

\begin{theorem*}[%%TITLE%%]
%%STATEMENT%%
\end{theorem*}

\begin{proof}
\textbf{Professional Standard Proof.}~
TODO: professional standard proof for %%ROOT%%.
\end{proof}

\begin{proof}
\textbf{Detailed Learning Proof.}~
TODO: detailed learning proof for %%ROOT%%.
\end{proof}

\begin{remark*}[Proof structure]
\end{remark*}

%%DEPS%%

\clearpage
"""

DEFAULT_DEPS = (r"\begin{dependencies}" "\n"
                r"\begin{itemize}" "\n"
                r"  \item TODO: list mathematical dependencies." "\n"
                r"\end{itemize}" "\n"
                r"\end{dependencies}")

def extract_payload(notes_path: Path, thm_label: str):
    """Return (title, statement_body, deps_block_or_None) for the theorem labelled thm_label."""
    text = notes_path.read_text(encoding="utf-8", errors="ignore")
    matches = list(idp.THEOREM_ENV_RE.finditer(text))
    for k, m in enumerate(matches):
        body = m.group(3)
        lab = idp.LABEL_IN_BODY_RE.search(body)
        if not lab or lab.group(1) != thm_label:
            continue
        title = (m.group(2) or "").strip()
        statement = idp.clean_restatement(body)
        nxt = matches[k + 1].start() if k + 1 < len(matches) else len(text)
        dm = idp.DEPENDENCIES_RE.search(text, m.end(), nxt)
        return title, statement, (dm.group(0) if dm else None)
    return None, None, None

def build_stub(root, thm_label, title, statement, deps):
    title = title or root
    statement = statement or "TODO: restate the theorem."
    deps = deps or DEFAULT_DEPS
    return (STUB_TEMPLATE
            .replace("%%THMLABEL%%", thm_label)
            .replace("%%ROOT%%", root)
            .replace("%%TITLE%%", title)
            .replace("%%STATEMENT%%", statement)
            .replace("%%DEPS%%", deps))

def detect_nl(*texts):
    for t in texts:
        if t and "\r\n" in t:
            return "\r\n"
    return "\n"

def append_input(index_path: Path, target_rel: str, nl: str, apply: bool):
    """Append \\input{target_rel} to index_path if absent. Returns action str or None."""
    if index_path.exists():
        text = open(index_path, encoding="utf-8", newline="").read()
        if target_rel in idp.normalized_input_targets(text):
            return None
        ix_nl = "\r\n" if "\r\n" in text else nl
        new = text + (ix_nl if text and not text.endswith(("\n", "\r")) else "") + f"\\input{{{target_rel}}}" + ix_nl
        if apply:
            open(index_path, "w", encoding="utf-8", newline="").write(new)
        return f"WIRE   {index_path.name}  <- \\input{{{target_rel}}}"
    # create fresh topic index
    banner = (f"% ========================================================={nl}"
              f"% Proofs: {index_path.parent.name}{nl}"
              f"% ========================================================={nl}{nl}")
    new = banner + f"\\input{{{target_rel}}}" + nl
    if apply:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        open(index_path, "w", encoding="utf-8", newline="").write(new)
    return f"CREATE {index_path.relative_to(index_path.parents[2])}  (+ \\input{{{target_rel}}})"

def main():
    ap = argparse.ArgumentParser(description="Create proof stubs for missing obligations.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--topic", help="Restrict to one notes/{topic}.")
    ap.add_argument("--require-proof-link", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    obs = idp.find_missing(root, a.require_proof_link, a.topic)
    todo = [o for o in obs if o.status in ("missing", "unindexed")]
    skips = [o for o in obs if o.status in ("unlabeled", "no-topic")]
    for o in skips:
        print(f"  SKIP ({o.status}): {o.thm_label or '(unlabeled)'} \"{o.title}\" in {o.notes_file}")
    made = wired = 0
    for o in todo:
        chap = Path(o.chapter_root_abs)
        notes_path = chap / o.notes_file
        proof_path = chap / o.expected_proof
        topic_index = chap / "proofs" / o.topic / "index.tex"
        proofs_index = chap / "proofs" / "index.tex"
        target_file  = f"{o.chapter}/proofs/{o.topic}/prf-{o.root}"
        target_index = f"{o.chapter}/proofs/{o.topic}/index"
        notes_text = (open(notes_path, encoding="utf-8", newline="").read() if notes_path.exists() else "")
        nl = detect_nl(notes_text)
        print(f"\n[{o.status}] {o.thm_label}  ->  {o.expected_proof}")
        if o.status == "missing":
            title, statement, deps = extract_payload(notes_path, o.thm_label)
            stub = build_stub(o.root, o.thm_label, title, statement, deps).replace("\n", nl)
            print(f"  {'WRITE' if a.apply else 'WOULD WRITE'} {o.expected_proof}"
                  f"  (deps: {'transplanted' if deps else 'TODO placeholder'})")
            if a.apply:
                if proof_path.exists():
                    print("  REFUSE: file exists; not overwriting"); continue
                proof_path.parent.mkdir(parents=True, exist_ok=True)
                open(proof_path, "w", encoding="utf-8", newline="").write(stub)
            made += 1
        topic_new = not topic_index.exists()
        act1 = append_input(topic_index, target_file, nl, a.apply)
        if act1:
            print(f"  {act1}"); wired += 1
        if topic_new:
            act2 = append_input(proofs_index, target_index, nl, a.apply)
            if act2:
                print(f"  {act2}")
    print(f"\n{'APPLIED' if a.apply else 'DRY-RUN'}: stubs={made}, index wirings touched, "
          f"obligations handled={len(todo)}, skipped={len(skips)}")

if __name__ == "__main__":
    raise SystemExit(main())
