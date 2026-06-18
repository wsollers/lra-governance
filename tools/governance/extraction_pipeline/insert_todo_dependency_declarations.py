#!/usr/bin/env python3
"""Insert TODO dependency declarations for formal blocks missing declarations.

This is a migration aid. It does not infer mathematical dependencies. It makes
missing dependency debt explicit in source so later audit passes can replace
TODO items with real graph edges.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


FORMAL_ENVS = ("definition", "axiom", "theorem", "lemma", "proposition", "corollary")
WRAPPER_ENVS = (
    "definitionbox",
    "definitionalbox",
    "axiombox",
    "theorembox",
    "lemmabox",
    "propositionbox",
    "corollarybox",
)


def load_missing(validation_path: Path) -> list[dict[str, Any]]:
    data = json.loads(validation_path.read_text(encoding="utf-8"))
    return [
        issue
        for issue in data.get("issues", [])
        if issue.get("code") == "missing_dependency_declaration"
    ]


def end_of_formal_block(text: str, label: str) -> int | None:
    label_match = re.search(rf"\\label\{{{re.escape(label)}\}}", text)
    if not label_match:
        return None
    before = text[: label_match.start()]
    begin_matches = list(
        re.finditer(
            r"\\begin\{(?P<env>definition|axiom|theorem|lemma|proposition|corollary)\}",
            before,
            re.IGNORECASE,
        )
    )
    if not begin_matches:
        return None
    env = begin_matches[-1].group("env")
    end_match = re.search(rf"\\end\{{{re.escape(env)}\}}", text[label_match.end() :], re.IGNORECASE)
    if not end_match:
        return None
    end = label_match.end() + end_match.end()

    after = text[end:]
    wrapper_match = re.match(
        rf"(?P<space>\s*)\\end\{{(?P<wrapper>{'|'.join(WRAPPER_ENVS)})\}}",
        after,
        re.IGNORECASE,
    )
    if wrapper_match:
        end += wrapper_match.end()
    return end


def insertion_text(label: str) -> str:
    return (
        "\n\n"
        "\\begin{dependencies}\n"
        "\\begin{itemize}\n"
        f"  \\item TODO: determine dependencies for \\texttt{{{label}}}.\n"
        "\\end{itemize}\n"
        "\\end{dependencies}"
    )


def apply_insertions(repo_path: Path, issues: list[dict[str, Any]], write: bool) -> tuple[int, list[str]]:
    by_file: dict[Path, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        by_file[repo_path / str(issue["file"]).replace("/", "\\")].append(issue)

    changed = 0
    problems: list[str] = []
    for path, file_issues in sorted(by_file.items(), key=lambda item: str(item[0])):
        text = path.read_text(encoding="utf-8")
        insertions: list[tuple[int, str]] = []
        for issue in file_issues:
            label = str(issue["label"])
            end = end_of_formal_block(text, label)
            if end is None:
                problems.append(f"{path}: could not locate formal block for {label}")
                continue
            window = text[end : re.search(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}|\\(?:chapter|section|subsection|subsubsection)\*?\{", text[end:], re.IGNORECASE).start() + end if re.search(r"\\begin\{(?:definition|axiom|theorem|lemma|proposition|corollary)\}|\\(?:chapter|section|subsection|subsubsection)\*?\{", text[end:], re.IGNORECASE) else len(text)]
            if re.search(r"\\begin\{dependencies\}|\\NoLocalDependencies\b|\\DefinitionalRoot\b", window, re.IGNORECASE):
                continue
            insertions.append((end, insertion_text(label)))
        if not insertions:
            continue
        changed += len(insertions)
        if write:
            new_text = text
            for offset, payload in sorted(insertions, reverse=True):
                new_text = new_text[:offset] + payload + new_text[offset:]
            path.write_text(new_text, encoding="utf-8", newline="")
    return changed, problems


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = load_missing(args.validation)
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in missing:
        by_repo[str(issue["repo"])].append(issue)

    total = 0
    all_problems: list[str] = []
    for repo, issues in sorted(by_repo.items()):
        repo_path = args.repos_root / repo
        changed, problems = apply_insertions(repo_path, issues, args.write)
        total += changed
        all_problems.extend(problems)
        print(f"{repo}: {'would insert' if not args.write else 'inserted'} {changed} TODO dependency declaration(s)")
    for problem in all_problems:
        print(f"warning: {problem}")
    return 1 if all_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

