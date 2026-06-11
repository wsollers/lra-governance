#!/usr/bin/env python3
"""author-definition bound verifier: focused post-generation check on one target file.
Exit 0 = pass, 1 = fail."""
import argparse, re, sys, os

DEFAULT_REQUIRED = {"definition": ["Standard quantified statement", "Interpretation"]}
KIND_KEYS = {"definition": "def"}
BLOCK_TITLES = {
    "standard_quantified_stmt": "Standard quantified statement",
    "interpretation": "Interpretation",
}

def balance_report(s):
    p=[]
    if len(re.findall(r"(?<!\\)\$", s))%2: p.append("odd unescaped $")
    if len(re.findall(r"(?<!\\)\\\[", s))!=len(re.findall(r"(?<!\\)\\\]", s)): p.append(r"\[ vs \] mismatch")
    if len(re.findall(r"\\begin\{", s))!=len(re.findall(r"\\end\{", s)): p.append(r"\begin vs \end mismatch")
    if len(re.findall(r"(?<!\\)\{", s))!=len(re.findall(r"(?<!\\)\}", s)): p.append("brace mismatch")
    return p

def required_blocks(kind, matrix_path):
    if matrix_path and os.path.exists(matrix_path):
        try:
            import yaml
            data = yaml.safe_load(open(matrix_path, encoding="utf-8")) or {}
            matrix = data.get("matrix", {})
            key = KIND_KEYS.get(kind, kind)
            required = []
            for block_id, by_kind in matrix.items():
                if by_kind.get(key) == "R" and block_id in BLOCK_TITLES:
                    required.append(BLOCK_TITLES[block_id])
            if required:
                return required
        except Exception as exc:
            print(f"WARN: could not read matrix {matrix_path}: {exc}", file=sys.stderr)
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
    print(f"VERIFY PASS ({a.target}) [kind={a.kind}] - definition invariants satisfied.")
    sys.exit(0)

if __name__=="__main__": main()
