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

    def test_author_filtered_source_miss_warns_to_retry_more_broadly(self) -> None:
        args = Namespace(
            query="pointlike function",
            scope=["sources"],
            limit=3,
            author=["Searcoid"],
            source_id=[],
            source_list=[],
            profile=None,
            volume=None,
            book=None,
            chapter=None,
            include_disabled=False,
        )
        locations = lra_lookup.LookupLocations(self.catalog, self.profiles, self.index_root)
        with patch.object(
            lra_lookup,
            "search_sources",
            return_value={"hits": [], "codesearch": [], "filters": {}},
        ):
            payload = lra_lookup.lookup(args, locations)

        self.assertIn("sources", payload["results"])
        self.assertTrue(
            any("retry sources without --author" in item for item in payload["warnings"])
        )

    def test_unfiltered_source_miss_does_not_warn_about_author_filter(self) -> None:
        args = Namespace(
            query="pointlike function",
            scope=["sources"],
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
        locations = lra_lookup.LookupLocations(self.catalog, self.profiles, self.index_root)
        with patch.object(
            lra_lookup,
            "search_sources",
            return_value={"hits": [], "codesearch": [], "filters": {}},
        ):
            payload = lra_lookup.lookup(args, locations)

        self.assertEqual(payload["warnings"], [])

    def test_loose_source_planner_extracts_from_author_hint(self) -> None:
        args = Namespace(
            author=[],
            source_id=[],
            source_list=[],
            profile=None,
            book=None,
            chapter=None,
        )

        attempts = lra_lookup.plan_loose_source_attempts(
            "derivative def from zorich", args
        )

        self.assertEqual(attempts[0].query, "derivative definition")
        self.assertEqual(attempts[0].authors, ("zorich",))
        self.assertIn(
            lra_lookup.SourceLooseAttempt("derivative definition"),
            attempts,
        )

    def test_loose_source_planner_handles_typos_and_open_author_query(self) -> None:
        args = Namespace(
            author=[],
            source_id=[],
            source_list=[],
            profile=None,
            book=None,
            chapter=None,
        )

        attempts = lra_lookup.plan_loose_source_attempts(
            "Which authors have guage and partition info for analysis", args
        )

        self.assertEqual(attempts, [lra_lookup.SourceLooseAttempt("gauge partition analysis")])

    def test_loose_source_results_fill_zero_hit_strict_source_query(self) -> None:
        args = Namespace(
            query="tao sigma algebra",
            scope=["sources"],
            limit=3,
            author=[],
            source_id=[],
            source_list=[],
            profile=None,
            volume=None,
            book=None,
            chapter=None,
            include_disabled=False,
            loose_sources=True,
        )
        locations = lra_lookup.LookupLocations(self.catalog, self.profiles, self.index_root)
        strict = {"hits": [], "codesearch": [], "filters": {}}
        loose_hit = {
            "score": 1.0,
            "kind": "definition",
            "number": None,
            "title": "Sigma Algebra",
            "source_id": "tao-analysis",
            "source_title": "Analysis",
            "author": "Tao",
            "volume": None,
            "path": "tao.md",
            "line": 10,
            "snippet": "A sigma algebra is...",
        }
        with patch.object(
            lra_lookup,
            "search_sources",
            side_effect=[
                strict,
                {"hits": [loose_hit], "codesearch": [], "filters": {}},
                {"hits": [], "codesearch": [], "filters": {}},
            ],
        ) as search:
            payload = lra_lookup.lookup(args, locations)

        self.assertEqual(search.call_args_list[1].args[1], "sigma algebra")
        retry_args = search.call_args_list[1].kwargs["args"]
        self.assertEqual(retry_args.author, ["tao"])
        hit = payload["results"]["sources"]["hits"][0]
        self.assertEqual(hit["matched_query"], "sigma algebra")
        self.assertEqual(hit["matched_author_filter"], ["tao"])
        self.assertTrue(any("loose retry returned" in item for item in payload["warnings"]))


if __name__ == "__main__":
    unittest.main()
