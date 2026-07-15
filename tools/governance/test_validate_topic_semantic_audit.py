from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE_PATH = Path(__file__).with_name("validate_topic_semantic_audit.py")
SPEC = importlib.util.spec_from_file_location("validate_topic_semantic_audit", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def reviewer(role: str, response_id: str) -> dict:
    return {
        "provider": "openai_responses_api",
        "role": role,
        "requested_model": "gpt-5.6",
        "resolved_model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "response_id": response_id,
        "request_id": "req_test",
        "prompt": "constitution/prompts/test.md",
        "executor": "tools/governance/invoke_external_gpt_reviewer.py",
        "input_sha256": "sha256:" + "1" * 64,
        "output_sha256": "sha256:" + "2" * 64,
        "started_at": "2026-07-15T12:00:00Z",
        "completed_at": "2026-07-15T12:01:00Z",
        "self_review": False,
    }


class TopicSemanticAuditValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.gov = self.root / "lra-governance"
        self.repo = self.root / "lra-volume-iii"
        schema_dir = self.gov / "constitution" / "schema"
        schema_dir.mkdir(parents=True)
        canonical = Path(__file__).resolve().parents[2] / "constitution" / "schema"
        for name in ("topic-semantic-audit.schema.json", "artifact-audit-validation.schema.json"):
            schema_dir.joinpath(name).write_text(canonical.joinpath(name).read_text(encoding="utf-8"), encoding="utf-8")
        self.topic = self.repo / "volume-iii/book-analysis-i/bounding/notes/bounds-extremals"
        self.topic.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def audit_record(self, review_directory: str, *, revert_commit: str | None = "c" * 40, restored: bool = True) -> dict:
        check_names = (
            "binder_scope", "language_level", "assumptions_and_conclusion", "statement_shape",
            "quantifier_order", "witness_dependencies", "negation", "normalization_assumptions",
            "contrapositive", "applicability_failure", "order_strength", "predicate_signatures",
            "failure_modes", "yaml_tex_equivalence",
        )
        return {
            "schema_version": "lra-artifact-audit-validation/1.0",
            "artifact": {
                "label": "def:supremum", "kind": "definition",
                "source_file": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
                "review_directory": review_directory,
            },
            "review_package": {
                "result": "pass", "review_commit": "a" * 40,
                "semantic_artifact_command": "validate_semantic_artifact.py", "exit_code": 0,
                "reviewer": reviewer("semantic_reviewer", "resp_semantic_test"), "findings": [],
            },
            "temporary_application": {
                "applied": True, "commit": "b" * 40,
                "changed_files": [{
                    "path": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
                    "pre_apply_blob_sha": "1" * 40, "tested_blob_sha": "2" * 40,
                }],
            },
            "deterministic_validation": {
                "result": "pass",
                "checks": [{
                    "id": "semantic_artifact", "command": "validate_semantic_artifact.py",
                    "result": "pass", "exit_code": 0, "started_at": None, "completed_at": None,
                    "log_path": None, "findings": [],
                }],
            },
            "logic_validation": {
                "result": "pass", "reviewer": reviewer("logic_validator", "resp_logic_test"),
                "checks": {name: {"result": "pass", "notes": None} for name in check_names},
                "findings": [],
            },
            "reversion": {
                "required": True, "commit": revert_commit, "source_restored": restored,
                "verified_files": [{
                    "path": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
                    "expected_blob_sha": "1" * 40,
                    "actual_blob_sha": "1" * 40 if restored else "3" * 40,
                    "matches": restored,
                }],
            },
            "overall": {
                "result": "pass" if restored and revert_commit else "fail",
                "blocking_issues": [], "warnings": [],
            },
        }

    def write_package(self, slug: str, *, revert_commit: str | None = "c" * 40, restored: bool = True) -> str:
        rel = Path("volume-iii/book-analysis-i/bounding/notes/bounds-extremals") / slug
        folder = self.repo / rel
        folder.mkdir(parents=True)
        for name in MODULE.REVIEW_FILES:
            folder.joinpath(name).write_text("{}\n" if name.endswith(".yaml") else "test\n", encoding="utf-8")
        folder.joinpath(MODULE.AUDIT_FILE).write_text(
            yaml.safe_dump(self.audit_record(rel.as_posix(), revert_commit=revert_commit, restored=restored), sort_keys=False),
            encoding="utf-8",
        )
        return rel.as_posix()

    def manifest(self, review_directory: str, **overrides) -> dict:
        artifact = {
            "order": 1, "label": "def:supremum", "kind": "definition", "title": "Supremum",
            "source_file": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
            "source_line_start": 10, "source_line_end": 50,
            "review_directory": review_directory,
            "audit_validation_file": f"{review_directory}/audit-validation.yaml",
            "status": "validated", "review_commit": "a" * 40,
            "temporary_apply_commit": "b" * 40, "revert_commit": "c" * 40,
            "deterministic_result": "pass", "logic_result": "pass", "source_restored": True,
            "blocking_issues": [], "notes": None,
        }
        artifact.update(overrides)
        return {
            "schema_version": "lra-topic-semantic-audit/1.0",
            "topic": {
                "repository": "wsollers/lra-volume-iii", "branch": "audit/bounds-extremals-semantic-artifacts",
                "volume": "volume-iii", "book": "book-analysis-i", "chapter": "bounding",
                "topic_id": "bounds-extremals",
                "notes_directory": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals",
                "governance_commit": "d" * 40, "inventory_commit": "4" * 40,
                "started_at": None, "completed_at": None,
            },
            "source_baseline": {
                "commit": "e" * 40, "router_closure_hash": "sha256:" + "f" * 64,
                "source_files": [{
                    "path": "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/notes-bounds-extremals.tex",
                    "blob_sha": "1" * 40,
                }],
            },
            "artifacts": [artifact],
            "summary": {
                "inventory_count": 1, "validated_count": 1, "failed_count": 0,
                "blocked_count": 0, "source_restored": True, "unresolved_labels": [],
            },
        }

    def validate(self, data: dict, strict: bool = True):
        path = self.topic / "semantic-topic-audit.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        result = MODULE.Result()
        MODULE.schema_validate(data, self.gov / "constitution/schema/topic-semantic-audit.schema.json", "topic", result)
        MODULE.semantic_checks(data, self.repo, self.gov, strict, result)
        return result

    def test_accepts_complete_restored_audit(self):
        review_directory = self.write_package("def-supremum")
        result = self.validate(self.manifest(review_directory))
        self.assertTrue(result.clean, result.errors)

    def test_rejects_temporary_commit_without_revert(self):
        review_directory = self.write_package("def-supremum", revert_commit=None)
        result = self.validate(self.manifest(review_directory, revert_commit=None))
        self.assertFalse(result.clean)
        self.assertTrue(any("revert" in message for message in result.errors))

    def test_rejects_incorrect_summary_counts(self):
        review_directory = self.write_package("def-supremum")
        data = self.manifest(review_directory)
        data["summary"]["validated_count"] = 0
        result = self.validate(data)
        self.assertFalse(result.clean)
        self.assertTrue(any("summary.validated_count" in message for message in result.errors))

    def test_allows_queued_inventory_without_review_folders_non_strict(self):
        review_directory = "volume-iii/book-analysis-i/bounding/notes/bounds-extremals/def-supremum"
        data = self.manifest(
            review_directory, status="queued", review_commit=None,
            temporary_apply_commit=None, revert_commit=None,
            deterministic_result="not_run", logic_result="not_run", source_restored=False,
        )
        data["topic"]["inventory_commit"] = None
        data["summary"].update({"validated_count": 0, "source_restored": False})
        result = self.validate(data, strict=False)
        self.assertTrue(result.clean, result.errors)


if __name__ == "__main__":
    unittest.main()
