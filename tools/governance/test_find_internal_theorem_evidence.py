from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "governance" / "find_internal_theorem_evidence.py"


class FindInternalTheoremEvidenceTests(unittest.TestCase):
    def test_finds_knowledge_explorer_and_source_profile_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            explorer = root / "chapter" / ".explorer"
            explorer.mkdir(parents=True)
            (explorer / "knowledge.json").write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "id": "thm:darboux",
                                "name": "Darboux's Theorem",
                                "statement_tex": "Derivatives have the intermediate value property.",
                                "source": "notes-darboux.tex",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            profiles = root / "lra-source-profiles"
            (profiles / "inventory").mkdir(parents=True)
            (profiles / "inventory" / "source-registry.yaml").write_text(
                yaml.safe_dump(
                    {
                        "sources": [
                            {
                                "source_id": "SRC-1",
                                "canonical_title": "Real Analysis Notes",
                                "author": "Analyst",
                                "canonical_file": "Real Analysis Notes.pdf",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            active = profiles / "active-profile"
            active.mkdir()
            (active / "source01.md").write_text(
                "---\nsource_id: SRC-1\ncanonical_title: Real Analysis Notes\nauthor: Analyst\n---\nDarboux theorem says derivatives have the intermediate value property.\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--query",
                    "Darboux theorem",
                    "--knowledge-root",
                    str(root / "chapter"),
                    "--source-profiles-root",
                    str(profiles),
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            source_types = {hit["source_type"] for hit in payload["hits"]}
            self.assertIn("knowledge_explorer", source_types)
            self.assertIn("source_markdown", source_types)

    def test_scans_markdown_referenced_by_source_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles = root / "lra-source-profiles"
            (profiles / "inventory").mkdir(parents=True)
            (profiles / "inventory" / "source-registry.yaml").write_text("sources: []\n", encoding="utf-8")
            chapter = profiles / "volumes" / "volume-iii" / "book-analysis-ii" / "differentiation"
            markdown_dir = chapter / "markdown"
            markdown_dir.mkdir(parents=True)
            markdown = markdown_dir / "SRC-1.md"
            markdown.write_text(
                "---\nsource_id: SRC-1\ncanonical_title: Differentiation Source\n---\nDarboux theorem appears here.\n",
                encoding="utf-8",
            )
            (chapter / "source-index.yaml").write_text(
                yaml.safe_dump(
                    {
                        "sources": [
                            {
                                "source_id": "SRC-1",
                                "canonical_title": "Differentiation Source",
                                "markdown_extract_path": str(markdown),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--query",
                    "Darboux theorem",
                    "--source-profiles-root",
                    str(profiles),
                    "--volume",
                    "volume-iii",
                    "--chapter",
                    "differentiation",
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertIn(str(markdown.resolve()), payload["inputs"]["source_index_markdown_files"])
            self.assertEqual("source_index_markdown", payload["hits"][0]["source_type"])


if __name__ == "__main__":
    unittest.main()
