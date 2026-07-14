#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from core.file_inventory import files_to_validate
from core.formal_blocks import FormalBlock, formal_blocks_for_file
from core.tex import line_at, read_stripped_text
from core.validator_runner import run_validator
from core.volume import resolve_volume
from validators import predicate_reading_constructions, predicate_reading_signatures


CALL_RE = re.compile(r"\\(?:operatorname|mathsf)\{(?P<name>[^}]+)\}")
DEPENDENCIES_RE = re.compile(r"\\begin\{dependencies\}[\s\S]*?\\end\{dependencies\}|\\NoLocalDependencies")
PREDICATE_READING_RE = re.compile(
    r"\\begin\{remark\*\}\[(?:Predicate reading|Negation predicate reading|Contrapositive predicate reading)\][\s\S]*?\\end\{remark\*\}",
    re.IGNORECASE,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate per-item predicate/dependency migration context packets.")
    parser.add_argument("--volume", required=True, help="Volume repo root or volume-* source directory.")
    parser.add_argument("--chapter", required=True, help="Chapter directory name, e.g. bounding.")
    parser.add_argument("--output-root", default="migration-reports/predicate-contexts", help="Output root for ignored report files.")
    args = parser.parse_args(argv)

    volume = resolve_volume(args.volume)
    chapter = _resolve_chapter(volume.root, args.chapter)
    output_root = Path(args.output_root).resolve() / volume.root.name / chapter.name
    packets_dir = output_root / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)

    files = files_to_validate([chapter], only_reachable=False)
    findings = []
    for validator in (predicate_reading_signatures, predicate_reading_constructions):
        findings.extend(run_validator(validator, volume.root, files))
    blocks = _formal_blocks(files, volume.root)
    signatures = _signatures()
    findings_by_block = _findings_by_block(blocks, findings)

    roster = []
    for index, block in enumerate(blocks, start=1):
        packet_path = packets_dir / f"{index:04d}.{_safe_label(block)}.md"
        block_findings = findings_by_block.get(block_key(block), [])
        packet_path.write_text(_packet_text(volume.root, chapter, index, block, block_findings, blocks, signatures), encoding="utf-8")
        roster.append(
            {
                "index": index,
                "label": block.label,
                "env": block.env,
                "title": block.title,
                "path": rel(block.path, volume.root),
                "line": block.line,
                "finding_count": len(block_findings),
                "packet": rel(packet_path, output_root),
            }
        )

    summary = {
        "volume": volume.root.name,
        "chapter": rel(chapter, volume.root),
        "formal_item_count": len(blocks),
        "finding_count": len(findings),
        "findings_by_code": dict(Counter(item.code for item in findings)),
        "findings_by_file": dict(Counter(item.path for item in findings)),
        "roster": roster,
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_root / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")
    print(f"wrote {len(blocks)} packet(s) and {len(findings)} validator finding(s) to {output_root}")
    return 0


def _resolve_chapter(volume_root: Path, chapter_name: str) -> Path:
    matches = sorted(path for path in volume_root.rglob(chapter_name) if path.is_dir() and (path / "notes").is_dir())
    if not matches:
        raise SystemExit(f"chapter not found: {chapter_name}")
    if len(matches) > 1:
        joined = ", ".join(rel(path, volume_root) for path in matches)
        raise SystemExit(f"chapter is ambiguous: {joined}")
    return matches[0].resolve()


def _formal_blocks(files: list[Path], volume_root: Path) -> list[FormalBlock]:
    blocks: list[FormalBlock] = []
    for path in files:
        if path.suffix != ".tex":
            continue
        path_text = path.as_posix()
        if "/notes/" not in path_text.replace("\\", "/"):
            continue
        blocks.extend(formal_blocks_for_file(path))
    return sorted(blocks, key=lambda block: (rel(block.path, volume_root), block.line, block.label))


def _findings_by_block(blocks: list[FormalBlock], findings) -> dict[tuple[str, int], list]:
    by_file = defaultdict(list)
    for block in blocks:
        by_file[block.path.resolve()].append(block)
    result = defaultdict(list)
    for item in findings:
        item_path = Path(item.path)
        candidates = []
        for path, file_blocks in by_file.items():
            if path.as_posix().endswith(item_path.as_posix()):
                candidates = file_blocks
                break
        selected = None
        for block in candidates:
            if block.line <= item.line:
                selected = block
            else:
                break
        if selected is not None:
            result[block_key(selected)].append(item)
    return result


def _packet_text(volume_root: Path, chapter: Path, index: int, block: FormalBlock, findings, blocks: list[FormalBlock], signatures: dict[str, str]) -> str:
    operators = sorted(set(CALL_RE.findall(block.body + "\n" + block.decoration)))
    deps = "\n\n".join(match.group(0).strip() for match in DEPENDENCIES_RE.finditer(block.decoration)) or "(none found)"
    predicate_blocks = "\n\n".join(match.group(0).strip() for match in PREDICATE_READING_RE.finditer(block.decoration)) or "(none found)"
    nearby = _nearby_definitions(block, blocks, volume_root)
    finding_text = "\n".join(f"- `{item.code}` at line {item.line}: {item.message}" for item in findings) or "- No predicate signature/construction findings for this item."
    signature_text = "\n".join(f"- `{name}`: {signatures[name]}" for name in operators if name in signatures) or "- No registered predicate/structure calls detected."
    return "\n".join(
        [
            f"# Predicate Migration Packet {index:04d}: {block.label or '(unlabeled)'}",
            "",
            "## Target",
            "",
            f"- Chapter: `{rel(chapter, volume_root)}`",
            f"- Source: `{rel(block.path, volume_root)}:{block.line}`",
            f"- Kind: `{block.env}`",
            f"- Title: `{block.title}`",
            f"- Label: `{block.label}`",
            "",
            "## Task",
            "",
            "Inspect this formal item even if no validator finding appears. Fix predicate-reading signatures, add construction lines, and update parse/type, structure, and proof-use dependencies. If canonical vocabulary or dependency targets are missing, record the gap instead of inventing local names.",
            "",
            "## Validator Findings",
            "",
            finding_text,
            "",
            "## Registered Signatures In Scope",
            "",
            signature_text,
            "",
            "## Formal Body",
            "",
            "```tex",
            block.body.strip(),
            "```",
            "",
            "## Predicate Reading Blocks",
            "",
            "```tex",
            predicate_blocks,
            "```",
            "",
            "## Current Dependencies",
            "",
            "```tex",
            deps,
            "```",
            "",
            "## Nearby Definitions",
            "",
            nearby,
            "",
            "## Validation Commands",
            "",
            "```powershell",
            "python ..\\lra-governance\\scripts\\build_volume.py --root . --validate-only",
            "```",
            "",
        ]
    )


def _nearby_definitions(block: FormalBlock, blocks: list[FormalBlock], volume_root: Path) -> str:
    previous = [candidate for candidate in blocks if candidate.path == block.path and candidate.line < block.line and candidate.env == "definition"]
    items = previous[-5:]
    if not items:
        return "- No earlier definitions in this source file."
    return "\n".join(f"- `{item.label}` ({item.title}) at `{rel(item.path, volume_root)}:{item.line}`" for item in items)


def _signatures() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    signatures = {}
    for filename, key, kind in (("predicates.yaml", "predicates", "predicate"), ("structures.yaml", "structures", "structure")):
        data = yaml.safe_load((root / filename).read_text(encoding="utf-8")) or {}
        for item in data.get(key, []) or []:
            name = item.get("name")
            args = item.get("arguments") or []
            if not name:
                continue
            rendered = ", ".join(f"{arg.get('name')}:{arg.get('role')}" for arg in args)
            signatures[str(name)] = f"{kind}({rendered})"
    return signatures


def _summary_markdown(summary: dict) -> str:
    lines = [
        f"# Predicate Migration Summary: {summary['volume']} / {summary['chapter']}",
        "",
        f"- Formal items: `{summary['formal_item_count']}`",
        f"- Validator findings: `{summary['finding_count']}`",
        "",
        "## Findings By Code",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in summary["findings_by_code"].items())
    lines.extend(["", "## Roster", ""])
    for item in summary["roster"]:
        lines.append(f"- {item['index']:04d} `{item['label']}` `{item['env']}` findings={item['finding_count']} packet=`{item['packet']}`")
    lines.append("")
    return "\n".join(lines)


def block_key(block: FormalBlock) -> tuple[str, int]:
    return (block.path.resolve().as_posix(), block.line)


def _safe_label(block: FormalBlock) -> str:
    value = block.label or f"{block.env}-{block.line}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value)


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
