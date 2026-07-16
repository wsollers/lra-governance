#!/usr/bin/env python3
"""Generate a small static HTML page for the LRA ↔ Lean crosswalk registry."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_crosswalk(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def entry_row(entry: dict[str, Any]) -> str:
    lra = entry["lra"]
    lean = entry["lean"]
    lra_lean = entry.get("lra_lean")
    lra_name = html.escape(str(lra["name"]))
    predicate_id = html.escape(str(lra["predicate_id"]))
    declaration = html.escape(str(lean["display_name"]))
    module = html.escape(str(lean["module"]))
    docs_url = html.escape(str(lean["docs_url"]), quote=True)
    source_url = html.escape(str(lean["source_url"]), quote=True)
    signature = html.escape(str(lean["signature"]))
    proposition_lens = html.escape(str(lean["proposition_lens"]))
    expansion = html.escape(str(lean.get("expansion") or "—"))
    role = html.escape(str(entry["semantic_role"]))
    notes = html.escape(str(entry["notes"]))
    surfaces = ", ".join(html.escape(str(item)) for item in lra.get("surface_forms", []))
    if lra_lean:
        bridge = lra_lean.get("bridge_to_mathlib")
        bridge_text = ""
        if bridge:
            bridge_text = (
                "<br><small>bridge: "
                f"<code>{html.escape(str(bridge['declaration']))}</code> "
                f"<code>{html.escape(str(bridge['signature']))}</code>"
                "</small>"
            )
        lra_lean_cell = (
            f"<code>{html.escape(str(lra_lean['declaration']))}</code>"
            f"<br><small>{html.escape(str(lra_lean['file']))}:{int(lra_lean['line_hint'])}</small>"
            f"<br><code>{html.escape(str(lra_lean['proposition_lens']))}</code>"
            f"<br><small>{html.escape(str(lra_lean.get('expansion') or '—'))}</small>"
            f"{bridge_text}"
        )
    else:
        lra_lean_cell = "—"
    return f"""\
      <tr data-lra="{lra_name}" data-lean="{declaration}">
        <td><code>{predicate_id}</code><br><strong>{lra_name}</strong><br><small>{surfaces}</small></td>
        <td><a href="{docs_url}"><code>{declaration}</code></a><br><small>{module}</small><br><a href="{source_url}">source</a></td>
        <td>{lra_lean_cell}</td>
        <td>{role}</td>
        <td><code>{signature}</code><br><code>{proposition_lens}</code><br><small>{expansion}</small></td>
        <td>{notes}</td>
      </tr>"""


def render_html(crosswalk: dict[str, Any]) -> str:
    rows = "\n".join(entry_row(entry) for entry in crosswalk.get("entries", []))
    note = html.escape(str(crosswalk.get("source", {}).get("note", "")))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LRA ↔ Lean Crosswalk</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d8dee4; padding: 0.65rem; vertical-align: top; }}
    th {{ background: #f6f8fa; text-align: left; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 0.25rem; }}
    .toolbar {{ margin: 1rem 0; display: flex; gap: 0.5rem; flex-wrap: wrap; }}
    button {{ padding: 0.35rem 0.6rem; }}
    [data-view="lra"] .lean-only {{ display: none; }}
    [data-view="lean"] .lra-only {{ display: none; }}
  </style>
</head>
<body data-view="both">
  <h1>LRA ↔ Lean Crosswalk</h1>
  <p>{note}</p>
  <div class="toolbar" aria-label="view toggle">
    <button type="button" onclick="document.body.dataset.view='lra'">LRA lens</button>
    <button type="button" onclick="document.body.dataset.view='lean'">Lean lens</button>
    <button type="button" onclick="document.body.dataset.view='both'">Both</button>
  </div>
  <table>
    <thead>
      <tr>
        <th class="lra-only">LRA predicate</th>
        <th class="lean-only">Lean/mathlib anchor</th>
        <th>LRA Lean anchor</th>
        <th>Role</th>
        <th>Formal lens</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""


def write_html(crosswalk_path: Path, output_path: Path) -> None:
    crosswalk = load_crosswalk(crosswalk_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(crosswalk), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crosswalk", type=Path, default=ROOT / "lean-crosswalk.yaml")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_html(args.crosswalk, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
