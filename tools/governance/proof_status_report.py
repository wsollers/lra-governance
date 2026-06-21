from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from core.file_inventory import files_to_validate


ROOT = Path(__file__).resolve().parents[2]
PROOF_FOR_RE = re.compile(r"\\LRAProofFor\{(?P<label>(?:thm|lem|prop|cor):[A-Za-z0-9-]+)\}")
PROOF_RE = re.compile(r"\\begin\{proof\}\[(?P<title>[^\]]+)\](?P<body>.*?)\\end\{proof\}", re.DOTALL)
TODO_RE = re.compile(
    r"\bTODO\b|MIGRATION TODO|professional standard proof for|detailed learning proof for",
    re.IGNORECASE,
)


def volume_name(repo_root: Path) -> str:
    volume_roots = [child.name for child in sorted(repo_root.iterdir()) if child.is_dir() and child.name.startswith("volume-")]
    if len(volume_roots) != 1:
        raise ValueError(f"Expected exactly one volume-* directory in {repo_root}, found {len(volume_roots)}.")
    return volume_roots[0]


def chapter_from_path(path: Path, volume_root: Path) -> str:
    parts = path.relative_to(volume_root).parts
    return parts[0] if parts else ""


def active_proof_files(repo_root: Path) -> list[Path]:
    volume_root = repo_root / volume_name(repo_root)
    return [
        path
        for path in files_to_validate(volume_root, only_reachable=True)
        if path.name.startswith("prf-") and "proofs" in path.relative_to(volume_root).parts
    ]


def proof_bodies(text: str) -> dict[str, str]:
    bodies: dict[str, str] = {}
    for match in PROOF_RE.finditer(text):
        title = match.group("title")
        body = match.group("body")
        if "Professional Standard Proof" in title:
            bodies["professional"] = body
        elif "Detailed Learning Proof" in title:
            bodies["detailed"] = body
    return bodies


def classify_proof(path: Path, repo_root: Path) -> dict[str, str]:
    volume_root = repo_root / volume_name(repo_root)
    text = path.read_text(encoding="utf-8", errors="replace")
    proof_for = PROOF_FOR_RE.search(text)
    bodies = proof_bodies(text)
    missing_layers = [name for name in ("professional", "detailed") if name not in bodies]
    todo_layers = [name for name, body in bodies.items() if TODO_RE.search(body)]
    status = "done"
    if not proof_for or missing_layers:
        status = "invalid"
    elif todo_layers:
        status = "todo"

    return {
        "status": status,
        "label": proof_for.group("label") if proof_for else "",
        "chapter": chapter_from_path(path, volume_root),
        "proof_file": path.relative_to(repo_root).as_posix(),
        "todo_layers": "; ".join(todo_layers),
        "missing_layers": "; ".join([*([] if proof_for else ["proof_for"]), *missing_layers]),
    }


def collect_rows(repo_root: Path) -> list[dict[str, str]]:
    return [classify_proof(path, repo_root) for path in active_proof_files(repo_root)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["status", "label", "chapter", "proof_file", "todo_layers", "missing_layers"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], volume: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    done = [row for row in rows if row["status"] == "done"]
    todo = [row for row in rows if row["status"] == "todo"]
    invalid = [row for row in rows if row["status"] == "invalid"]
    title = volume.replace("-", " ").title()
    lines = [
        f"# {title} Proof Status",
        "",
        f"- Total active proof files: {len(rows)}",
        f"- Done: {len(done)}",
        f"- TODO: {len(todo)}",
        f"- Invalid proof-layer shape: {len(invalid)}",
        "",
        "| Status | Label | Chapter | Proof file | TODO layers | Missing layers |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['status']} | `{row['label']}` | `{row['chapter']}` | "
            f"`{row['proof_file']}` | {row['todo_layers']} | {row['missing_layers']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report active proof files done versus TODO.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    volume = volume_name(repo_root)
    csv_path = args.csv or repo_root / "build" / "reports" / f"{volume}-proof-status.csv"
    markdown_path = args.markdown or repo_root / "build" / "reports" / f"{volume}-proof-status.md"

    rows = collect_rows(repo_root)
    write_csv(csv_path, rows)
    write_markdown(markdown_path, rows, volume)

    counts = {status: sum(1 for row in rows if row["status"] == status) for status in ("done", "todo", "invalid")}
    print(f"total active proof files: {len(rows)}")
    print(f"done: {counts['done']}")
    print(f"todo: {counts['todo']}")
    print(f"invalid: {counts['invalid']}")
    print(f"csv: {csv_path}")
    print(f"markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
