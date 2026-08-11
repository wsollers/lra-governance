from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from internal_object_sqlite import build_family_databases, metadata, query_candidates
from search_internal_object_index import search_sqlite


def record(family: str, name: str, path: str, *, object_id: str = "duplicate-id") -> dict:
    return {
        "object_id": object_id,
        "source_family": family,
        "kind": "theorem" if family != "cpp" else "function",
        "name": name,
        "declaration": name.replace(" ", "_"),
        "repo_root": "F:/repos/example",
        "path": path,
        "line": 7,
        "statement": f"The {name} statement concerns a supremum of a sum.",
        "search_text": f"{name} supremum sum",
        "metadata": {},
    }


class InternalObjectSqliteTests(unittest.TestCase):
    def test_builds_separate_databases_and_accepts_duplicate_object_ids(self) -> None:
        records = [
            record("tex", "Supremum Subadditivity", "one.tex"),
            record("tex", "Second Copy", "two.tex"),
            record("lean", "supremum_subadditivity", "One.lean"),
            record("cpp", "rough_supremum", "one.cpp"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            sqlite_dir = Path(temporary)
            results = build_family_databases(
                records,
                families=("tex", "lean", "cpp"),
                sqlite_dir=sqlite_dir,
            )

            self.assertEqual([item["objects"] for item in results], [2, 1, 1])
            self.assertEqual(metadata(sqlite_dir / "tex-search.sqlite")["object_count"], "2")
            self.assertTrue(sqlite_dir.joinpath("lean-search.sqlite").exists())
            self.assertTrue(sqlite_dir.joinpath("cpp-search.sqlite").exists())

    def test_queries_candidates_without_loading_yaml(self) -> None:
        records = [record("tex", "Supremum Subadditivity", "one.tex")]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tex-search.sqlite"
            build_family_databases(records, families=("tex",), sqlite_dir=path.parent)

            hits = query_candidates(path, ["supremum", "sum"], source_family="tex")

            self.assertEqual(hits[0]["name"], "Supremum Subadditivity")

    def test_sqlite_search_retains_typo_tolerant_ranking(self) -> None:
        records = [record("tex", "Supremum Subadditivity", "one.tex")]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tex-search.sqlite"
            build_family_databases(records, families=("tex",), sqlite_dir=path.parent)

            hits = search_sqlite(path, "sumpremum sum", source_family="tex")

            self.assertEqual(hits[0]["name"], "Supremum Subadditivity")


if __name__ == "__main__":
    unittest.main()
