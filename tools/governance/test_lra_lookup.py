from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import yaml

import lra_lookup
from internal_object_sqlite import build_database


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


class LookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.governance = self.root / "lra-governance"
        self.catalog = self.root / "lra-sources"
        self.profiles = self.root / "lra-source-profiles"
        self.index_root = self.root / "indexes"
        self.governance.mkdir()
        self.profiles.mkdir()
        self.index_root.mkdir()
        write_yaml(
            self.catalog / "index.yaml",
            {
                "source_profiles_root": str(self.profiles),
                "source_index_root": str(self.index_root),
            },
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_catalog_resolves_profile_and_index_roots(self) -> None:
        with patch.dict("os.environ", {"LRA_SOURCES_ROOT": str(self.catalog)}, clear=True):
            locations = lra_lookup.resolve_locations(self.governance)

        self.assertEqual(locations.catalog_root, self.catalog)
        self.assertEqual(locations.source_profiles_root, self.profiles)
        self.assertEqual(locations.index_root, self.index_root)

    def test_scope_expansion(self) -> None:
        self.assertEqual(
            lra_lookup.expand_scopes(["internal"]), {"tex", "lean", "cpp"}
        )
        self.assertEqual(
            lra_lookup.expand_scopes(None),
            {"sources", "tex", "lean", "cpp", "vocabulary"},
        )

    def test_internal_search_returns_compact_records(self) -> None:
        path = self.index_root / lra_lookup.INTERNAL_DATABASES["tex"]
        records = [
                    {
                        "object_id": "tex:thm:least-upper-bound",
                        "source_family": "tex",
                        "kind": "theorem",
                        "name": "Least Upper Bound",
                        "label": "thm:least-upper-bound",
                        "repo_root": "F:/repos/lra-volume-iii",
                        "path": "notes/theorem.tex",
                        "line": 12,
                        "statement": "Every nonempty bounded-above set has a supremum.",
                        "search_text": "least upper bound supremum bounded above",
                        "metadata": {},
                    }
                ]
        build_database(
            records,
            family="tex",
            db_path=path,
        )
        locations = lra_lookup.LookupLocations(self.catalog, self.profiles, self.index_root)

        results = lra_lookup.search_internal(
            locations, "least upper bound", {"tex"}, limit=3, volume=None
        )

        self.assertEqual(results["tex"][0]["label"], "thm:least-upper-bound")
        self.assertNotIn("search_text", results["tex"][0])

    def test_lookup_preserves_other_lanes_when_one_is_unavailable(self) -> None:
        args = Namespace(
            query="least upper bound",
            scope=["sources", "tex"],
            limit=3,
            author=[],
            source_id=[],
            source_list=[],
            profile=None,
            volume=None,
            book=None,
            chapter=None,
            include_disabled=False,
        )
        locations = lra_lookup.LookupLocations(None, None, None)
        with patch.object(lra_lookup, "search_internal", return_value={"tex": [{"id": "x"}]}):
            payload = lra_lookup.lookup(args, locations)

        self.assertEqual(payload["results"]["tex"], [{"id": "x"}])
        self.assertTrue(any(item.startswith("sources:") for item in payload["warnings"]))


if __name__ == "__main__":
    unittest.main()
