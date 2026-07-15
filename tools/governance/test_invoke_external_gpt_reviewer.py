from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("invoke_external_gpt_reviewer.py")
SPEC = importlib.util.spec_from_file_location("invoke_external_gpt_reviewer", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ROOT = Path(__file__).resolve().parents[2]


def semantic_result(label: str = "def:test") -> dict:
    return {
        "result": "reviewed",
        "blocking_issues": [],
        "artifact_yaml": f"identity:\n  label: {label}\n",
        "corrected_tex": "\\begin{definition}Test\\end{definition}",
        "source_patch": "diff --git a/test.tex b/test.tex",
        "validation_yaml": "artifact_label: def:test\nresult: pass",
        "source_map_yaml": "artifact_label: def:test\nentries: []",
        "registry_needs_yaml": "artifact_label: def:test\nmissing_predicates: []",
        "formalization_links_yaml": "artifact_label: def:test\nformalizations: []",
        "proof_vault_links_yaml": "artifact_label: def:test\nrecords: []",
    }


def response(response_id: str, result: dict, status: str = "completed") -> dict:
    return {
        "id": response_id,
        "model": "gpt-5.6-sol",
        "status": status,
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(result),
                    }
                ],
            }
        ],
    }


class ExternalReviewerTransportTests(unittest.TestCase):
    def test_authority_bundle_contains_canonical_schema_and_registries(self):
        bundle = MODULE.build_authority_bundle(ROOT)
        by_path = {item["path"]: item for item in bundle.files}
        required = {
            "constitution/schema/semantic-artifact.schema.json",
            "constitution/schema/artifact-matrix.yaml",
            "constitution/schema/block-registry.yaml",
            "predicates.yaml",
            "structures.yaml",
            "notation.yaml",
            "relations.yaml",
            "docs/architecture/semantic-artifact-record.md",
        }
        self.assertTrue(required.issubset(by_path))
        for path in required:
            self.assertEqual(
                by_path[path]["content"],
                (ROOT / path).read_text(encoding="utf-8"),
            )
            self.assertTrue(by_path[path]["sha256"].startswith("sha256:"))

    def test_request_payload_embeds_schema_registry_and_renderer_contract(self):
        bundle = MODULE.build_authority_bundle(ROOT)
        payload, input_text = MODULE.request_payload(
            "review prompt",
            {"source": {"label": "def:test"}},
            "semantic_reviewer",
            bundle,
        )
        self.assertEqual(payload["model"], "gpt-5.6")
        self.assertEqual(payload["reasoning"]["effort"], "high")
        self.assertIn("constitution/schema/semantic-artifact.schema.json", input_text)
        self.assertIn("predicates.yaml", input_text)
        self.assertIn("structures.yaml", input_text)
        self.assertIn("docs/architecture/semantic-artifact-record.md", input_text)
        self.assertIn("predicates:", input_text)

    def test_background_response_polls_until_completed(self):
        calls: list[tuple[str, str, dict | None]] = []
        queued = {"id": "resp_poll", "model": "gpt-5.6-sol", "status": "queued"}
        running = {"id": "resp_poll", "model": "gpt-5.6-sol", "status": "in_progress"}
        completed = response("resp_poll", semantic_result())
        sequence = iter([(queued, "req_1"), (running, None), (completed, None)])

        def fake_request(method, url, api_key, payload=None, timeout=60.0):
            calls.append((method, url, payload))
            return next(sequence)

        with patch.object(MODULE, "request_json", side_effect=fake_request):
            final, request_id = MODULE.submit_background_response(
                {"model": "gpt-5.6"},
                "secret",
                poll_interval=0,
                poll_timeout=10,
                sleep=lambda _: None,
                monotonic=lambda: 0,
            )
        self.assertEqual(request_id, "req_1")
        self.assertEqual(final["status"], "completed")
        self.assertEqual([method for method, _, _ in calls], ["POST", "GET", "GET"])
        self.assertTrue(calls[1][1].endswith("/resp_poll"))
        self.assertIsNotNone(calls[0][2])
        self.assertTrue(calls[0][2]["background"])

    def test_failed_validation_is_sent_to_distinct_external_repair_call(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            output = temp_root / "def-test"
            diagnostics = temp_root / "diagnostics"
            prompt = temp_root / "prompt.md"
            prompt.write_text("Review exactly one artifact.", encoding="utf-8")
            packet = {
                "source": {
                    "repository": "wsollers/lra-volume-iii",
                    "commit": "a" * 40,
                    "file": "volume-iii/test.tex",
                    "label": "def:test",
                    "source_hash": "sha256:" + "b" * 64,
                },
                "governance": {"commit": "c" * 40},
            }
            args = argparse.Namespace(
                output=output,
                diagnostics_dir=diagnostics,
                governance_root=ROOT,
                repos_root=None,
                prompt=prompt,
                max_repair_attempts=1,
                poll_interval=0,
                poll_timeout=10,
            )
            payloads: list[dict] = []
            responses = iter(
                [
                    (response("resp_initial", semantic_result()), "req_initial"),
                    (response("resp_repair", semantic_result()), "req_repair"),
                ]
            )

            def fake_submit(payload, api_key, **kwargs):
                payloads.append(payload)
                return next(responses)

            validation_runs = [
                MODULE.ValidationRun(
                    1,
                    "schema: artifact.yaml used a noncanonical shape",
                    "",
                    ("validate-semantic",),
                ),
                MODULE.ValidationRun(0, "PASS", "", ("validate-semantic",)),
            ]
            tiny_authority = MODULE.AuthorityBundle(
                (
                    {
                        "path": "constitution/schema/semantic-artifact.schema.json",
                        "sha256": "sha256:" + "d" * 64,
                        "content": "{\"title\":\"canonical semantic schema\"}",
                    },
                    {
                        "path": "predicates.yaml",
                        "sha256": "sha256:" + "e" * 64,
                        "content": "predicates: []",
                    },
                ),
                "sha256:" + "f" * 64,
            )

            with (
                patch.object(MODULE, "submit_background_response", side_effect=fake_submit),
                patch.object(MODULE, "run_semantic_validation", side_effect=validation_runs),
                patch.object(MODULE, "build_authority_bundle", return_value=tiny_authority),
            ):
                result_code = MODULE.run_semantic(args, packet, "secret")

            self.assertEqual(result_code, 0)
            self.assertEqual(len(payloads), 2)
            first_input = payloads[0]["input"]
            second_input = payloads[1]["input"]
            self.assertIn("canonical semantic schema", first_input)
            self.assertNotIn("noncanonical shape", first_input)
            self.assertIn("noncanonical shape", second_input)
            self.assertIn("resp_initial", second_input)
            self.assertTrue((output / "package.yaml").exists())
            self.assertTrue((output / "external-review-receipt.yaml").exists())
            self.assertTrue((diagnostics / "attempt-01" / "validator.json").exists())
            receipt = (output / "external-review-receipt.yaml").read_text(encoding="utf-8")
            self.assertIn("resp_repair", receipt)
            self.assertNotIn("resp_initial", receipt)

    def test_missing_authority_file_fails_before_model_call(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                MODULE.build_authority_bundle(Path(temp))


if __name__ == "__main__":
    unittest.main()
