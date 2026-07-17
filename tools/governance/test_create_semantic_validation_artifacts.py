from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CREATOR = ROOT / "tools" / "governance" / "create_semantic_validation_artifacts.py"
INVENTORY = ROOT / "tools" / "governance" / "semantic_artifact_inventory.py"
TEMP_ROOT = ROOT / ".test-tmp" / "semantic-artifact-create"


@contextmanager
def temp_dir():
    path = TEMP_ROOT / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    yield path


def write_fake_volume(root: Path) -> Path:
    volume = root / "lra-volume-i"
    target = volume / "volume-i" / "book-order" / "bounds"
    target.mkdir(parents=True)
    (volume / "volume-i-book-order.tex").write_text(
        r"\input{volume-i/book-order/bounds/index}" + "\n",
        encoding="utf-8",
    )
    (target / "index.tex").write_text(
        r"\chapter{Bounds}" + "\n" + r"\input{volume-i/book-order/bounds/routed}" + "\n",
        encoding="utf-8",
    )
    (target / "routed.tex").write_text(
        r"\begin{definition}[Routed]\label{def:routed}Routed.\end{definition}" + "\n",
        encoding="utf-8",
    )
    (target / "unrouted.tex").write_text(
        r"\begin{definition}[Unrouted]\label{def:unrouted}Unrouted.\end{definition}" + "\n",
        encoding="utf-8",
    )
    return volume


def write_fake_volume_with_lean_record(root: Path) -> Path:
    volume = root / "lra-volume-ii"
    target = volume / "volume-ii" / "book-order" / "bounds"
    target.mkdir(parents=True)
    (volume / "volume-ii-book-order.tex").write_text(
        r"\input{volume-ii/book-order/bounds/index}" + "\n",
        encoding="utf-8",
    )
    (target / "index.tex").write_text(
        r"\chapter{Bounds}" + "\n" + r"\input{volume-ii/book-order/bounds/routed}" + "\n",
        encoding="utf-8",
    )
    (target / "routed.tex").write_text(
        "\n".join(
            [
                r"\begin{theorem}[Order]\label{thm:order}Ordered.\end{theorem}",
                r"\begin{formalizationrecord}{Lean 4 Verification Record}",
                r"\FormalizationSource{Internal source}",
                r"\Formalizes{thm:order}",
                r"\textbf{Lean module:} \texttt{LRA.VolumeII.Order}.\par",
                r"\LeanDeclaration{order\_theorem}",
                r"\textbf{Status:} checked against \texttt{lra-lean}.\par",
                r"\begin{leancode}",
                r"theorem order_theorem : True := by trivial",
                r"\end{leancode}",
                r"\end{formalizationrecord}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return volume


class CreateSemanticValidationArtifactsTests(unittest.TestCase):
    def test_creates_prompt_request_for_missing_routed_package(self):
        with temp_dir() as root:
            volume = write_fake_volume(root)
            output = root / "creation.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATOR),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(payload["created_count"], 1)
        self.assertEqual(payload["created"][0]["label"], "def:routed")
        package = volume / "volume-i" / "book-order" / "bounds" / "def-routed"
        self.assertTrue((package / "generation-request.json").exists())
        self.assertTrue((package / "prompt.md").exists())
        self.assertTrue((package / "source.tex").exists())
        self.assertFalse((volume / "volume-i" / "book-order" / "bounds" / "def-unrouted").exists())
        request = json.loads((package / "generation-request.json").read_text(encoding="utf-8"))
        self.assertEqual(request["llm_packet"]["source"]["current_tex"].count("def:routed"), 1)

    def test_inventory_creation_requires_source_text(self):
        with temp_dir() as root:
            write_fake_volume(root)
            inventory = root / "inventory.json"
            result_inventory = subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--format",
                    "json",
                    "--output",
                    str(inventory),
                ],
                capture_output=True,
                text=True,
            )
            result_create = subprocess.run(
                [
                    sys.executable,
                    str(CREATOR),
                    "--inventory",
                    str(inventory),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result_inventory.returncode, 0, result_inventory.stdout + result_inventory.stderr)
        self.assertEqual(result_create.returncode, 2)
        self.assertIn("--include-source-text", result_create.stderr)

    def test_inventory_creation_with_source_text_succeeds(self):
        with temp_dir() as root:
            write_fake_volume(root)
            inventory = root / "inventory.json"
            result_inventory = subprocess.run(
                [
                    sys.executable,
                    str(INVENTORY),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "i",
                    "--chapter",
                    "bounds",
                    "--include-source-text",
                    "--format",
                    "json",
                    "--output",
                    str(inventory),
                ],
                capture_output=True,
                text=True,
            )
            result_create = subprocess.run(
                [
                    sys.executable,
                    str(CREATOR),
                    "--inventory",
                    str(inventory),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result_inventory.returncode, 0, result_inventory.stdout + result_inventory.stderr)
        self.assertEqual(result_create.returncode, 0, result_create.stdout + result_create.stderr)
        self.assertIn('"created_count": 1', result_create.stdout)

    def test_generation_request_captures_lean_formalization_metadata(self):
        with temp_dir() as root:
            volume = write_fake_volume_with_lean_record(root)
            output = root / "creation.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATOR),
                    "--repos-root",
                    str(root),
                    "--volume",
                    "ii",
                    "--chapter",
                    "bounds",
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            request_path = volume / "volume-ii" / "book-order" / "bounds" / "thm-order" / "generation-request.json"
            request = json.loads(request_path.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        formalizations = request["llm_packet"]["source"]["formalizations"]
        self.assertEqual(len(formalizations), 1)
        self.assertEqual(formalizations[0]["artifact_label"], "thm:order")
        self.assertEqual(formalizations[0]["repository"], "lra-lean")
        self.assertEqual(formalizations[0]["module"], "LRA.VolumeII.Order")
        self.assertEqual(formalizations[0]["declaration"], "order_theorem")
        self.assertEqual(formalizations[0]["status"], "checked")
        self.assertEqual(formalizations[0]["environment"]["mathlib_policy"], "prohibited")
        self.assertIn("theorem order_theorem", formalizations[0]["code"])


if __name__ == "__main__":
    unittest.main()
