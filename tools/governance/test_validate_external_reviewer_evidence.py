from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE_PATH = Path(__file__).with_name("validate_external_reviewer_evidence.py")
SPEC = importlib.util.spec_from_file_location("validate_external_reviewer_evidence", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def evidence(role: str, response_id: str, *, provider: str = "openai_responses_api", requested_model: str = "gpt-5.6") -> dict:
    return {
        "provider": provider,
        "role": role,
        "requested_model": requested_model,
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


def checks() -> dict:
    names = (
        "binder_scope", "language_level", "assumptions_and_conclusion", "statement_shape",
        "quantifier_order", "witness_dependencies", "negation", "normalization_assumptions",
        "contrapositive", "applicability_failure", "order_strength", "predicate_signatures",
        "failure_modes", "yaml_tex_equivalence",
    )
    return {name: {"result": "pass", "notes": None} for name in names}


class ExternalReviewerEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def package(self, reviewer: dict | None = None) -> Path:
        review = reviewer or evidence("semantic_reviewer", "resp_sem")
        path = self.root / "package.yaml"
        path.write_text(yaml.safe_dump({"review": {"reviewer": review}}, sort_keys=False), encoding="utf-8")
        (self.root / "external-review-receipt.yaml").write_text(
            yaml.safe_dump({
                "schema_version": "lra.external-review-receipt/1.0",
                "reviewer": review,
                "result": "reviewed",
                "blocking_issues": [],
            }, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def audit(self, semantic: dict | None = None, logic: dict | None = None, *, missing_code: bool = False) -> Path:
        findings = []
        if missing_code:
            findings.append({"code": "REVIEW_PACKAGE_NOT_PRODUCED", "severity": "blocking", "message": "missing", "field": "review_package"})
        path = self.root / "audit-validation.yaml"
        path.write_text(yaml.safe_dump({
            "review_package": {"reviewer": semantic or evidence("semantic_reviewer", "resp_sem"), "findings": findings},
            "logic_validation": {"reviewer": logic or evidence("logic_validator", "resp_logic"), "checks": checks()},
        }, sort_keys=False), encoding="utf-8")
        return path

    def test_accepts_distinct_external_gpt56_evidence(self):
        result = MODULE.Result()
        MODULE.validate_package(self.package(), False, None, result)
        MODULE.validate_audit(self.audit(), False, None, result)
        self.assertTrue(result.clean, result.errors)

    def test_rejects_codex_provider(self):
        result = MODULE.Result()
        MODULE.validate_package(self.package(evidence("semantic_reviewer", "resp_sem", provider="codex")), False, None, result)
        self.assertFalse(result.clean)
        self.assertTrue(any("forbidden" in item for item in result.errors))

    def test_rejects_wrong_requested_model(self):
        result = MODULE.Result()
        MODULE.validate_package(self.package(evidence("semantic_reviewer", "resp_sem", requested_model="gpt-5-codex")), False, None, result)
        self.assertFalse(result.clean)
        self.assertTrue(any("requested_model" in item for item in result.errors))

    def test_rejects_same_semantic_and_logic_response(self):
        result = MODULE.Result()
        MODULE.validate_audit(self.audit(logic=evidence("logic_validator", "resp_sem")), False, None, result)
        self.assertFalse(result.clean)
        self.assertTrue(any("distinct response ids" in item for item in result.errors))

    def test_rejects_review_package_not_produced_terminal_marker(self):
        result = MODULE.Result()
        MODULE.validate_audit(self.audit(missing_code=True), False, None, result)
        self.assertFalse(result.clean)
        self.assertTrue(any("incomplete work" in item for item in result.errors))


if __name__ == "__main__":
    unittest.main()
