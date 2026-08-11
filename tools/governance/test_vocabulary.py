from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

import vocabulary


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def make_registry_root(root: Path) -> None:
    write_yaml(
        root / "predicates.yaml",
        {
            "predicates": [
                {
                    "id": "pred:upper-bound",
                    "name": "UpperBound",
                    "kind": "predicate",
                    "category": "order",
                    "arguments": [
                        {"name": "u", "role": "bound"},
                        {"name": "S", "role": "subset"},
                        {"name": "P", "role": "ambient_order"},
                    ],
                    "returns": "truth_value",
                    "surface_forms": ["upper bound", "bounds above"],
                    "description": "An element is an upper bound of a subset in an ordered set.",
                }
            ]
        },
    )
    write_yaml(
        root / "structures.yaml",
        {
            "structures": [
                {
                    "id": "struct:ordered-set",
                    "name": "OrderedSet",
                    "kind": "structure",
                    "category": "order",
                    "constructor": r"\mathsf{OrderedSet}",
                    "arguments": [
                        {"name": "A", "role": "carrier"},
                        {"name": "le", "role": "order_relation"},
                    ],
                    "carrier_argument": "A",
                    "structural_arguments": ["le"],
                    "surface_forms": ["ordered set", "poset ambient"],
                    "description": "A carrier equipped with an order relation.",
                }
            ]
        },
    )
    write_yaml(
        root / "notation.yaml",
        {
            "notation": [
                {
                    "id": "not:real-numbers",
                    "symbol": r"\mathbb{R}",
                    "category": "number_system",
                    "description": "Real numbers.",
                }
            ]
        },
    )
    write_yaml(
        root / "relations.yaml",
        {"edge_kinds": ["specializes"], "relations": []},
    )


class VocabularyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        make_registry_root(self.root)
        self.index = self.root / "index" / "vocabulary.sqlite"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_builds_fresh_index_and_reports_counts(self):
        result = vocabulary.build_index(self.root, self.index)

        self.assertEqual(result["entry_count"], 3)
        self.assertEqual(result["active_count"], 3)
        self.assertTrue(vocabulary.index_status(self.root, self.index)["fresh"])

    def test_exact_lookup_accepts_id_name_surface_form_and_symbol(self):
        vocabulary.build_index(self.root, self.index)

        for query in ("pred:upper-bound", "UpperBound", "upper bound"):
            matches = vocabulary.exact_matches(
                self.index,
                query,
                kind="predicate",
                include_testing=False,
                full=True,
            )
            self.assertEqual(matches[0]["record"]["id"], "pred:upper-bound")

        notation = vocabulary.exact_matches(
            self.index,
            r"\mathbb{R}",
            kind="notation",
            include_testing=False,
            full=True,
        )
        self.assertEqual(notation[0]["record"]["id"], "not:real-numbers")

    def test_search_returns_small_summaries(self):
        vocabulary.build_index(self.root, self.index)

        matches = vocabulary.search_entries(
            self.index,
            "bound ordered subset",
            kind="predicate",
            include_testing=False,
            limit=5,
        )

        self.assertEqual(matches[0]["id"], "pred:upper-bound")
        self.assertNotIn("record", matches[0])

    def test_overloaded_alias_returns_every_matching_entry(self):
        path = self.root / "predicates.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        overloaded = dict(data["predicates"][0])
        overloaded["id"] = "pred:upper-bound-relative"
        data["predicates"].append(overloaded)
        write_yaml(path, data)

        vocabulary.build_index(self.root, self.index)
        matches = vocabulary.exact_matches(
            self.index,
            "UpperBound",
            kind="predicate",
            include_testing=False,
            full=False,
        )

        self.assertEqual(
            [match["id"] for match in matches],
            ["pred:upper-bound", "pred:upper-bound-relative"],
        )

    def test_duplicate_id_is_losslessly_indexed_and_reported(self):
        path = self.root / "notation.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        duplicate = dict(data["notation"][0])
        duplicate["symbol"] = r"\mathbf{R}"
        data["notation"].append(duplicate)
        write_yaml(path, data)

        result = vocabulary.build_index(self.root, self.index)
        matches = vocabulary.exact_matches(
            self.index,
            "not:real-numbers",
            kind="notation",
            include_testing=False,
            full=False,
        )

        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[1]["index_key"], "not:real-numbers#2")
        self.assertIn("not:real-numbers", result["duplicate_ids"])

    def test_source_change_marks_index_stale(self):
        vocabulary.build_index(self.root, self.index)
        path = self.root / "notation.yaml"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        self.assertFalse(vocabulary.index_status(self.root, self.index)["fresh"])
        vocabulary.ensure_index(self.root, self.index, refresh=True)
        self.assertTrue(vocabulary.index_status(self.root, self.index)["fresh"])

    def test_add_is_dry_run_by_default_and_write_reindexes(self):
        vocabulary.build_index(self.root, self.index)
        candidate = self.root / "candidate.yaml"
        write_yaml(
            candidate,
            {
                "id": "not:star-operation",
                "symbol": r"\star",
                "category": "operation",
                "description": "A generic binary operation symbol.",
            },
        )
        original = (self.root / "notation.yaml").read_text(encoding="utf-8")

        preview = vocabulary.add_entry(
            self.root,
            self.index,
            kind="notation",
            candidate_path=candidate,
            write=False,
        )
        self.assertFalse(preview["write"])
        self.assertEqual((self.root / "notation.yaml").read_text(encoding="utf-8"), original)

        result = vocabulary.add_entry(
            self.root,
            self.index,
            kind="notation",
            candidate_path=candidate,
            write=True,
        )
        self.assertTrue(result["write"])
        matches = vocabulary.exact_matches(
            self.index,
            r"\star",
            kind="notation",
            include_testing=False,
            full=True,
        )
        self.assertEqual(matches[0]["record"]["id"], "not:star-operation")

    def test_invalid_add_restores_canonical_file(self):
        vocabulary.build_index(self.root, self.index)
        candidate = self.root / "bad.yaml"
        write_yaml(
            candidate,
            {
                "id": "pred:bad",
                "name": "Bad",
                "kind": "predicate",
                "category": "test",
            },
        )
        target = self.root / "predicates.yaml"
        original = target.read_text(encoding="utf-8")

        with self.assertRaises(vocabulary.VocabularyError):
            vocabulary.add_entry(
                self.root,
                self.index,
                kind="predicate",
                candidate_path=candidate,
                write=True,
            )

        self.assertEqual(target.read_text(encoding="utf-8"), original)
        self.assertTrue(vocabulary.index_status(self.root, self.index)["fresh"])


if __name__ == "__main__":
    unittest.main()
