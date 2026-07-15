from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE_PATH = Path(__file__).with_name("validate_topic_semantic_audit.py")
SPEC = importlib.util.spec_from_file_location("validate_topic_semantic_audit", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TopicSemanticAuditValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.gov = self.root / "lra-governance"
        self.repo = self.root / "lra-volume-iii"
        (self.gov / "constitution" / "schema").mkdir(parents=True)
        schema_source = Path(__file__).resolve().parents[2] / "constitution" / "schema" / "topic-semantic-audit.schema.json"
        (self.gov / "constitution" / "schema" / "topic-semantic-audit.schema.json").write_text(
            schema_source.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.topic = self.repo / "volume-iii" / "book-analysis-i" / "bounding" / "notes" / "bounds-extremals"
        self.topic.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_package(self, slug: str) -> str:
        rel = Path("volume-iii/book-analysis-i/bounding/notes/bounds-extremals") / slug
        folder = self.repo / rel
        folder.mkdir(parents=True)
        for name in MODULE.REVIEW_FILES | MODULE.AUDIT_FILES:
            folder.joinpath(name).write_text("{}\n" if name.endswith(".yaml") else "test\n", encoding="utf-8")
        return rel.as_posix()

    def manifest(self, review_directory: str, **overrides):
        commit = "a" * 40
        artifact = {
            "order": 1,
            "label": "def:supremum",
            "kind": "definition",
            "title": "Supremum",
            "source_file": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
            "source_line_start": 10,
            "source_line_end": 50,
            "review_directory": review_directory,
            "status": "validated",
            "review_commit": commit,
            "temporary_apply_commit": "b" * 40,
            "revert_commit": "c" * 40,
            "deterministic_result": "pass",
            "logic_result": "pass",
            "source_restored": True,
            "blocking_issues": [],
            "notes": None,
        }
        artifact.update(overrides)
        return {
            "schema_version": "lra-topic-semantic-audit/1.0",
            "topic": {
                "repository": "wsollers/lra-volume-iii",
                "branch": "audit/bounds-extremals-semantic-artifacts",
                "volume": "volume-iii",
                "book": "book-analysis-i",
                "chapter": "bounding",
                "topic_id": "bounds-extremals",
                "notes_directory": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals",
                "governance_commit": "d" * 40,
                "started_at": None,
                "completed_at": None,
            },
            "source_baseline": {
                "commit": "e" * 40,
                "router_closure_hash": "sha256:" + "f" * 64,
                "source_files": [
                    {
                        "path": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
                        "blob_sha": "1" * 40,
                    }
                ],
            },
            "artifacts": [artifact],
            "summary": {
                "inventory_count": 1,
                "validated_count": 1,
                "failed_count": 0,
                "blocked_count": 0,
                "source_restored": True,
                "final_validation_commit": "2" * 40,
                "unresolved_labels": [],
            },
        }

    def validate(self, data, strict=True):
        path = self.topic / "semantic-topic-audit.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        result = MODULE.Result()
        MODULE.schema_validate(
            data,
            self.gov / "constitution" / "schema" / "topic-semantic-audit.schema.json",
            result,
        )
        MODULE.semantic_checks(data, self.repo, strict, result)
        return result

    def test_accepts_complete_restored_audit(self):
        review_directory = self.write_package("def-supremum")
        result = self.validate(self.manifest(review_directory))
        self.assertTrue(result.clean, result.errors)

    def test_rejects_temporary_commit_without_revert(self):
        review_directory = self.write_package("def-supremum")
        data = self.manifest(review_directory, revert_commit=None)
        result = self.validate(data)
        self.assertFalse(result.clean)
        self.assertTrue(any("matching revert" in message or "revert_commit" in message for message in result.errors))

    def test_rejects_incorrect_summary_counts(self):
        review_directory = self.write_package("def-supremum")
        data = self.manifest(review_directory)
        data["summary"]["validated_count"] = 0
        result = self.validate(data)
        self.assertFalse(result.clean)
        self.assertTrue(any("summary.validated_count" in message for message in result.errors))


if __name__ == "__main__":
    unittest.main()
