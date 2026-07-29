#!/usr/bin/env python3
"""Report Lean <-> TeX cross-reference coverage from an internal object index."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

try:
    from plan_lean_tex_formalizations import (
        GENERIC_TITLES,
        build_plan,
        normalized_title,
        production_lean,
        terminal_declaration_name,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised by package imports
    from tools.governance.plan_lean_tex_formalizations import (
        GENERIC_TITLES,
        build_plan,
        normalized_title,
        production_lean,
        terminal_declaration_name,
    )


def load_structured(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def write_structured(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".yaml", ".yml"}:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    else:
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


SCRATCH_MODULE_RE = re.compile(r"^###\s+`(?P<path>[^`]+\.lean)`")
SCRATCH_MAPPING_RE = re.compile(
    r"^-\s+\*\*(?P<kind>[A-Za-z_][A-Za-z0-9_]*)\s+`(?P<declaration>[^`]+)`\*\*\s+←\s+(?P<labels>.+)$"
)
TEX_LABEL_RE = re.compile(r"`(?P<label>(?:def|axiom|thm|lem|prop|cor):[^`]+)`")
NO_BOOK_LABEL_TEXT = "*(no book label found)*"


def parse_scratch_mapping(path: Path) -> list[dict[str, Any]]:
    """Parse lra-lean's generated TeX-label-to-Lean-name Markdown map."""
    mappings: list[dict[str, Any]] = []
    current_module = ""
    current_path = ""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        module_match = SCRATCH_MODULE_RE.match(line)
        if module_match:
            current_path = module_match.group("path")
            module_path = current_path.removesuffix(".lean").replace("/", ".").replace("\\", ".")
            current_module = f"LRA.VolumeIII.Analysis.{module_path}"
            continue
        mapping_match = SCRATCH_MAPPING_RE.match(line)
        if not mapping_match or not current_module:
            continue
        labels = [match.group("label") for match in TEX_LABEL_RE.finditer(mapping_match.group("labels"))]
        if not labels and NO_BOOK_LABEL_TEXT in mapping_match.group("labels"):
            labels = [""]
        elif not labels:
            continue
        for label in labels:
            mappings.append(
                {
                    "tex_label": label or None,
                    "lean_kind": mapping_match.group("kind"),
                    "lean_module": current_module,
                    "lean_declaration": mapping_match.group("declaration"),
                    "has_tex_label": bool(label),
                    "source": str(path),
                    "source_line": line_number,
                    "scratch_path": current_path,
                }
            )
    return mappings


def lean_identity(record: dict[str, Any]) -> tuple[str, str]:
    module = str(record.get("module") or "")
    declaration = terminal_declaration_name(record)
    return module, declaration


def link_identity(link: dict[str, Any]) -> tuple[str, str]:
    return str(link.get("module") or ""), str(link.get("declaration") or "")


def resolve_mapping_against_index(
    mapping: dict[str, Any],
    lean_by_declaration: dict[str, list[dict[str, Any]]],
    lean_by_normalized_declaration: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    matches = lean_by_declaration.get(str(mapping.get("lean_declaration") or ""), [])
    if not matches:
        matches = lean_by_normalized_declaration.get(normalized_title(str(mapping.get("lean_declaration") or "")), [])
    if len(matches) != 1:
        return mapping
    resolved = dict(mapping)
    lean = matches[0]
    resolved["lean_module"] = lean.get("module") or resolved.get("lean_module")
    resolved["lean_declaration"] = terminal_declaration_name(lean)
    resolved["lean_object_id"] = lean.get("object_id")
    resolved["lean_path"] = lean.get("path")
    resolved["lean_line"] = lean.get("line")
    return resolved


def module_prefix(record: dict[str, Any], depth: int) -> str:
    parts = str(record.get("module") or "(missing)").split(".")
    return ".".join(parts[:depth]) if parts and parts[0] else "(missing)"


def tex_volume(record: dict[str, Any]) -> str:
    return str(record.get("volume") or str(record.get("path") or "").split("/", 1)[0] or "(unknown)")


def volume_i_region(record: dict[str, Any]) -> str | None:
    if tex_volume(record) != "volume-i":
        return None
    path = str(record.get("path") or "")
    if "propositional-logic" in path:
        return "propositional_logic"
    if "predicate-logic" in path:
        return "predicate_logic"
    if "axiom-systems" in path or "many-sorted-first-order-logic" in path or "second-order-logic" in path:
        return "axiom_systems_and_model_theory"
    if "book-sets/set-theory" in path:
        return "initial_set_theory"
    if any(part in path for part in ("book-sets/functions", "book-sets/functions-and-order", "book-sets/orderings", "book-sets/relations", "book-sets/cardinality")):
        return "set_order_relation_function_material"
    return "other_volume_i"


def compact_ref(record: dict[str, Any]) -> dict[str, Any]:
    ref = {
        "object_id": record.get("object_id"),
        "kind": record.get("kind"),
        "name": record.get("name"),
        "path": record.get("path"),
        "line": record.get("line"),
    }
    if record.get("label"):
        ref["label"] = record.get("label")
    if record.get("module"):
        ref["module"] = record.get("module")
    if record.get("declaration"):
        ref["declaration"] = record.get("declaration")
    return ref


def has_bracketed_display_name(record: dict[str, Any]) -> bool:
    name = str(record.get("name") or "")
    label = str(record.get("label") or "")
    return bool(name and name != label and not name.endswith(f":{record.get('line')}"))


def suspicious_reasons(tex: dict[str, Any], candidates: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    title = normalized_title(str(tex.get("name") or ""))
    if tex.get("metadata", {}).get("starred"):
        reasons.append("starred_restatement")
    if "/proofs/" in str(tex.get("path") or ""):
        reasons.append("proof_side_restatement")
    if title in GENERIC_TITLES:
        reasons.append("generic_title")
    if not has_bracketed_display_name(tex):
        reasons.append("missing_bracketed_display_name")
    if len(candidates) > 1:
        top = int(candidates[0].get("score") or 0)
        second = int(candidates[1].get("score") or 0)
        if second >= top - 20:
            reasons.append("multiple_close_candidates")
        else:
            reasons.append("multiple_candidates")
    if candidates and int(candidates[0].get("score") or 0) < 100:
        reasons.append("heuristic_candidate_only")
    return reasons


def build_report(
    index_payload: dict[str, Any],
    *,
    strict_plan: dict[str, Any] | None = None,
    scratch_mappings: list[dict[str, Any]] | None = None,
    production_only: bool = True,
    module_depth: int = 2,
    example_limit: int = 10,
) -> dict[str, Any]:
    tex_records = [item for item in index_payload.get("objects", []) if item.get("source_family") == "tex"]
    all_lean_records = [item for item in index_payload.get("objects", []) if item.get("source_family") == "lean"]
    lean_records = [item for item in all_lean_records if not production_only or production_lean(item)]
    strict_plan = strict_plan or build_plan(index_payload, status="pending", production_only=production_only, strict_safe=True)

    tex_by_id = {str(item["object_id"]): item for item in tex_records}
    production_lean_ids = {str(item["object_id"]) for item in lean_records}
    lean_by_identity = {lean_identity(item): item for item in lean_records}
    lean_by_declaration: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lean_by_normalized_declaration: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lean in lean_records:
        declaration = terminal_declaration_name(lean)
        lean_by_declaration[declaration].append(lean)
        lean_by_normalized_declaration[normalized_title(declaration)].append(lean)
    safe_entries = strict_plan.get("entries", [])
    safe_tex_ids = {str(item["tex_object_id"]) for item in safe_entries}
    safe_lean_identities = {
        (str(item.get("lean_module") or ""), str(item.get("lean_declaration") or "")) for item in safe_entries
    }

    linked_tex: list[dict[str, Any]] = []
    linked_identities: set[tuple[str, str]] = set()
    dangling_links: list[dict[str, Any]] = []
    for tex in tex_records:
        links = tex.get("metadata", {}).get("lean_formalizes") or []
        if not links:
            continue
        linked_tex.append({"tex": compact_ref(tex), "links": links})
        for link in links:
            identity = link_identity(link)
            linked_identities.add(identity)
            if identity not in lean_by_identity:
                dangling_links.append({"tex": compact_ref(tex), "link": link})

    match_report = index_payload.get("match_report") or {}
    candidate_by_tex = {
        str(item.get("tex_object_id")): item for item in match_report.get("candidate_matches", [])
    }
    scratch_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    resolved_scratch_mappings = [
        resolve_mapping_against_index(mapping, lean_by_declaration, lean_by_normalized_declaration)
        for mapping in scratch_mappings or []
    ]
    scratch_additions_without_tex = [
        mapping for mapping in resolved_scratch_mappings if not mapping.get("has_tex_label")
    ]
    for mapping in resolved_scratch_mappings:
        if mapping.get("has_tex_label"):
            scratch_by_label[str(mapping.get("tex_label") or "")].append(mapping)
    scratch_linked_tex = [
        {"tex": compact_ref(tex), "scratch_mappings": scratch_by_label[str(tex.get("label") or "")]}
        for tex in tex_records
        if str(tex.get("label") or "") in scratch_by_label
    ]
    scratch_only_tex = [
        item
        for item in scratch_linked_tex
        if str(item["tex"].get("object_id")) not in safe_tex_ids
        and not tex_by_id[str(item["tex"]["object_id"])].get("metadata", {}).get("lean_formalizes")
    ]

    review_items: list[dict[str, Any]] = []
    for tex_id, item in candidate_by_tex.items():
        if tex_id in safe_tex_ids:
            continue
        tex = tex_by_id.get(tex_id)
        if not tex or tex.get("metadata", {}).get("lean_formalizes"):
            continue
        candidates = [
            candidate
            for candidate in item.get("candidates", [])
            if not production_only or str(candidate.get("lean_object_id")) in production_lean_ids
        ]
        if not candidates:
            continue
        reasons = suspicious_reasons(tex, candidates)
        review_items.append(
            {
                "tex": compact_ref(tex),
                "reasons": reasons or ["broad_candidate_requires_review"],
                "candidates": candidates,
            }
        )

    missing_lean = [
        compact_ref(tex)
        for tex in tex_records
        if not tex.get("metadata", {}).get("lean_formalizes")
        and str(tex["object_id"]) not in safe_tex_ids
        and str(tex["object_id"]) not in candidate_by_tex
    ]
    lean_without_tex = [
        compact_ref(lean)
        for lean in lean_records
        if lean_identity(lean) not in linked_identities and lean_identity(lean) not in safe_lean_identities
    ]

    tex_by_volume_kind: dict[str, dict[str, int]] = defaultdict(dict)
    for (volume, kind), count in sorted(Counter((tex_volume(item), str(item["kind"])) for item in tex_records).items()):
        tex_by_volume_kind[volume][kind] = count

    tex_status_by_id: dict[str, str] = {}
    tex_status_by_id.update({str(item["tex"]["object_id"]): "already_tagged" for item in linked_tex})
    tex_status_by_id.update({str(item["tex_object_id"]): "strict_safe" for item in safe_entries})
    tex_status_by_id.update({str(item["object_id"]): "missing_lean" for item in missing_lean})
    for item in review_items:
        tex_status_by_id[str(item["tex"]["object_id"])] = "review"

    volume_i_region_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for tex in tex_records:
        region = volume_i_region(tex)
        if not region:
            continue
        status = tex_status_by_id.get(str(tex["object_id"]), "unclassified")
        volume_i_region_counts[region]["total"] += 1
        volume_i_region_counts[region][status] += 1

    lean_by_kind_prefix: dict[str, dict[str, int]] = defaultdict(dict)
    for (kind, prefix), count in sorted(Counter((str(item["kind"]), module_prefix(item, module_depth)) for item in lean_records).items()):
        lean_by_kind_prefix[kind][prefix] = count

    categories = {
        "tex_with_leanformalizes": linked_tex,
        "tex_with_exact_safe_matches": safe_entries,
        "tex_with_scratch_lean_mappings": scratch_linked_tex,
        "tex_with_scratch_only_mappings": scratch_only_tex,
        "lean_mapping_entries_without_tex_labels": scratch_additions_without_tex,
        "tex_missing_lean_matches": missing_lean,
        "lean_missing_tex_matches": lean_without_tex,
        "ambiguous_or_suspicious_matches": review_items + [
            {"tex": item["tex"], "reasons": ["leanformalizes_target_not_found"], "link": item["link"]}
            for item in dangling_links
        ],
    }
    return {
        "schema_version": "lra.lean-tex-crossref-report/1.0",
        "inputs": index_payload.get("inputs", {}),
        "counts": {
            "tex_objects": len(tex_records),
            "lean_declarations": len(lean_records),
            "lean_declarations_all_indexed": len(all_lean_records),
            "lean_nonproduction_excluded": len(all_lean_records) - len(lean_records),
            "tex_with_leanformalizes": len(linked_tex),
            "tex_with_exact_safe_matches": len(safe_entries),
            "tex_with_scratch_lean_mappings": len(scratch_linked_tex),
            "tex_with_scratch_only_mappings": len(scratch_only_tex),
            "lean_mapping_entries_without_tex_labels": len(scratch_additions_without_tex),
            "tex_missing_lean_matches": len(missing_lean),
            "lean_missing_tex_matches": len(lean_without_tex),
            "ambiguous_or_suspicious_matches": len(categories["ambiguous_or_suspicious_matches"]),
            "dangling_leanformalizes_links": len(dangling_links),
        },
        "totals": {
            "tex_by_volume_and_kind": dict(tex_by_volume_kind),
            "lean_by_kind_and_module_prefix": dict(lean_by_kind_prefix),
            "volume_i_by_region_and_status": {
                region: dict(counts) for region, counts in sorted(volume_i_region_counts.items())
            },
        },
        "policy": {
            "production_lean_only": production_only,
            "production_lean_path_prefix": "LRA/",
            "scratch_mappings_are_review_evidence_only": True,
            "lean_additions_without_tex_labels": (
                "Route to the owning TeX volume as content-addition work under governance; "
                "do not count as TeX-link coverage or add LeanFormalizes tags until matching TeX formal objects exist."
            ),
        },
        "categories": categories,
        "examples": {key: value[:example_limit] for key, value in categories.items()},
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        "# Lean <-> TeX Cross-Reference Report",
        "",
        "Generated from TeX source and Lean source indexes. Exact/safe matches come from the strict-safe formalization plan; broad candidates remain review-only.",
        "",
        "Lean mapping entries without TeX labels are content-addition candidates for the owning TeX volume. They are not TeX-link coverage and should not receive `\\LeanFormalizes` tags unless matching TeX formal objects are added under governance.",
        "",
        "## Summary",
        "",
        markdown_table(
            ["Category", "Count"],
            [
                ["TeX formal objects", counts["tex_objects"]],
                ["Lean declarations", counts["lean_declarations"]],
                ["All indexed Lean declarations", counts["lean_declarations_all_indexed"]],
                ["Nonproduction Lean declarations excluded", counts["lean_nonproduction_excluded"]],
                ["TeX objects already tagged", counts["tex_with_leanformalizes"]],
                ["TeX objects with exact/safe Lean matches", counts["tex_with_exact_safe_matches"]],
                ["TeX objects cited by mapping doc", counts["tex_with_scratch_lean_mappings"]],
                ["Mapping-doc TeX citations not production-tagged", counts["tex_with_scratch_only_mappings"]],
                ["Lean mapping entries without TeX labels", counts["lean_mapping_entries_without_tex_labels"]],
                ["TeX objects with no Lean match", counts["tex_missing_lean_matches"]],
                ["Lean declarations with no TeX match", counts["lean_missing_tex_matches"]],
                ["Ambiguous or suspicious matches", counts["ambiguous_or_suspicious_matches"]],
                ["Dangling LeanFormalizes targets", counts["dangling_leanformalizes_links"]],
            ],
        ),
        "",
        "## TeX Totals By Volume And Kind",
        "",
    ]
    tex_rows = []
    for volume, by_kind in report["totals"]["tex_by_volume_and_kind"].items():
        for kind, count in by_kind.items():
            tex_rows.append([volume, kind, count])
    lines.append(markdown_table(["Volume", "Kind", "Count"], tex_rows or [["(none)", "(none)", 0]]))
    volume_i_rows = []
    for region, by_status in report["totals"].get("volume_i_by_region_and_status", {}).items():
        volume_i_rows.append(
            [
                region,
                by_status.get("total", 0),
                by_status.get("already_tagged", 0),
                by_status.get("strict_safe", 0),
                by_status.get("review", 0),
                by_status.get("missing_lean", 0),
            ]
        )
    lines.extend(["", "## Volume I Region Breakdown", ""])
    lines.append(
        markdown_table(
            ["Region", "Total", "Tagged", "Strict-safe", "Review", "Missing Lean"],
            volume_i_rows or [["(none)", 0, 0, 0, 0, 0]],
        )
    )
    lines.extend(["", "## Lean Totals By Kind And Module Prefix", ""])
    lean_rows = []
    for kind, by_prefix in report["totals"]["lean_by_kind_and_module_prefix"].items():
        for prefix, count in by_prefix.items():
            lean_rows.append([kind, prefix, count])
    lines.append(markdown_table(["Kind", "Module prefix", "Count"], lean_rows or [["(none)", "(none)", 0]]))
    lines.extend(["", "## Examples", ""])
    example_titles = {
        "tex_with_leanformalizes": "TeX Objects Already Linked",
        "tex_with_exact_safe_matches": "Exact/Safe Lean Matches",
        "tex_with_scratch_lean_mappings": "Mapping-Doc Entries For Existing TeX Labels",
        "tex_with_scratch_only_mappings": "Mapping-Doc Entries Not Yet Production-Tagged",
        "lean_mapping_entries_without_tex_labels": "Lean Additions Without TeX Labels",
        "tex_missing_lean_matches": "TeX Objects Missing Lean Matches",
        "lean_missing_tex_matches": "Lean Declarations Missing TeX Matches",
        "ambiguous_or_suspicious_matches": "Ambiguous Or Suspicious Matches",
    }
    for key, title in example_titles.items():
        lines.extend([f"### {title}", ""])
        examples = report["examples"].get(key) or []
        if not examples:
            lines.extend(["No examples in this category.", ""])
            continue
        for item in examples:
            if key == "tex_with_exact_safe_matches":
                lines.append(
                    f"- `{item['tex_label']}` {item['tex_name']} -> `{item['lean_module']}.{item['lean_declaration']}`"
                    f" ({item['tex_path']}:{item['tex_line']})"
                )
            elif key == "tex_with_leanformalizes":
                tex = item["tex"]
                links = ", ".join(f"`{link['module']}.{link['declaration']}` ({link['status']})" for link in item["links"])
                lines.append(f"- `{tex.get('label', tex['object_id'])}` {tex['name']} -> {links} ({tex['path']}:{tex['line']})")
            elif key in {"tex_with_scratch_lean_mappings", "tex_with_scratch_only_mappings"}:
                tex = item["tex"]
                mappings = ", ".join(
                    f"`{mapping['lean_module']}.{mapping['lean_declaration']}`"
                    for mapping in item["scratch_mappings"][:3]
                )
                more = "" if len(item["scratch_mappings"]) <= 3 else f" +{len(item['scratch_mappings']) - 3} more"
                lines.append(
                    f"- `{tex.get('label', tex['object_id'])}` {tex['name']} -> {mappings}{more} "
                    f"({tex['path']}:{tex['line']})"
                )
            elif key == "lean_mapping_entries_without_tex_labels":
                lines.append(
                    f"- `{item['lean_module']}.{item['lean_declaration']}` "
                    f"({item.get('lean_path') or item['scratch_path']}:{item.get('lean_line') or item['source_line']})"
                )
            elif key == "ambiguous_or_suspicious_matches":
                tex = item["tex"]
                candidates = item.get("candidates") or []
                first = candidates[0] if candidates else item.get("link", {})
                target = first.get("declaration") or first.get("lean_object_id") or "(missing target)"
                lines.append(
                    f"- `{tex.get('label', tex['object_id'])}` {tex['name']} -> `{target}`; "
                    f"reasons: {', '.join(item['reasons'])} ({tex['path']}:{tex['line']})"
                )
            else:
                lines.append(f"- `{item.get('label') or item.get('declaration') or item['object_id']}` {item['name']} ({item['path']}:{item['line']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True, help="Internal object index JSON/YAML.")
    parser.add_argument("--strict-plan", type=Path, help="Optional strict-safe plan YAML/JSON.")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--include-nonproduction-lean", action="store_true")
    parser.add_argument("--module-prefix-depth", type=int, default=2)
    parser.add_argument("--example-limit", type=int, default=10)
    parser.add_argument(
        "--scratch-mapping",
        type=Path,
        action="append",
        default=[],
        help="Optional lra-lean LEAN_TEX_MAPPING.md file(s) to include as review-only scratch mappings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index_payload = load_structured(args.index)
    strict_plan = load_structured(args.strict_plan) if args.strict_plan else None
    scratch_mappings: list[dict[str, Any]] = []
    for path in args.scratch_mapping:
        scratch_mappings.extend(parse_scratch_mapping(path))
    report = build_report(
        index_payload,
        strict_plan=strict_plan,
        scratch_mappings=scratch_mappings,
        production_only=not args.include_nonproduction_lean,
        module_depth=args.module_prefix_depth,
        example_limit=args.example_limit,
    )
    write_structured(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "reported "
        f"{report['counts']['tex_objects']} TeX object(s), "
        f"{report['counts']['lean_declarations']} Lean declaration(s), "
        f"{report['counts']['ambiguous_or_suspicious_matches']} review item(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
