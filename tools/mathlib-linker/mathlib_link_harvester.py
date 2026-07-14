#!/usr/bin/env python3
"""
mathlib_link_harvester.py

Given a list of Lean/Mathlib4 identifiers (or LRA predicate names mapped to
candidate Mathlib identifiers), resolves each to:

  - its defining module (via the Loogle JSON API, exact-name filtered)
  - its doc-gen4 documentation URL (static, stable)
  - its exact GitHub source permalink, pinned to the commit doc-gen4 built
    from, with a precise line range (scraped from the static doc page)

Two-step pipeline (no headless browser / JS execution needed):
  1. Loogle (https://loogle.lean-lang.org/json?q=<name>) returns a list of
     hits "mentioning" the query; we keep only the hit whose `name` field is
     an *exact* match, and read off its `module`.
  2. The static doc-gen4 page for that module
     (https://leanprover-community.github.io/mathlib4_docs/<Module/Path>.html)
     contains a `<div class="decl" id="<Name>">` block with a
     `<div class="gh_link"><a href="...">source</a></div>` -- a GitHub
     permalink of the form
     https://github.com/leanprover-community/mathlib4/blob/<sha>/<path>.lean#L<a>-L<b>

Notes on failure modes this script surfaces rather than hides:
  - Aliases: Loogle's `doc` field often starts with "**Alias** of `X`."
    We record this and DO NOT silently follow it to X -- the caller decides.
  - No exact match: reported as NOT_FOUND rather than guessed.
  - Ambiguous LRA -> Mathlib mapping (multiple plausible candidates): the
    input format supports a list of candidates per LRA name; the first
    resolvable one wins, all attempts are logged.
  - A "FOUND" result means the Mathlib declaration exists and the link is
    correct. It does NOT mean the Mathlib declaration is mathematically the
    same construction as your LRA definition (e.g. Mathlib's `DedekindCut`
    is a generic Dedekind-MacNeille order completion, not the specific
    Dedekind-cut construction of the reals) -- that judgment call is left
    to you, deliberately.

Usage:
    python3 mathlib_link_harvester.py mapping.yaml output.md

mapping.yaml format:
    - lra_name: LeastUpperBound
      candidates: [IsLUB]
    - lra_name: Bounded
      candidates: [Bornology.IsBounded, Metric.Bounded]
"""
import sys
import json
import time
import urllib.request
import urllib.parse
import yaml
from bs4 import BeautifulSoup

LOOGLE_URL = "https://loogle.lean-lang.org/json?q={}"
DOCS_ROOT = "https://leanprover-community.github.io/mathlib4_docs/"
USER_AGENT = "lra-volume-ii-mathlib-linker/1.0 (research tooling; contact via repo)"


def http_get(url, retries=3, delay=1.5):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(delay)
    raise RuntimeError(f"GET failed for {url}: {last_err}")


def loogle_exact_lookup(name):
    """Return (module, doc_string, is_alias, alias_of) or None if no exact match."""
    for query in (name,):
        raw = http_get(LOOGLE_URL.format(urllib.parse.quote(query)))
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for hit in data.get("hits", []):
            if hit.get("name") == name:
                doc = hit.get("doc") or ""
                is_alias = doc.strip().startswith("**Alias**")
                alias_of = None
                if is_alias and "`" in doc:
                    parts = doc.split("`")
                    if len(parts) >= 2:
                        alias_of = parts[1]
                return hit.get("module"), doc, is_alias, alias_of
    return None


def module_to_doc_path(module):
    return module.replace(".", "/") + ".html"


def fetch_source_link(module, name):
    """Scrape the static doc-gen4 page for the gh_link href in the decl block."""
    page_url = DOCS_ROOT + module_to_doc_path(module)
    html = http_get(page_url)
    soup = BeautifulSoup(html, "html.parser")
    decl_div = soup.find("div", {"class": "decl", "id": name})
    if decl_div is None:
        return page_url, None
    gh_link_div = decl_div.find("div", {"class": "gh_link"})
    if gh_link_div is None:
        return page_url, None
    a = gh_link_div.find("a")
    return page_url, (a["href"] if a and a.has_attr("href") else None)


def harvest(lra_name, candidates):
    for cand in candidates:
        try:
            result = loogle_exact_lookup(cand)
        except Exception as e:  # noqa: BLE001
            return {
                "lra_name": lra_name, "mathlib_name": cand, "module": None,
                "doc_url": None, "source_url": None,
                "status": "ERROR", "notes": str(e),
            }
        if result is None:
            continue
        module, doc, is_alias, alias_of = result
        doc_url = DOCS_ROOT + module_to_doc_path(module) + f"#{cand}"
        try:
            _, source_url = fetch_source_link(module, cand)
        except Exception as e:  # noqa: BLE001
            source_url = None
            notes = f"source scrape failed: {e}"
        else:
            notes = ""
        if is_alias:
            notes = (notes + " " if notes else "") + f"ALIAS of `{alias_of}` (not followed)"
        return {
            "lra_name": lra_name, "mathlib_name": cand, "module": module,
            "doc_url": doc_url, "source_url": source_url,
            "status": "FOUND" if source_url else "FOUND_NO_SOURCE_LINK",
            "notes": notes.strip(),
        }
    return {
        "lra_name": lra_name, "mathlib_name": "/".join(candidates), "module": None,
        "doc_url": None, "source_url": None,
        "status": "NOT_FOUND", "notes": "no exact-name match among candidates",
    }


def render_markdown(rows):
    out = ["| LRA predicate | Mathlib name | Doc link | Source (commit-pinned) | Status | Notes |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        doc = f"[{r['mathlib_name']}]({r['doc_url']})" if r["doc_url"] else "\u2014"
        src = f"[source]({r['source_url']})" if r["source_url"] else "\u2014"
        out.append(f"| {r['lra_name']} | {r['mathlib_name']} | {doc} | {src} | {r['status']} | {r['notes']} |")
    return "\n".join(out)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    mapping_path, output_path = sys.argv[1], sys.argv[2]
    with open(mapping_path, encoding="utf-8") as f:
        mapping = yaml.safe_load(f)

    rows = []
    for entry in mapping:
        lra_name = entry["lra_name"]
        candidates = entry["candidates"]
        print(f"Resolving {lra_name} -> {candidates} ...", file=sys.stderr)
        rows.append(harvest(lra_name, candidates))
        time.sleep(0.5)  # be polite to Loogle / GitHub Pages

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(rows))
    print(f"Wrote {len(rows)} rows to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
