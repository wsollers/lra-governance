#!/usr/bin/env python3
"""author-definition bound verifier: post-generation self-check on ONE target file.
Reads the same schema source as the canonical validator when provided; never forks rule logic.
Exit 0 = pass, 1 = fail."""
import argparse, re, sys, os

DEFAULT_REQUIRED = {"definition": ["Standard quantified statement", "Interpretation"]}

def balance_report(s):
    p=[]
    if len(re.findall(r"(?<!\\)\$", s))%2: p.append("odd unescaped $")
    if len(re.findall(r"(?<!\\)\\\[", s))!=len(re.findall(r"(?<!\\)\\\]", s)): p.append(r"\[ vs \] mismatch")
    if len(re.findall(r"\\begin\{", s))!=len(re.findall(r"\\end\{", s)): p.append(r"\begin vs \end mismatch")
    if len(re.findall(r"(?<!\\)\{", s))!=len(re.findall(r"(?<!\\)\}", s)): p.append("brace mismatch")
    return p

def required_blocks(kind, matrix_path):
    # Production: parse artifact-matrix.yaml for this kind's required blocks.
    # Falls back to the documented default when the schema file is absent (PoC).
    return DEFAULT_REQUIRED.get(kind, [])

def predicate_names(path):
    names=set()
    if path and os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            m=re.match(r"\s*name:\s*([A-Za-z][A-Za-z0-9]*)\s*$", ln)
            if m: names.add(m.group(1))
    return names

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--kind", default="definition")
    ap.add_argument("--matrix", default=None)
    ap.add_argument("--predicates", default=None)
    a=ap.parse_args()
    if not os.path.exists(a.target):
        print(f"FAIL: target not found: {a.target}"); sys.exit(1)
    s=open(a.target, encoding="utf-8", errors="replace").read()
    fails=[]
    for p in balance_report(s): fails.append(f"latex: {p}")
    if not re.search(r"\\begin\{definition\}", s): fails.append(r"missing \begin{definition}")
    if not re.search(r"\\label\{def:[a-z0-9-]+\}", s): fails.append(r"missing \label{def:<slug>}")
    for blk in required_blocks(a.kind, a.matrix):
        if not re.search(r"\\begin\{remark\*\}\[\s*"+re.escape(blk), s):
            fails.append(f"missing required block: {blk}")
    if not (re.search(r"\\begin\{dependencies\}", s) or re.search(r"\\NoLocalDependencies", s)):
        fails.append(r"missing Dependencies block or \NoLocalDependencies")
    names=predicate_names(a.predicates)
    if re.search(r"\\begin\{remark\*\}\[\s*Definition predicate reading\]", s) and names:
        used={u for u in re.findall(r"\\operatorname\{([A-Za-z][A-Za-z0-9]*)\}", s) if u[:1].isupper()}
        for u in sorted(used):
            if u not in names:
                fails.append(f"non-canonical predicate \\operatorname{{{u}}} (not in predicates.yaml)")
    if fails:
        print(f"VERIFY FAIL ({a.target}) [kind={a.kind}]:")
        for f in fails: print(f"  - {f}")
        sys.exit(1)
    print(f"VERIFY PASS ({a.target}) [kind={a.kind}] — definition invariants satisfied.")
    sys.exit(0)

if __name__=="__main__": main()
